"""
Personalizer workflow node.

This node performs resume-job matching analysis and calculates
personalization results within the LangGraph workflow.
"""

import logging

from ...agents.personalizer import PersonalizerAgent
from ...services.llm_factory import create_gemini_client
from ..state import ReviewState

logger = logging.getLogger(__name__)


async def personalizer_node(state: ReviewState) -> dict:
    """
    Analyze resume-job match and generate personalization recommendations.

    This node runs after aggregator when a job posting is present.

    Args:
        state: Current workflow state

    Returns:
        Dict with personalization_result field
    """
    # Only run if job posting is present
    job_posting = state.get("job_posting")
    if not job_posting:
        return {}

    logger.info("=" * 60)
    logger.info("Personalizer Node - Calculating match score")
    logger.info("=" * 60)

    # Get resume from state
    resume = state.get("resume")

    # Initialize personalizer with Gemini (cost-effective for analysis)
    gemini_api_key = state.get("gemini_api_key")
    if not gemini_api_key:
        logger.warning("Gemini API key not available, skipping personalization")
        return {}

    llm_client = create_gemini_client(
        api_key=gemini_api_key,
        model="gemini-2.0-flash-exp"
    )

    personalizer = PersonalizerAgent(llm_client=llm_client)

    try:
        # Perform match analysis
        result = await personalizer.analyze_match(
            resume=resume,
            job_posting=job_posting
        )

        logger.info(f"✓ Match score: {result.match_score:.1f}% ({result.match_level})")
        logger.info(f"  Required: {result.required_match_score:.1f}%")
        logger.info(f"  Preferred: {result.preferred_match_score:.1f}%")
        logger.info(f"  Critical gaps: {len(result.missing_required_skills)}")
        logger.info(f"  Suggestions: {len(result.emphasis_suggestions)}")

        return {
            "personalization_result": result,
        }

    except Exception as e:
        logger.error(f"✗ Personalization analysis failed: {e}")
        # Don't fail the workflow, just skip personalization
        return {}
