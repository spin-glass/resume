"""Revisor node for applying content revisions."""

import logging
from typing import Any

from ...services.revision import RevisionService
from ..state import ReviewState

logger = logging.getLogger("resume_review")


def revisor_node(state: ReviewState) -> dict[str, Any]:
    """
    Revisor node that applies content revisions based on feedback.

    Uses RevisionService to modify resume content while preserving YAML.
    """
    logger.info("Revisor: Applying content revisions")

    api_key = state["api_key"]
    resume = state["resume"]
    current_feedback = state.get("current_feedback", [])
    dry_run = state.get("dry_run", False)

    revision_service = RevisionService(api_key)

    try:
        revised_resume, revisions = revision_service.apply_revisions(
            resume, current_feedback, dry_run=dry_run
        )

        # Update state with revisions
        result = {
            "applied_revisions": revisions,
            "current_iteration": state.get("current_iteration", 0) + 1,
        }

        if not dry_run:
            result["resume"] = revised_resume
            result["resume_content"] = revised_resume.content
            result["revised_content"] = revised_resume.content

        logger.info(f"Revisor: Applied {len(revisions)} revisions")
        return result

    except Exception as e:
        logger.error(f"Revisor node failed: {e}")
        return {"error": str(e), "applied_revisions": [f"Error: {str(e)}"]}
