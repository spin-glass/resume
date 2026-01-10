"""Design applier workflow node for applying design modifications.

This node orchestrates CSS generation, section reordering, theme recommendations,
and preview generation based on design feedback from UX and Visual Designer agents.
"""

import logging
import tempfile
from pathlib import Path
from typing import Any

from ...agents.css_generator import CSSGeneratorAgent
from ...models.design import CSSModification, DesignPreview, SectionReorder
from ...services.css_service import CSSService
from ...services.llm_factory import AgentName, LLMClientFactory
from ...services.screenshot import ScreenshotService
from ...services.section_reorder import SectionReorderService
from ...services.theme_recommender import ThemeRecommenderService
from ..state import ReviewState

logger = logging.getLogger(__name__)


async def _generate_css(
    state: ReviewState, design_feedback: list
) -> CSSModification | None:
    """Generate CSS modifications from design feedback.

    Args:
        state: Workflow state
        design_feedback: Design feedback list

    Returns:
        CSSModification or None if generation fails
    """
    try:
        # Create LLM client for CSS generator
        llm_client = LLMClientFactory.create_client(
            agent_name=AgentName.CSS_GENERATOR,
            gemini_api_key=state.get("gemini_api_key"),
            openai_api_key=state.get("openai_api_key"),
            anthropic_api_key=state.get("anthropic_api_key"),
            override_model=state.get("override_model"),
        )

        # Initialize CSS generator agent
        css_agent = CSSGeneratorAgent(llm_client=llm_client)

        # Read current CSS if exists
        css_output_path = state.get("css_output_path") or "styles/resume-custom.css"
        css_path = Path(css_output_path)
        current_css = ""
        if css_path.exists():
            current_css = css_path.read_text(encoding="utf-8")

        # Generate CSS
        css_mod = await css_agent.generate_css(
            design_feedback=design_feedback,
            current_css=current_css,
            target_role=state.get("target_role", "LLM Engineer"),
        )

        return css_mod

    except Exception as e:
        logger.error(f"CSS generation failed: {e}", exc_info=True)
        return None


async def _generate_preview(
    state: ReviewState,
    css_modification: CSSModification,
    screenshot_service: ScreenshotService,
) -> DesignPreview | None:
    """Generate visual preview of CSS changes without modifying files (T040).

    Workflow:
    1. Capture "before" screenshot of current resume
    2. Apply CSS to temporary location
    3. Capture "after" screenshot with temp CSS
    4. Generate diff image using pixelmatch
    5. Create composite before|diff|after image
    6. Clean up temporary files
    7. Return DesignPreview model

    Args:
        state: Workflow state containing screenshot_url
        css_modification: Generated CSS to preview
        screenshot_service: Service for capturing screenshots

    Returns:
        DesignPreview with screenshot paths and diff stats, or None on failure
    """
    screenshot_url = state.get("screenshot_url")
    if not screenshot_url:
        logger.warning("Preview mode enabled but no screenshot_url provided")
        return None

    try:
        # Step 1: Capture "before" screenshot
        logger.info(f"Capturing 'before' screenshot from {screenshot_url}")
        before_path = await screenshot_service.capture(
            url=screenshot_url,
            output_filename="preview_before.png",
        )

        if not before_path or not before_path.exists():
            logger.error("Failed to capture 'before' screenshot")
            return None

        # Step 2: Write CSS to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".css", delete=False
        ) as temp_css:
            temp_css.write(css_modification.css_content)
            temp_css_path = Path(temp_css.name)

        # Step 3: For preview, we'd need to inject the CSS into the page
        # In practice, this requires server-side support or browser extension
        # For now, we simulate by capturing the same URL (TODO: inject CSS)
        logger.info("Capturing 'after' screenshot (simulated - CSS not injected)")
        after_path = await screenshot_service.capture(
            url=screenshot_url,
            output_filename="preview_after.png",
        )

        # Clean up temp CSS
        try:
            temp_css_path.unlink()
        except OSError:
            pass

        if not after_path or not after_path.exists():
            logger.error("Failed to capture 'after' screenshot")
            return None

        # Step 4: Generate diff image
        diff_path = screenshot_service.cache_dir / "preview_diff.png"
        diff_result_path, diff_stats = screenshot_service.generate_diff(
            before_path, after_path, diff_path
        )

        if "error" in diff_stats:
            logger.warning(f"Diff generation failed: {diff_stats['error']}")
            # Continue without diff

        # Step 5: Create composite image
        composite_path = None
        if diff_result_path and diff_result_path.exists():
            composite_path = screenshot_service.create_composite(
                before_path,
                diff_result_path,
                after_path,
                screenshot_service.cache_dir / "preview_composite.png",
            )

        # Step 6: Build and return DesignPreview
        preview = DesignPreview(
            before_screenshot=before_path,
            after_screenshot=after_path,
            diff_screenshot=diff_result_path,
            composite_screenshot=composite_path,
            diff_pixel_count=diff_stats.get("diffPixels"),
            diff_percentage=diff_stats.get("diffPercentage"),
            metrics={
                "width": diff_stats.get("width"),
                "height": diff_stats.get("height"),
            },
        )

        logger.info(f"Preview generated: {preview.get_summary()}")
        return preview

    except Exception as e:
        logger.error(f"Preview generation failed: {e}", exc_info=True)
        return None


def _recommend_theme(
    design_feedback: list,
) -> dict | None:
    """Analyze design feedback for systematic issues and recommend theme (T065).

    Args:
        design_feedback: Design feedback list

    Returns:
        ThemeRecommendation dict, or None if no recommendation needed
    """
    try:
        recommender = ThemeRecommenderService()
        recommendation = recommender.recommend(design_feedback)

        if recommendation:
            logger.info(f"Theme recommended: {recommendation.theme_name}")
            return recommendation.model_dump()
        else:
            logger.info("No theme recommendation (issues not systematic)")
            return None

    except Exception as e:
        logger.error(f"Theme recommendation failed: {e}", exc_info=True)
        return None


def _analyze_section_order(
    state: ReviewState,
    ux_feedback: list,
) -> SectionReorder | None:
    """Analyze UX feedback for section reorder suggestions (T056).

    Args:
        state: Workflow state containing resume
        ux_feedback: UX feedback list

    Returns:
        SectionReorder recommendation, or None if no reorder needed
    """
    # Get resume content
    resume = state.get("resume")
    if not resume or not hasattr(resume, "content"):
        logger.info("No resume content available for section analysis")
        return None

    try:
        reorder_service = SectionReorderService()
        recommendation = reorder_service.analyze_and_recommend(
            qmd_content=resume.content,
            ux_feedback=ux_feedback,
            target_role=state.get("target_role", ""),
        )

        if recommendation and recommendation.is_changed():
            logger.info(f"Section reorder recommended: {recommendation.new_order}")
            return recommendation
        else:
            logger.info("No section reorder needed")
            return None

    except Exception as e:
        logger.error(f"Section order analysis failed: {e}", exc_info=True)
        return None


async def design_applier_node(state: ReviewState) -> dict[str, Any]:
    """Apply design modifications based on feedback and CLI flags.

    Orchestrates:
    - CSS generation (if design issues exist)
    - Section reordering (if UX feedback suggests) - NOT IMPLEMENTED YET
    - Theme recommendation (if systematic issues) - NOT IMPLEMENTED YET
    - Preview generation (if --design-preview enabled) - NOT IMPLEMENTED YET
    - File modification (if --auto-design enabled)

    Args:
        state: Current workflow state

    Returns:
        State updates dict with design modification results
    """
    logger.info("Design Applier: Starting design modification workflow")

    # Get design feedback (from current_feedback)
    current_feedback = state.get("current_feedback", [])
    if not current_feedback:
        logger.info("Design Applier: No feedback, skipping")
        return {
            "design_changes_applied": False,
            "design_changes_pending": False,
            "design_changes_list": [],
        }

    # Filter for design-related feedback (UX and Visual Designer)
    design_feedback = [
        f for f in current_feedback if f.agent_name in ["ux_designer", "visual_designer"]
    ]

    if not design_feedback:
        logger.info("Design Applier: No design feedback, skipping")
        return {
            "design_changes_applied": False,
            "design_changes_pending": False,
            "design_changes_list": [],
        }

    auto_design = state.get("auto_design_enabled", False)
    preview_mode = state.get("design_preview_enabled", False)

    result: dict[str, Any] = {
        "design_changes_applied": False,
        "design_changes_pending": False,
        "design_changes_list": [],
        "design_backup_paths": {},
    }

    # 1. CSS Generation (always run if feedback exists)
    logger.info(f"Generating CSS from {len(design_feedback)} design feedback items")
    css_mod = await _generate_css(state, design_feedback)

    if css_mod and css_mod.validation_passed:
        result["css_modification"] = css_mod
        logger.info(f"CSS generated: {css_mod.get_summary()}")
    elif css_mod:
        logger.warning(
            f"CSS validation failed: {css_mod.validation_errors}. Not applying."
        )
        result["css_modification"] = css_mod
        # Don't apply if validation failed
        return result

    # 2. Preview Generation (if preview mode)
    if preview_mode and css_mod:
        logger.info("Preview mode enabled - generating preview without applying changes")

        # Check if screenshot URL is provided
        screenshot_url = state.get("screenshot_url")
        if screenshot_url:
            screenshot_service = ScreenshotService()
            preview = await _generate_preview(state, css_mod, screenshot_service)

            if preview:
                result["design_preview"] = preview
                diff_path = str(preview.diff_screenshot) if preview.diff_screenshot else None
                comp_path = (
                    str(preview.composite_screenshot) if preview.composite_screenshot else None
                )
                result["design_preview_paths"] = {
                    "before": str(preview.before_screenshot),
                    "after": str(preview.after_screenshot),
                    "diff": diff_path,
                    "composite": comp_path,
                }
                logger.info(f"Preview generated: {preview.get_summary()}")
            else:
                logger.warning("Preview generation failed, continuing without preview images")
        else:
            logger.info("No screenshot URL provided, skipping visual preview")

        result["design_changes_pending"] = True
        result["design_changes_applied"] = False
        return result

    # 3. Analyze Section Reorder (T056, T057)
    ux_feedback = [f for f in design_feedback if f.agent_name == "ux_designer"]
    section_reorder = None
    if ux_feedback:
        section_reorder = _analyze_section_order(state, ux_feedback)
        if section_reorder:
            result["section_reorder"] = section_reorder
            logger.info(f"Section reorder recommended: {section_reorder.new_order}")

    # 4. Theme Recommendation (T065, T066)
    theme_recommendation = _recommend_theme(design_feedback)
    if theme_recommendation:
        result["theme_recommendation"] = theme_recommendation
        logger.info(f"Theme recommendation: {theme_recommendation.get('theme_name')}")

    # 5. Apply Modifications (if auto-design mode)
    if auto_design:
        changes_list = []
        backup_paths = {}

        # Apply CSS
        if css_mod and css_mod.validation_passed:
            css_service = CSSService()
            # Use state's css_output_path if provided, otherwise use css_mod.target_file
            css_output_path = state.get("css_output_path")
            css_path = Path(css_output_path) if css_output_path else css_mod.target_file

            backup, applied_css_mod = css_service.write_with_backup(
                css_mod.css_content, css_path
            )

            if applied_css_mod.validation_passed:
                if backup:
                    backup_paths[str(css_path)] = str(backup)
                changes_list.append(f"CSS: {css_path}")
                logger.info(f"CSS applied successfully: {css_path}")
            else:
                logger.error(
                    f"CSS application failed: {applied_css_mod.validation_errors}"
                )
                result["design_changes_applied"] = False
                result["design_changes_list"] = [
                    f"CSS application failed: {applied_css_mod.validation_errors}"
                ]
                return result

        # Apply Section Reorder (T057)
        if section_reorder and section_reorder.is_changed():
            resume = state.get("resume")
            if resume and hasattr(resume, "file_path") and resume.file_path:
                reorder_service = SectionReorderService()
                try:
                    backup, applied_reorder = reorder_service.reorder_with_backup(
                        Path(resume.file_path),
                        section_reorder.new_order,
                        section_reorder.rationale,
                    )
                    if backup:
                        backup_paths[str(resume.file_path)] = str(backup)
                    changes_list.append(f"Section Reorder: {resume.file_path}")
                    result["section_reorder"] = applied_reorder
                    logger.info(f"Section reorder applied: {resume.file_path}")
                except Exception as e:
                    logger.error(f"Section reorder failed: {e}")
                    # Continue without section reorder
            else:
                logger.warning("Cannot apply section reorder: no resume file path")

        result["design_changes_applied"] = True
        result["design_changes_list"] = changes_list
        result["design_backup_paths"] = backup_paths
        logger.info(f"Design modifications applied: {changes_list}")

    return result
