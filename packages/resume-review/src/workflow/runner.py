"""ReviewWorkflow class for CLI integration."""

import asyncio
import logging
from pathlib import Path
from typing import Callable, Optional

from ..config.model_config import calculate_cost
from ..models import SessionStatus
from ..models.session import ReviewSession
from ..services.qmd_parser import QMDParser
from ..services.quarto_validator import QuartoValidator
from .graph import build_review_workflow
from .persistence import create_session_directory, save_feedback, save_iteration, save_revisions
from .state import ReviewState, add_feedback, add_portfolio, add_revisions

logger = logging.getLogger("resume_review")


class ReviewWorkflow:
    """High-level wrapper for LangGraph workflow integration with CLI."""

    def __init__(self, api_key: str, save_iterations: bool = False,
                 output_dir: Optional[Path] = None,
                 on_iteration_complete: Optional[Callable[[int, float, Path], None]] = None,
                 gemini_api_key: Optional[str] = None,
                 openai_api_key: Optional[str] = None,
                 anthropic_api_key: Optional[str] = None,
                 override_model: Optional[str] = None):
        """Initialize workflow wrapper.

        Args:
            api_key: Legacy Anthropic API key (for backward compatibility)
            save_iterations: Whether to save iteration artifacts
            output_dir: Directory for saving artifacts
            on_iteration_complete: Callback after each iteration
            gemini_api_key: Google Gemini API key (optional)
            openai_api_key: OpenAI API key (optional)
            anthropic_api_key: Anthropic API key (optional, overrides api_key)
            override_model: Force all agents to use this model (optional, for testing)
        """
        self.api_key = api_key  # Legacy
        self.gemini_api_key = gemini_api_key
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key or api_key
        self.override_model = override_model
        self.save_iterations = save_iterations
        self.output_dir = output_dir
        self.on_iteration_complete = on_iteration_complete
        self.session_dir: Optional[Path] = None
        self.session_timestamp: Optional[str] = None
        self.compiled_workflow = build_review_workflow()
        self.qmd_parser = QMDParser()

    def run_review(self, session: ReviewSession) -> ReviewSession:
        """Run the complete review workflow using LangGraph StateGraph."""
        logger.info(f"Starting LangGraph review session {session.session_id}")
        logger.info(f"Target role: {session.target_role}, threshold: {session.score_threshold}")
        logger.info(f"Max iterations: {session.max_iterations}, dry_run: {session.dry_run}")

        if self.save_iterations and not session.dry_run:
            self.session_dir, self.session_timestamp = create_session_directory(
                self.output_dir, session.resume.file_path)
            save_iteration(session, self.session_dir, self.output_dir, 0, "original")

        initial_state = self._create_initial_state(session)
        try:
            final_state = asyncio.run(self._run_workflow_async(initial_state))
            session = self._update_session_from_state(session, final_state)
            session.status = SessionStatus.COMPLETED
            logger.info(f"Review completed. Final score: {session.final_score}/{session.score_threshold}")

            # Log cost summary if token usage is tracked
            self._log_cost_summary(final_state)

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            session.status = SessionStatus.FAILED
        return session

    def _create_initial_state(self, session: ReviewSession) -> ReviewState:
        """Create initial state dictionary for workflow."""
        return {
            "resume": session.resume, "resume_content": session.resume.content,
            "target_role": session.target_role, "score_threshold": session.score_threshold,
            "max_iterations": session.max_iterations, "api_key": self.api_key,
            # New multi-provider API keys
            "anthropic_api_key": self.anthropic_api_key,
            "gemini_api_key": self.gemini_api_key,
            "openai_api_key": self.openai_api_key,
            "override_model": self.override_model,
            "dry_run": session.dry_run, "screenshot_url": session.screenshot_url,
            "save_iterations": self.save_iterations,
            "output_dir": str(self.output_dir) if self.output_dir else None,
            "session_id": session.session_id, "current_iteration": 0,
            "feedback_history": [], "current_feedback": [],
            "integrated_score": 0.0, "threshold_met": False,
            "skill_gaps": [], "portfolio_suggestions": [],
            "revised_content": "", "applied_revisions": [],
            "token_usage": {},  # New: token usage tracking
            "final_score": 0.0, "should_continue": True, "error": None,
            "validation_retry_count": 0,
            "max_validation_retries": session.max_validation_retries,
            "strict_validation": session.strict_validation,
            "current_retry_attempts": [],
        }

    async def _run_workflow_async(self, initial_state: ReviewState) -> ReviewState:
        """Execute the workflow asynchronously."""
        accumulated_state = dict(initial_state)
        async for state in self.compiled_workflow.astream(initial_state):
            for node_name, node_state in state.items():
                self._update_accumulated_state(accumulated_state, node_state)
                await self._handle_node_persistence(node_name, node_state, accumulated_state)
        return accumulated_state

    def _update_accumulated_state(self, accumulated_state: dict, node_state: dict) -> None:
        """Update accumulated state with node outputs, applying reducers."""
        for key, value in node_state.items():
            if key == "feedback_history" and key in accumulated_state:
                accumulated_state[key] = add_feedback(accumulated_state[key], value)
            elif key == "applied_revisions" and key in accumulated_state:
                accumulated_state[key] = add_revisions(accumulated_state[key], value)
            elif key == "portfolio_suggestions" and key in accumulated_state:
                accumulated_state[key] = add_portfolio(accumulated_state[key], value)
            else:
                accumulated_state[key] = value

    async def _handle_node_persistence(self, node_name: str, node_state: dict,
                                  accumulated_state: dict) -> None:
        """Handle saving artifacts after specific nodes."""
        if not self.save_iterations or not self.session_dir:
            # Still need to run validation retry even if not saving iterations
            if node_name == "revisor":
                await self._validate_and_retry(accumulated_state)  # T021
            return
        if node_name == "aggregator":
            iteration = accumulated_state.get("current_iteration", 0) + 1
            score = node_state.get("integrated_score", 0.0)
            feedback = accumulated_state.get("current_feedback", [])
            if feedback:
                save_feedback(self.session_dir, feedback, iteration, score)
                logger.info(f"Saved feedback for iteration {iteration}")
        elif node_name == "revisor":
            iteration = node_state.get("current_iteration", 0)
            save_revisions(self.session_dir, node_state.get("applied_revisions", []), iteration)
            if "resume" in node_state:
                iter_dir = self.session_dir / f"iter{iteration}"
                iter_dir.mkdir(exist_ok=True)
                resume_path = iter_dir / "resume.qmd"
                QMDParser.save_resume(node_state["resume"], resume_path, create_backup=False)
                logger.info(f"Saved resume for iteration {iteration}")

                # Validate Quarto syntax (original validation - will be replaced by retry loop)
                self._validate_quarto_syntax(resume_path, iteration)

            # Run validation retry loop after revisor (T021)
            await self._validate_and_retry(accumulated_state)
        elif node_name == "portfolio" and "resume" in accumulated_state:
            iteration = accumulated_state.get("current_iteration", 0) + 1
            iter_dir = self.session_dir / f"iter{iteration}"
            iter_dir.mkdir(exist_ok=True)
            QMDParser.save_resume(accumulated_state["resume"], iter_dir / "resume.qmd", create_backup=False)
            logger.info(f"Saved final resume for iteration {iteration}")

    def _validate_quarto_syntax(self, resume_path: Path, iteration: int) -> None:
        """Validate Quarto syntax after saving resume."""
        validator = QuartoValidator()
        is_valid, error_msg = validator.validate(resume_path.read_text(encoding="utf-8"))

        if not is_valid:
            logger.error(f"Quarto validation failed for iteration {iteration}: {error_msg}")
            if self.session_dir:
                validation_log = self.session_dir / f"iter{iteration}" / "validation_error.txt"
                validation_log.write_text(f"Quarto Validation Failed:\n\n{error_msg}", encoding="utf-8")
        else:
            logger.info(f"Quarto validation passed for iteration {iteration}")

    async def _validate_and_retry(self, state: dict) -> None:
        """
        Execute validation retry loop after revisor node (T017, T018, T032-T036).

        Args:
            state: Current accumulated workflow state
        """
        from ..models.validation import ValidationResult, RetryAttempt
        from ..services.quarto_validator import QuartoValidator
        from ..services.retry_logger import RetryLogger

        max_retries = state.get("max_validation_retries", 3)
        strict_validation = state.get("strict_validation", False)
        current_iteration = state.get("current_iteration", 0)

        # Reset retry count for this iteration (T023)
        state["validation_retry_count"] = 0
        state["current_retry_attempts"] = []

        validator = QuartoValidator()
        retry_count = 0

        # Initialize RetryLogger (T032)
        retry_logger = None
        if self.session_dir:
            try:
                retry_logger = RetryLogger(self.session_dir, current_iteration)
            except Exception as e:
                logger.warning(f"Failed to initialize RetryLogger: {e}")

        while retry_count <= max_retries:
            # Get current QMD content
            qmd_content = state.get("revised_content", "")
            if not qmd_content:
                logger.warning("No revised content to validate, skipping retry loop")
                return

            # Validate current content
            is_valid, error_msg = validator.validate(qmd_content)

            # Create ValidationResult for logging
            validation_result = ValidationResult(
                is_valid=is_valid,
                error_message=error_msg,
                timestamp=__import__('datetime').datetime.now(),
                attempt_number=retry_count
            )

            # Log initial validation (T033)
            if retry_count == 0 and retry_logger:
                try:
                    retry_logger.log_initial_validation(validation_result)
                except Exception as e:
                    logger.warning(f"Failed to log initial validation: {e}")

            if is_valid:
                logger.info(f"Quarto validation passed (attempt {retry_count})")
                # Finalize log on success (T035)
                if retry_logger:
                    try:
                        final_file = self.session_dir / f"iter{current_iteration}" / "resume.qmd"
                        retry_logger.finalize_log(
                            success=True,
                            total_retries=retry_count,
                            final_file=final_file
                        )
                    except Exception as e:
                        logger.warning(f"Failed to finalize retry log: {e}")
                return

            # Validation failed
            logger.warning(f"Quarto validation failed (attempt {retry_count}/{max_retries}): {error_msg}")

            # Check if we've exhausted retries
            if retry_count >= max_retries:
                logger.error(f"Quarto validation failed after {max_retries} retries")
                # Finalize log on failure (T035)
                if retry_logger:
                    try:
                        final_file = self.session_dir / f"iter{current_iteration}" / "resume.qmd"
                        retry_logger.finalize_log(
                            success=False,
                            total_retries=retry_count,
                            final_file=final_file
                        )
                    except Exception as e:
                        logger.warning(f"Failed to finalize retry log: {e}")

                if strict_validation:
                    raise ValueError(f"Validation failed after {max_retries} retries: {error_msg}")
                else:
                    logger.warning("Continuing workflow despite validation failure (strict_validation=False)")
                return

            # Generate validation feedback
            validation_feedback = validator.create_validation_feedback(error_msg)
            logger.info(f"Generated validation feedback with {len(validation_feedback.issues)} issues")

            # Re-invoke revisor to fix validation issues (T019)
            revised_content = await self._invoke_revisor_for_retry(state, validation_feedback)
            state["revised_content"] = revised_content

            # Save retry artifact (T020)
            retry_path = None
            if self.session_dir:
                retry_path = self._save_retry_artifact(revised_content, current_iteration, retry_count + 1)
                logger.info(f"Saved retry artifact: {retry_path}")

            # Re-validate to get updated validation result
            is_valid_after_fix, error_msg_after_fix = validator.validate(revised_content)

            # Record retry attempt
            retry_attempt = RetryAttempt(
                attempt_number=retry_count + 1,
                error_detected=error_msg[:500],  # Limit error message length
                correction_applied=f"Applied {len(validation_feedback.issues)} validation fixes",
                validation_result=ValidationResult(
                    is_valid=is_valid_after_fix,
                    error_message=error_msg_after_fix,
                    timestamp=__import__('datetime').datetime.now(),
                    attempt_number=retry_count + 1
                ),
                qmd_snapshot_path=retry_path if self.session_dir else None
            )
            state["current_retry_attempts"].append(retry_attempt.model_dump())
            state["validation_retry_count"] = retry_count + 1

            # Log retry attempt (T034)
            if retry_logger:
                try:
                    retry_logger.log_retry_attempt(retry_attempt)
                except Exception as e:
                    logger.warning(f"Failed to log retry attempt: {e}")

            retry_count += 1

    async def _invoke_revisor_for_retry(self, state: dict, validation_feedback) -> str:
        """
        Re-invoke revisor node with validation feedback (T019).

        Args:
            state: Current workflow state
            validation_feedback: Feedback generated from validation errors

        Returns:
            Revised QMD content from revisor
        """
        # Import revisor node dynamically to avoid circular imports
        from .graph import build_review_workflow
        from ..agents.revisor import revisor_node

        # Create temporary state with validation feedback
        temp_state = dict(state)
        temp_state["current_feedback"] = [validation_feedback]

        # Call revisor node directly
        result = await revisor_node(temp_state)

        # Extract revised content
        revised_content = result.get("revised_content", state.get("revised_content", ""))
        return revised_content

    def _save_retry_artifact(self, qmd_content: str, iteration: int, retry_count: int) -> Path:
        """
        Save intermediate QMD file from retry attempt (T020).

        Args:
            qmd_content: QMD content to save
            iteration: Current iteration number
            retry_count: Current retry attempt number

        Returns:
            Path to saved retry file
        """
        if not self.session_dir:
            raise ValueError("Cannot save retry artifact without session directory")

        retry_path = self.session_dir / f"iter{iteration}_retry{retry_count}.qmd"
        retry_path.parent.mkdir(parents=True, exist_ok=True)
        retry_path.write_text(qmd_content, encoding="utf-8")
        return retry_path

    def _update_session_from_state(self, session: ReviewSession, state: ReviewState) -> ReviewSession:
        """Update ReviewSession from final LangGraph state."""
        logger.debug(f"Updating session from state. Keys: {list(state.keys())}")
        # NEVER update resume object - user will manually copy from session directory
        # This prevents accidental overwrites of the original file
        for feedback_iteration in state.get("feedback_history", []):
            session.add_feedback(feedback_iteration)
        for revision in state.get("applied_revisions", []):
            session.add_revision(revision)
        for portfolio in state.get("portfolio_suggestions", []):
            session.add_portfolio_suggestion(portfolio)
        final_score = state.get("final_score") or state.get("integrated_score") or 0.0
        session.final_score = final_score
        session.current_iteration = state.get("current_iteration", 0)
        logger.debug(f"Session updated: final_score={session.final_score}, iteration={session.current_iteration}")
        return session

    def _log_cost_summary(self, state: ReviewState) -> None:
        """Log token usage and cost summary.

        Args:
            state: Final workflow state with token_usage data
        """
        token_usage = state.get("token_usage", {})
        if not token_usage:
            return

        logger.info("=== Cost Summary ===")
        total_cost = 0.0

        for agent_name, usage in token_usage.items():
            model = usage.get("model", "unknown")
            provider = usage.get("provider", "unknown")
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)

            # Calculate cost if we have token counts
            if input_tokens > 0 and output_tokens > 0:
                try:
                    cost = calculate_cost(model, input_tokens, output_tokens)
                    total_cost += cost
                    logger.info(
                        f"{agent_name}: {model} ({provider}) - "
                        f"in:{input_tokens} out:{output_tokens} cost:${cost:.4f}"
                    )
                except KeyError:
                    logger.warning(f"{agent_name}: Model '{model}' not found in pricing data")
            else:
                logger.info(f"{agent_name}: {model} ({provider})")

        if total_cost > 0:
            logger.info(f"Total estimated cost: ${total_cost:.4f}")
            logger.info("=" * 40)
