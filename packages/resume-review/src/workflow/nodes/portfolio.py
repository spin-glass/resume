"""Portfolio analyzer node for identifying skill gaps and suggesting projects."""

import json
import logging
import re
from typing import Any

from ...models import ActionType
from ...models.portfolio import PortfolioItem
from ..state import ReviewState

logger = logging.getLogger("resume_review")


def portfolio_analyzer_node(state: ReviewState) -> dict[str, Any]:
    """
    Portfolio analyzer node that identifies skill gaps and suggests projects.

    Analyzes feedback for ADD_PORTFOLIO actions and generates suggestions.
    """
    logger.info("Portfolio Analyzer: Identifying skill gaps")

    api_key = state["api_key"]
    target_role = state["target_role"]
    feedback_history = state.get("feedback_history", [])

    # Collect all ADD_PORTFOLIO issues
    portfolio_issues = []
    for feedback_iteration in feedback_history:
        for feedback in feedback_iteration:
            for issue in feedback.issues:
                if issue.action_type == ActionType.ADD_PORTFOLIO:
                    portfolio_issues.append((feedback.agent_name, issue))

    if not portfolio_issues:
        logger.info("Portfolio Analyzer: No skill gaps requiring portfolio projects")
        return {"portfolio_suggestions": [], "skill_gaps": []}

    logger.info(
        f"Portfolio Analyzer: Found {len(portfolio_issues)} skill gaps"
    )

    # Generate portfolio suggestions
    suggestions = []
    skill_gaps = []

    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)

    for agent_name, issue in portfolio_issues:
        skill_gaps.append(issue.description)

        try:
            prompt = f"""Based on this skill gap for a {target_role} position:

Skill Gap: {issue.description}
Location: {issue.location or 'General'}
Severity: {issue.severity.value}

Suggest a portfolio project that would demonstrate this skill. Provide:
1. Repository name (format: {{technology}}-{{type}}, lowercase with hyphens)
2. List of 2-3 skills this project demonstrates
3. Brief description (1-2 sentences)
4. Priority (1-3, where 1 is highest)

Format your response as JSON:
{{
  "repository_name": "example-project",
  "skills": ["Skill1", "Skill2"],
  "description": "Brief description of what this project demonstrates",
  "priority": 1
}}"""

            response = client.messages.create(
                model="claude-opus-4-5-20251101",
                max_tokens=1000,
                system="You are an expert at identifying valuable portfolio projects for software engineers.",
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)

            if json_match:
                data = json.loads(json_match.group())

                github_url = PortfolioItem.generate_github_url(
                    "spin-glass", data["repository_name"]
                )
                demo_url = None

                if any(
                    keyword in data["repository_name"].lower()
                    for keyword in ["web", "app", "frontend", "ui", "dashboard"]
                ):
                    demo_url = PortfolioItem.generate_demo_url(data["repository_name"])

                portfolio_item = PortfolioItem(
                    repository_name=data["repository_name"],
                    skills=data["skills"],
                    description=data["description"],
                    github_url=github_url,
                    demo_url=demo_url,
                    priority=data.get("priority", 2),
                )
                suggestions.append(portfolio_item)
                logger.debug(f"Generated portfolio: {portfolio_item.repository_name}")

        except Exception as e:
            logger.error(f"Failed to generate portfolio suggestion: {e}")

    return {"portfolio_suggestions": suggestions, "skill_gaps": skill_gaps}
