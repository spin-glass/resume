"""Router node for fan-out coordination in the LangGraph workflow."""

import logging
from typing import Any

from ..state import ReviewState

logger = logging.getLogger("resume_review")


async def router_node(state: ReviewState) -> dict[str, Any]:
    """
    Router node that initiates parallel agent evaluation.

    This is a stateless fan-out node. LangGraph handles the actual
    parallel execution via multiple outgoing edges (router → recruiter,
    router → tech_writer, router → copywriter).

    Args:
        state: Full workflow state containing resume and target_role

    Returns:
        Empty dict (no state changes) - parallel execution triggered by edges
    """
    current_iteration = state.current_iteration
    logger.info(f"Router: Starting agent evaluation (iteration {current_iteration + 1})")

    return {}  # LangGraph executes all outgoing edges in parallel
