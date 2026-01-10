"""Design applier workflow node for applying design modifications.

This node orchestrates CSS generation, section reordering, theme recommendations,
and preview generation based on design feedback from UX and Visual Designer agents.
"""

import logging
import re
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

    # Determine cache directory  
    cache_dir = None
    session_dir = state.get("session_dir")
    current_iteration = state.get("current_iteration", 0)
    
    design_loop_active = state.get("design_loop_active", False)
    design_iteration = state.get("design_iteration", 0)

    if session_dir:
        if design_loop_active:
            # Save to design_iter folder for design loop
            iter_name = f"design_iter{design_iteration + 1}"
        else:
            # Normal iteration (text refinement)
            # Save to iter folder (consistent with 1-based indexing for user outputs)
            iter_num = current_iteration + 1
            iter_name = f"iter{iter_num}"

        cache_dir = Path(session_dir) / iter_name
        cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving design preview to {cache_dir}")
    
    try:
        # Initialize screenshot service with custom cache dir
        # Note: We create a new instance here to use the correct directory
        # The passed screenshot_service might have default cache
        service = ScreenshotService(cache_dir=cache_dir)
        
        # Step 1: Capture "before" screenshot (full page for user review)
        logger.info(f"Capturing 'before' screenshot from {screenshot_url}")
        before_path = await service.capture(
            url=screenshot_url,
            output_filename="preview_before.png",
            full_page=True,  # Full page for design preview
        )

        if not before_path or not before_path.exists():
            logger.error("Failed to capture 'before' screenshot")
            return None

        # Step 2: Capture "after" screenshot with injected CSS
        logger.info("Capturing 'after' screenshot with injected CSS")
        after_path = await service.capture(
            url=screenshot_url,
            output_filename="preview_after.png",
            full_page=True,
            css=css_modification.css_content,
        )

        if not after_path or not after_path.exists():
            logger.error("Failed to capture 'after' screenshot")
            return None

        # Step 4: Generate diff image
        diff_path = service.cache_dir / "preview_diff.png"
        diff_result_path, diff_stats = service.generate_diff(
            before_path, after_path, diff_path
        )

        if "error" in diff_stats:
            logger.warning(f"Diff generation failed: {diff_stats['error']}")
            # Continue without diff

        # Step 5: Create composite image
        composite_path = None
        if diff_result_path and diff_result_path.exists():
            composite_path = service.create_composite(
                before_path,
                diff_result_path,
                after_path,
                service.cache_dir / "preview_composite.png",
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


def _inject_css_reference(content: str, css_path: str) -> str:
    """Inject or update CSS reference in QMD frontmatter.
    
    Args:
        content: Markdown content with YAML frontmatter
        css_path: Relative path to CSS file
        
    Returns:
        Updated content with CSS reference
    """
    # Pattern to find YAML frontmatter at start of file
    yaml_pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.search(yaml_pattern, content, re.DOTALL)
    
    if match:
        frontmatter = match.group(1)
        # Check if css key exists
        if re.search(r"^css:\s*", frontmatter, re.MULTILINE):
            # Already has css, check if our path is present
            if css_path not in frontmatter:
                # Append to existing css (simplistic handling for list)
                # If it's a list [a, b], insert c. If single val, make list.
                # For now, just logging warning or assuming single line replacement might be risky.
                # Safest: Replace 'css: .*' with 'css: [old, new]'?
                # Given strict QMD structure, we'll skip if exists to avoid breaking complex YAML
                logger.warning(f"CSS key exists in frontmatter. Not modifying to avoid YAML errors. Please check manually.")
                return content
        else:
            # Insert css entry at end of frontmatter
            new_frontmatter = frontmatter + f"\ncss: {css_path}"
            return content.replace(frontmatter, new_frontmatter)
    else:
        # No frontmatter? Create it.
        return f"---\ncss: {css_path}\n---\n\n{content}"
    
    return content


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

    design_loop_active = state.get("design_loop_active", False)
    design_iteration = state.get("design_iteration", 0)

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

        # 6. Save CSS to design_iter folder for history/preview (Independent of auto_design)
        if design_loop_active and css_mod and css_mod.validation_passed:
             iter_name = f"design_iter{design_iteration + 1}"
             session_dir = state.get("session_dir")
             if session_dir:
                 iter_dir = Path(session_dir) / iter_name / "styles"
                 iter_dir.mkdir(parents=True, exist_ok=True)
                 iter_css_path = iter_dir / "resume-custom.css"
                 try:
                     iter_css_path.write_text(css_mod.css_content, encoding="utf-8")
                     logger.info(f"Saved CSS copy to {iter_css_path}")
                 except Exception as e:
                     logger.error(f"Failed to save CSS copy to iteration folder: {e}")
             else:
                 logger.debug("No session_dir, skipping CSS artifact save")

        # Increment design iteration
        if design_loop_active:
            result["design_iteration"] = design_iteration + 1
            logger.info(f"Incremented design iteration to {design_iteration + 1}")

        # Only return early if auto-design is NOT enabled (preview only mode)
        if not auto_design:
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
        
        # Inject CSS reference into revised_content (or original resume content)
        # using the LOCAL path (styles/resume-custom.css) which works for both
        # root and iteration folder if file structure is preserved
        current_content = state.get("revised_content")
        if not current_content:
             resume = state.get("resume")
             if resume and hasattr(resume, "content"):
                 current_content = resume.content
        
        if current_content:
            new_content = _inject_css_reference(current_content, "styles/resume-custom.css")
            if new_content != current_content:
                result["revised_content"] = new_content
                logger.info("Injected 'css: styles/resume-custom.css' into resume frontmatter")

        logger.info(f"Design modifications applied: {changes_list}")

    return result
