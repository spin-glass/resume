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
        }

    async def _run_workflow_async(self, initial_state: ReviewState) -> ReviewState:
        """Execute the workflow asynchronously."""
        accumulated_state = dict(initial_state)
        async for state in self.compiled_workflow.astream(initial_state):
            for node_name, node_state in state.items():
                self._update_accumulated_state(accumulated_state, node_state)
                self._handle_node_persistence(node_name, node_state, accumulated_state)
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

    def _handle_node_persistence(self, node_name: str, node_state: dict,
                                  accumulated_state: dict) -> None:
        """Handle saving artifacts after specific nodes."""
        if not self.save_iterations or not self.session_dir:
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

                # Validate Quarto syntax
                self._validate_quarto_syntax(resume_path, iteration)
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
