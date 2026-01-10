"""Theme recommender service for Quarto themes.

This service analyzes design feedback and recommends Quarto themes
when systematic design issues are detected (3+ issues of the same type).
"""

import logging
from collections import Counter

from ..models.design import DesignIssueType, ThemeRecommendation
from ..models.feedback import Feedback

logger = logging.getLogger(__name__)

# Theme profiles with strengths and issue types they address (T061)
THEME_PROFILES = {
    "cosmo": {
        "strengths": [
            "Excellent readability with clean typography",
            "Good spacing and whitespace utilization",
            "Professional appearance",
        ],
        "good_for": [DesignIssueType.SPACING, DesignIssueType.TYPOGRAPHY],
        "pdf_support": True,
        "preview_url": "https://bootswatch.com/cosmo/",
        "config": {
            "format": {
                "pdf": {
                    "theme": "cosmo",
                    "fontfamily": "libertinus",
                }
            }
        },
    },
    "simplex": {
        "strengths": [
            "Minimal, clean design",
            "Strong typography hierarchy",
            "Excellent for technical documents",
        ],
        "good_for": [DesignIssueType.HIERARCHY, DesignIssueType.TYPOGRAPHY],
        "pdf_support": True,
        "preview_url": "https://bootswatch.com/simplex/",
        "config": {
            "format": {
                "pdf": {
                    "theme": "simplex",
                }
            }
        },
    },
    "flatly": {
        "strengths": [
            "Flat design with modern aesthetics",
            "Good color balance",
            "Clear visual hierarchy",
        ],
        "good_for": [DesignIssueType.COLOR, DesignIssueType.HIERARCHY],
        "pdf_support": True,
        "preview_url": "https://bootswatch.com/flatly/",
        "config": {
            "format": {
                "pdf": {
                    "theme": "flatly",
                }
            }
        },
    },
    "readable": {
        "strengths": [
            "Optimized for long-form reading",
            "Generous line spacing",
            "High contrast for accessibility",
        ],
        "good_for": [DesignIssueType.COLOR, DesignIssueType.TYPOGRAPHY, DesignIssueType.SPACING],
        "pdf_support": True,
        "preview_url": "https://bootswatch.com/readable/",
        "config": {
            "format": {
                "pdf": {
                    "theme": "readable",
                }
            }
        },
    },
    "journal": {
        "strengths": [
            "Professional academic style",
            "Clean and formal layout",
            "Good balance of elements",
        ],
        "good_for": [DesignIssueType.LAYOUT, DesignIssueType.TYPOGRAPHY],
        "pdf_support": True,
        "preview_url": "https://bootswatch.com/journal/",
        "config": {
            "format": {
                "pdf": {
                    "theme": "journal",
                }
            }
        },
    },
    "lumen": {
        "strengths": [
            "Light, airy design",
            "Excellent whitespace",
            "Modern professional look",
        ],
        "good_for": [DesignIssueType.SPACING, DesignIssueType.LAYOUT],
        "pdf_support": True,
        "preview_url": "https://bootswatch.com/lumen/",
        "config": {
            "format": {
                "pdf": {
                    "theme": "lumen",
                }
            }
        },
    },
    "spacelab": {
        "strengths": [
            "Clean, technical aesthetic",
            "Good for developer/engineer resumes",
            "Balanced layout",
        ],
        "good_for": [DesignIssueType.LAYOUT, DesignIssueType.HIERARCHY],
        "pdf_support": True,
        "preview_url": "https://bootswatch.com/spacelab/",
        "config": {
            "format": {
                "pdf": {
                    "theme": "spacelab",
                }
            }
        },
    },
    "yeti": {
        "strengths": [
            "Friendly, approachable design",
            "Good color scheme",
            "Clean typography",
        ],
        "good_for": [DesignIssueType.COLOR, DesignIssueType.TYPOGRAPHY],
        "pdf_support": True,
        "preview_url": "https://bootswatch.com/yeti/",
        "config": {
            "format": {
                "pdf": {
                    "theme": "yeti",
                }
            }
        },
    },
}


class ThemeRecommenderService:
    """Service for recommending Quarto themes based on design issues.

    Analyzes design feedback for systematic issues (3+ of same type)
    and recommends themes that address those specific problems.
    """

    def __init__(self):
        """Initialize theme recommender with theme profiles (T062)."""
        self.theme_profiles = THEME_PROFILES
        self.systematic_threshold = 3  # Minimum issues to trigger recommendation

    def _classify_issue(self, description: str) -> DesignIssueType:
        """Classify issue description into DesignIssueType.

        Args:
            description: Issue description text

        Returns:
            DesignIssueType classification
        """
        desc_lower = description.lower()

        # Spacing keywords
        spacing_kw = ["spacing", "margin", "padding", "gap", "whitespace", "cramped", "crowded"]
        if any(kw in desc_lower for kw in spacing_kw):
            return DesignIssueType.SPACING

        # Typography keywords
        typography_kw = ["font", "size", "line height", "typography", "text", "readable", "legible"]
        if any(kw in desc_lower for kw in typography_kw):
            return DesignIssueType.TYPOGRAPHY

        # Color/Accessibility keywords
        color_kw = ["color", "contrast", "accessibility", "wcag", "dark", "light"]
        if any(kw in desc_lower for kw in color_kw):
            return DesignIssueType.COLOR

        # Hierarchy keywords
        hierarchy_kw = ["hierarchy", "heading", "emphasis", "priority", "prominent", "structure"]
        if any(kw in desc_lower for kw in hierarchy_kw):
            return DesignIssueType.HIERARCHY

        # Layout keywords
        layout_keywords = ["layout", "alignment", "balance", "arrangement", "position"]
        if any(kw in desc_lower for kw in layout_keywords):
            return DesignIssueType.LAYOUT

        # Default to layout
        return DesignIssueType.LAYOUT

    def _count_issue_types(self, feedback_list: list[Feedback]) -> Counter:
        """Count occurrences of each design issue type (T063).

        Args:
            feedback_list: List of design feedback

        Returns:
            Counter mapping DesignIssueType to count
        """
        counts: Counter = Counter()

        for feedback in feedback_list:
            for issue in feedback.issues:
                issue_type = self._classify_issue(issue.description)
                counts[issue_type] += 1

        return counts

    def recommend(
        self,
        feedback_list: list[Feedback],
        current_theme: str | None = None,
    ) -> ThemeRecommendation | None:
        """Recommend a theme based on design feedback (T064).

        Only recommends when 3+ issues of the same type are detected
        (indicating systematic design problems).

        Args:
            feedback_list: List of design feedback
            current_theme: Currently used theme (if any)

        Returns:
            ThemeRecommendation or None if no recommendation needed
        """
        # Count issue types
        issue_counts = self._count_issue_types(feedback_list)

        if not issue_counts:
            logger.info("No design issues found, no theme recommendation")
            return None

        # Find most common issue type
        most_common_type, count = issue_counts.most_common(1)[0]

        # Check if systematic (3+ issues)
        if count < self.systematic_threshold:
            logger.info(
                f"Only {count} {most_common_type.value} issues found "
                f"(threshold: {self.systematic_threshold}). No theme recommendation."
            )
            return None

        # Find best theme for this issue type
        best_theme = self._find_best_theme(most_common_type, current_theme)

        if not best_theme:
            logger.warning(f"No suitable theme found for {most_common_type.value} issues")
            return None

        profile = self.theme_profiles[best_theme]

        # Build rationale
        rationale = self._build_rationale(
            best_theme, most_common_type, count, profile
        )

        return ThemeRecommendation(
            theme_name=best_theme,
            rationale=rationale,
            quarto_config=profile["config"],
            installation_command=f"quarto use theme {best_theme}",
            preview_url=profile.get("preview_url"),
            addresses_issues=profile["good_for"],
        )

    def _find_best_theme(
        self,
        primary_issue: DesignIssueType,
        exclude_theme: str | None = None,
    ) -> str | None:
        """Find best theme for given issue type.

        Args:
            primary_issue: Primary design issue to address
            exclude_theme: Theme to exclude (e.g., current theme)

        Returns:
            Theme name or None
        """
        candidates = []

        for name, profile in self.theme_profiles.items():
            if name == exclude_theme:
                continue
            if not profile.get("pdf_support", False):
                continue
            if primary_issue in profile.get("good_for", []):
                # Score by how well it matches
                score = len([i for i in profile["good_for"] if i == primary_issue])
                candidates.append((name, score, profile))

        if not candidates:
            # Fall back to any theme that addresses this issue type
            for name, profile in self.theme_profiles.items():
                if name == exclude_theme:
                    continue
                if primary_issue in profile.get("good_for", []):
                    return name
            return None

        # Return best candidate
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def _build_rationale(
        self,
        theme_name: str,
        issue_type: DesignIssueType,
        issue_count: int,
        profile: dict,
    ) -> str:
        """Build human-readable rationale for theme recommendation.

        Args:
            theme_name: Recommended theme name
            issue_type: Primary issue type being addressed
            issue_count: Number of issues detected
            profile: Theme profile dict

        Returns:
            Rationale string (at least 20 characters)
        """
        strengths = profile.get("strengths", [])
        strength_text = " ".join(strengths[:2]) if strengths else "good design qualities"

        addressed = ', '.join(t.value for t in profile.get('good_for', []))
        return (
            f"Detected {issue_count} {issue_type.value} issues in your resume design. "
            f"The '{theme_name}' theme is recommended because it provides {strength_text}. "
            f"This theme specifically addresses {addressed} issues."
        )
