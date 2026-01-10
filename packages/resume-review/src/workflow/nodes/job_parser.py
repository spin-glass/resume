"""
Job parser workflow node.

This node handles parsing job postings from files or URLs within
the LangGraph workflow.
"""

import logging
from typing import Any, cast
from pathlib import Path

from ...services.job_parser import JobParserService
from ...services.llm_factory import create_gemini_client
from ..state import ReviewState

logger = logging.getLogger(__name__)


async def job_parser_node(state: ReviewState) -> dict[str, Any]:
    """
    Parse job posting from file or URL and add to state.

    This node runs at the start of the workflow. If no job posting
    is provided, it's a no-op and returns an empty dict.

    Args:
        state: Current workflow state

    Returns:
        Dict with job_posting, job_source_type fields if job posting provided,
        otherwise empty dict

    Raises:
        ValueError: If job posting file/URL is invalid
    """
    job_posting_file = state.job_posting_file
    job_url = state.job_url

    # If no job posting provided, this is a standard (non-personalized) review
    if not job_posting_file and not job_url:
        return {}

    logger.info("=" * 60)
    logger.info("Job Parser Node - Extracting job requirements")
    logger.info("=" * 60)

    # Initialize parser with Gemini (fast and cost-effective for parsing)
    gemini_api_key = state.gemini_api_key
    if not gemini_api_key:
        raise ValueError("Gemini API key required for job parsing")

    llm_client = create_gemini_client(
        api_key=gemini_api_key,
        model="gemini-2.0-flash-exp"  # Fast model for parsing
    )

    parser = JobParserService(llm_client=llm_client)

    # Parse job posting
    try:
        if job_url:
            # Parse from URL
            job_posting = await parser.parse_url(job_url)
            source_type = "url"
        else:
            # Parse from file
            file_path = Path(cast(str, job_posting_file))
            job_posting = await parser.parse_file(file_path)
            source_type = "file"

        logger.info(f"✓ Job posting parsed successfully")
        logger.info(f"  Title: {job_posting.title}")
        if job_posting.company:
            logger.info(f"  Company: {job_posting.company}")
        logger.info(f"  Required skills: {len(job_posting.required_skills)}")
        logger.info(f"  Preferred skills: {len(job_posting.preferred_skills)}")
        logger.info(f"  Responsibilities: {len(job_posting.responsibilities)}")

        return {
            "job_posting": job_posting,
            "job_source_type": source_type,
        }

    except Exception as e:
        logger.error(f"✗ Failed to parse job posting: {e}")
        raise
