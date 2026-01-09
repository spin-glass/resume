"""Content revision service for applying feedback to resume.

DEPRECATED: This module is deprecated in favor of the new RevisorAgent architecture.

The old RevisionService used fuzzy replacement which caused "Fuzzy replacement failed"
errors. The new RevisorAgent (src/agents/revisor.py) uses full-rewrite approach which
eliminates these errors entirely.

New code should use:
  from src.agents.revisor import RevisorAgent

This module is kept for backward compatibility but will be removed in a future version.
"""

import logging
import re
from typing import Optional

import frontmatter
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import ActionType, Severity
from ..models.feedback import Feedback, Issue, Resume

logger = logging.getLogger("resume_review")


class RevisionService:
    """Service for applying content changes while preserving YAML frontmatter.

    DEPRECATED: Use RevisorAgent instead. This class uses fuzzy replacement which
    causes reliability issues. The new RevisorAgent uses full-rewrite approach.
    """

    def __init__(self, api_key: str, model: str = "claude-opus-4-5-20251101"):
        """
        Initialize revision service.

        Args:
            api_key: Anthropic API key
            model: Claude model to use (default: Claude Opus 4.5)
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def apply_revisions(
        self, resume: Resume, feedback_list: list[Feedback], dry_run: bool = False
    ) -> tuple[Resume, list[str]]:
        """
        Apply revisions based on agent feedback.

        Args:
            resume: Current resume
            feedback_list: List of feedback from agents
            dry_run: If True, don't modify content, just return proposed changes

        Returns:
            Tuple of (revised_resume, list of applied revision descriptions)

        Raises:
            ValueError: If YAML frontmatter would be modified
        """
        # Collect all high and critical issues
        issues_to_fix = []
        for feedback in feedback_list:
            for issue in feedback.issues:
                if issue.severity in [Severity.CRITICAL, Severity.HIGH]:
                    issues_to_fix.append((feedback.agent_name, issue))

        if not issues_to_fix:
            return resume, []

        # Limit issues to avoid excessive API calls (max 5 per iteration)
        MAX_ISSUES_PER_ITERATION = 5
        if len(issues_to_fix) > MAX_ISSUES_PER_ITERATION:
            # Prioritize CRITICAL over HIGH
            critical_issues = [(a, i) for a, i in issues_to_fix if i.severity == Severity.CRITICAL]
            high_issues = [(a, i) for a, i in issues_to_fix if i.severity == Severity.HIGH]
            issues_to_fix = (critical_issues + high_issues)[:MAX_ISSUES_PER_ITERATION]
            logger.warning(
                f"RevisionService: Limiting to {MAX_ISSUES_PER_ITERATION} issues per iteration "
                f"(was {len(critical_issues) + len(high_issues)})"
            )

        logger.info(f"RevisionService: Processing {len(issues_to_fix)} HIGH/CRITICAL issues")

        # Group issues by action type
        revisions_applied = []
        revised_content = resume.content

        # Process issues in priority order
        for idx, (agent_name, issue) in enumerate(issues_to_fix):
            logger.info(f"RevisionService: Processing issue {idx + 1}/{len(issues_to_fix)}: {issue.description[:50]}...")
            if dry_run:
                # In dry-run mode, just log what would be changed
                revisions_applied.append(
                    f"[DRY RUN] Would apply {issue.action_type.value}: {issue.description}"
                )
                continue

            # Apply revision based on action type
            try:
                new_content = self._apply_single_revision(
                    revised_content, issue, agent_name
                )
                if new_content != revised_content:
                    revised_content = new_content
                    revisions_applied.append(
                        f"Applied {issue.action_type.value} from {agent_name}: {issue.description}"
                    )
            except Exception as e:
                revisions_applied.append(
                    f"Failed to apply {issue.action_type.value}: {issue.description} - {e}"
                )

        # ALWAYS apply auto-fix (removes standalone #, fixes spacing, etc.)
        fixed_content = self._auto_fix_structure(revised_content)
        if fixed_content != revised_content:
            logger.info("Applied automatic structural fixes")
            revised_content = fixed_content
            revisions_applied.append("[AUTO-FIX] Applied structural corrections")

        # Validate structural integrity after auto-fix
        validation_issues = self._validate_structure(revised_content, resume.content)
        if validation_issues:
            logger.warning(f"Structural validation found {len(validation_issues)} issues")
            for issue in validation_issues:
                logger.warning(f"  - {issue}")
                revisions_applied.append(f"[VALIDATION WARNING] {issue}")

        # Create new Resume with revised content (preserving YAML)
        # Use frontmatter library to properly serialize YAML
        post = frontmatter.Post(revised_content, **resume.yaml_frontmatter)
        full_text = frontmatter.dumps(post)

        revised_resume = Resume.model_construct(
            file_path=resume.file_path,
            yaml_frontmatter=resume.yaml_frontmatter.copy(),  # Preserve unchanged
            content=revised_content,
            full_text=full_text,
        )

        return revised_resume, revisions_applied

    def _apply_single_revision(
        self, content: str, issue: Issue, agent_name: str
    ) -> str:
        """
        Apply a single revision to content.

        Args:
            content: Current content
            issue: Issue to fix
            agent_name: Name of agent that identified the issue

        Returns:
            Revised content
        """
        # Extract the specific section to revise (if location specified)
        section_content, section_start, section_end = self._extract_section(
            content, issue.location
        )

        # Build prompt with only the relevant section
        prompt = self._build_revision_prompt(
            section_content, issue, agent_name, full_content=content
        )

        # Call Claude to generate revision
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system="""You are an expert resume editor for Japanese resumes.

CRITICAL RULES:
1. Return ONLY the revised section content - NOT the entire resume
2. Do NOT include any headers (##, ###) unless they were in the original section
3. Do NOT add explanations or commentary - just the revised content
4. Make minimal, precise changes to address the specific issue
5. Do NOT fabricate experience or credentials
6. Keep the same language (Japanese) as the original
7. Preserve formatting (bullet points, indentation)""",
            messages=[{"role": "user", "content": prompt}],
        )

        revised_section = response.content[0].text.strip()

        # Clean up response - remove any accidental full resume returns
        revised_section = self._clean_revision_response(revised_section, issue.location)

        # Integrate the revision back into the original content
        if section_start is not None and section_end is not None:
            # Replace the specific section
            logger.debug(f"Replacing section at {section_start}:{section_end}")
            return (
                content[:section_start] +
                revised_section +
                content[section_end:]
            )
        else:
            # Fallback: Section not found by location
            original_lines = len(content.splitlines())
            revised_lines = len(revised_section.splitlines())

            logger.debug(
                f"Section not found for location '{issue.location}'. "
                f"Original: {original_lines} lines, Revised: {revised_lines} lines"
            )

            # If revised section is more than 50% of original, it's likely the full resume
            if revised_lines > original_lines * 0.5:
                logger.debug("Accepting full resume replacement")
                return revised_section
            elif revised_lines >= 1:
                # If Claude returned any revision, try to apply it by fuzzy matching
                logger.debug("Attempting fuzzy section replacement")
                result = self._fuzzy_replace_section(content, revised_section, issue.location)
                if result != content:
                    return result
                # If fuzzy replacement failed but we have a location, try line-based matching
                if issue.location:
                    logger.debug("Fuzzy replacement failed, attempting line-based matching")
                    return self._line_based_replacement(content, revised_section, issue.location)
                logger.warning(f"Could not apply revision: {revised_lines} lines")
                return content
            else:
                # Empty revision - return original (no change)
                logger.warning("Revision is empty, returning original content")
                return content

    def _validate_structure(self, revised_content: str, original_content: str) -> list[str]:
        """
        Validate structural integrity of revised content.

        Checks for common degradation issues:
        1. Headers merged with previous line (no blank line before ##)
        2. Section count decreased unexpectedly
        3. Major formatting issues

        Returns:
            List of validation issue descriptions (empty if no issues)
        """
        issues = []

        # Check 1: Headers should have blank line before them (except first header)
        # Pattern: non-whitespace character followed by 0 or 1 newline, then ## header
        # This catches both "text。##" and "text。\n##" cases
        # We need to find headers that don't have a blank line before them
        lines = revised_content.split('\n')
        original_lines = original_content.split('\n')

        for i, line in enumerate(lines):
            if re.match(r'^##\s+', line):  # This is a header
                # Check if there's a blank line before it
                if i > 0:  # Not the first line
                    prev_line = lines[i-1].strip()
                    if prev_line != '':  # Previous line is not blank
                        # Check if this was also a problem in original
                        header_text = line[:30]
                        is_original_issue = False

                        # Find this header in original
                        for j, orig_line in enumerate(original_lines):
                            if orig_line.strip() == line.strip() and j > 0:
                                if original_lines[j-1].strip() != '':
                                    is_original_issue = True
                                    break

                        if not is_original_issue:
                            issues.append(f"Header '{header_text}...' is merged with previous line (missing blank line)")

        # Check 2: Count major sections (## headers)
        original_sections = len(re.findall(r'^##\s+', original_content, re.MULTILINE))
        revised_sections = len(re.findall(r'^##\s+', revised_content, re.MULTILINE))

        if revised_sections < original_sections:
            issues.append(
                f"Section count decreased from {original_sections} to {revised_sections} "
                "(possible section merge or deletion)"
            )

        # Check 3: Detect incomplete sentences at end of paragraphs
        # Pattern: ends with 'いま' or 'です' followed by newline and header
        incomplete_before_header = re.findall(
            r'(従事していま|開発していま|取り組んでいま|担当していま|参画していま)\n+##',
            revised_content
        )
        if incomplete_before_header and not re.search(
            r'(従事していま|開発していま|取り組んでいま|担当していま|参画していま)\n+##',
            original_content
        ):
            issues.append(f"Incomplete sentence found before section header")

        return issues

    def _auto_fix_structure(self, content: str) -> str:
        """
        Automatically fix common structural issues.

        Fixes:
        1. Remove standalone # markers (visual separators that break Quarto)
        2. Add blank line before ## headers when missing
        3. Ensure proper spacing around headers

        Returns:
            Fixed content
        """
        fixed = content

        # Fix 1: Remove standalone # markers (visual separators Claude sometimes adds)
        # Pattern: blank line + # + blank line → keep the spacing
        fixed = re.sub(r'\n\s*#\s*\n', '\n\n', fixed)

        # Fix 2: Ensure blank line before all ## headers (except first line)
        # Pattern: non-whitespace character, 0 or 1 newline, then ## header
        # Replace with: non-whitespace, two newlines, then header
        # First pass: Fix cases with NO newline (text。##)
        fixed = re.sub(
            r'([^\s])(##\s+)',
            r'\1\n\n\2',
            fixed
        )
        # Second pass: Fix cases with single newline (text。\n##)
        fixed = re.sub(
            r'([^\n])\n(##\s+)',
            r'\1\n\n\2',
            fixed
        )

        # Fix 3: Ensure single blank line after ## headers
        # Pattern: ## header followed by multiple newlines
        fixed = re.sub(
            r'(^##[^\n]+)\n{3,}',
            r'\1\n\n',
            fixed,
            flags=re.MULTILINE
        )

        # Fix 4: Remove trailing whitespace at end of lines
        lines = fixed.splitlines(keepends=True)
        fixed = ''.join(line.rstrip() + '\n' if line.strip() else '\n' for line in lines)

        # Fix 5: Remove excessive blank lines (more than 2 consecutive)
        fixed = re.sub(r'\n{4,}', '\n\n\n', fixed)

        return fixed.rstrip() + '\n' if fixed.rstrip() else fixed

    def _extract_section(
        self, content: str, location: Optional[str]
    ) -> tuple[str, Optional[int], Optional[int]]:
        """
        Extract a specific section from the content.

        Args:
            content: Full content
            location: Section name to extract

        Returns:
            Tuple of (section_content, start_index, end_index)
            If location not found, returns (full_content, None, None)
        """
        if not location:
            return content, None, None

        # Try to find section by header (markdown # syntax)
        section_pattern = rf"(^#{1,3}\s+{re.escape(location)}\s*$)"
        match = re.search(section_pattern, content, re.MULTILINE | re.IGNORECASE)

        if not match:
            # Try partial match for headers
            section_pattern = rf"(^#{1,3}\s+[^#\n]*{re.escape(location)}[^#\n]*$)"
            match = re.search(section_pattern, content, re.MULTILINE | re.IGNORECASE)

        if match:
            # Found header - extract section
            section_start = match.start()
            header_level = match.group(1).count('#')

            # Find where section ends
            remaining = content[match.end():]
            next_pattern = rf"^#{{{1},{header_level}}}\s+\S"
            next_match = re.search(next_pattern, remaining, re.MULTILINE)

            if next_match:
                section_end = match.end() + next_match.start()
            else:
                section_end = len(content)

            section_content = content[section_start:section_end]
            return section_content, section_start, section_end

        # Try to find section by bullet point item (- **項目名**)
        bullet_pattern = rf"(^\s*-\s+\*\*{re.escape(location)}\*\*)"
        match = re.search(bullet_pattern, content, re.MULTILINE | re.IGNORECASE)

        if not match:
            # Try partial match for bullet points
            bullet_pattern = rf"(^\s*-\s+\*\*[^\*\n]*{re.escape(location)}[^\*\n]*\*\*)"
            match = re.search(bullet_pattern, content, re.MULTILINE | re.IGNORECASE)

        if match:
            # Found bullet point - extract until next bullet at same or higher level
            section_start = match.start()

            # Detect indentation level
            indent_match = re.match(r'^(\s*)', content[section_start:])
            indent_level = len(indent_match.group(1)) if indent_match else 0

            # Find where this bullet section ends (next bullet at same/higher level, or next header)
            remaining = content[match.end():]

            # Pattern: same/higher level bullet OR any header
            next_bullet_pattern = r"^[ ]{0," + str(indent_level) + r"}- \*\*"
            next_header_pattern = r"^#{1,3}\s+\S"

            next_bullet_match = re.search(next_bullet_pattern, remaining, re.MULTILINE)
            next_header_match = re.search(next_header_pattern, remaining, re.MULTILINE)

            # Find earliest match
            end_positions = []
            if next_bullet_match:
                end_positions.append(match.end() + next_bullet_match.start())
            if next_header_match:
                end_positions.append(match.end() + next_header_match.start())

            if end_positions:
                section_end = min(end_positions)
            else:
                section_end = len(content)

            section_content = content[section_start:section_end]
            logger.debug(f"Found bullet point section '{location}' at {section_start}:{section_end}")
            return section_content, section_start, section_end

        # No match found
        return content, None, None

    def _clean_revision_response(
        self, response: str, location: Optional[str]
    ) -> str:
        """
        Clean up Claude's response to ensure it's just the section content.

        Args:
            response: Raw response from Claude
            location: Expected section location

        Returns:
            Cleaned section content
        """
        # Remove common prefixes Claude might add
        prefixes_to_remove = [
            "Here is the revised",
            "Here's the revised",
            "Revised section:",
            "Updated content:",
            "修正後:",
            "以下が修正版",
        ]

        cleaned = response
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].lstrip(":").lstrip()

        # Check if response contains full resume indicators
        full_resume_indicators = [
            "# 職務経歴書",
            "## 基本情報",
            "## 職務要約",
            "## 経歴",
            "## スキル",
        ]

        # Count how many indicators are present
        indicator_count = sum(1 for ind in full_resume_indicators if ind in cleaned)

        # If multiple indicators present, it's likely the full resume
        if indicator_count >= 2 and location:
            # Try to extract just the relevant section
            section_content, start, end = self._extract_section(cleaned, location)
            if start is not None:
                cleaned = section_content

        # Remove trailing explanations
        explanation_markers = [
            "\n\n---\n",
            "\n\nNote:",
            "\n\n注:",
            "\n\n※",
        ]
        for marker in explanation_markers:
            if marker in cleaned:
                cleaned = cleaned[:cleaned.index(marker)]

        return cleaned.strip()

    def _build_revision_prompt(
        self, section_content: str, issue: Issue, agent_name: str, full_content: str = ""
    ) -> str:
        """Build prompt for generating revision."""
        action_instructions = {
            ActionType.ADD_CONTENT: "Add missing information to address this gap",
            ActionType.RESTRUCTURE: "Reorganize the content to improve clarity and flow",
            ActionType.EMPHASIZE: "Strengthen and highlight the existing content",
            ActionType.REMOVE: "Remove unnecessary or redundant content",
            ActionType.QUANTIFY: "Add specific metrics and numbers to quantify impact",
            ActionType.ADD_PORTFOLIO: "Note: Portfolio projects will be suggested separately",
        }

        instruction = action_instructions.get(issue.action_type, "Improve the content")

        location_context = f"'{issue.location}'" if issue.location else "the content"

        return f"""## Task
Revise ONLY the following section to address the issue. Return THE COMPLETE REVISED SECTION with all content, not just the changed parts.

## Section to revise ({location_context}):
```
{section_content}
```

## Issue ({issue.severity.value} priority, from {agent_name}):
{issue.description}

## Action required:
{instruction}

## CRITICAL INSTRUCTIONS:
1. Return THE COMPLETE revised section with ALL paragraphs, not just the changed parts
2. If the section starts with a header (##, ###), include that header in your response
3. Include ALL existing content from the section, with your modifications applied
4. Do NOT return the entire resume - only the section being revised
5. Keep Japanese language
6. Do NOT fabricate - only enhance truthful presentation
7. Preserve the original structure and formatting"""

    def _line_based_replacement(
        self, content: str, revised_section: str, location: Optional[str]
    ) -> str:
        """
        Attempt line-based replacement for small fixes like incomplete sentences.

        This method looks for specific incomplete patterns and replaces them.
        """
        # Check if this is an incomplete sentence issue (common pattern: ends with 'いま', 'です', etc without proper ending)
        lines = content.splitlines(keepends=True)
        revised_lines = revised_section.strip().splitlines()

        if not revised_lines:
            return content

        # Look for the problematic line in the original content
        # Common incomplete sentence patterns in Japanese
        incomplete_patterns = [
            r'従事していま$',
            r'開発していま$',
            r'取り組んでいま$',
            r'担当していま$',
            r'参画していま$',
        ]

        for i, line in enumerate(lines):
            stripped_line = line.rstrip()
            for pattern in incomplete_patterns:
                if re.search(pattern, stripped_line):
                    logger.debug(f"Found incomplete sentence at line {i+1}: {stripped_line[:50]}...")
                    # Try to find a corresponding complete line in revised_section
                    for revised_line in revised_lines:
                        revised_stripped = revised_line.strip()
                        # If the revised line starts similarly but is complete
                        if revised_stripped and not re.search(pattern, revised_stripped):
                            # Check if they share significant content
                            if any(word in revised_stripped for word in stripped_line.split()[:5]):
                                logger.debug(f"Replacing with: {revised_stripped[:50]}...")
                                lines[i] = revised_stripped + '\n'
                                return ''.join(lines)

        logger.debug("No incomplete sentence patterns found for line-based replacement")
        return content

    def _fuzzy_replace_section(
        self, content: str, revised_section: str, location: Optional[str]
    ) -> str:
        """
        Attempt to replace a section using fuzzy matching when exact location fails.

        Args:
            content: Full content
            revised_section: The revised section from Claude
            location: Hint about where the section should be

        Returns:
            Updated content with section replaced, or original if no match found
        """
        # If revised_section starts with a header, try to find that header in content
        revised_lines = revised_section.strip().splitlines()
        if not revised_lines:
            return content

        first_line = revised_lines[0].strip()

        # Check if first line is a header
        if first_line.startswith('#'):
            # Count header level (number of # characters)
            header_level = len(first_line) - len(first_line.lstrip('#'))

            # SAFETY: Never replace top-level headers (single #) as this would replace entire document
            if header_level == 1:
                logger.warning(
                    f"Refusing to replace top-level header '{first_line[:50]}...' - "
                    "would replace entire document"
                )
                return content

            # Try to find this header in the original content
            header_pattern = rf"(^{re.escape(first_line)}\s*$)"
            match = re.search(header_pattern, content, re.MULTILINE)

            if match:
                # Found the header - extract and replace that section
                section_start = match.start()

                # Find where section ends
                remaining = content[match.end():]
                next_pattern = rf"^#{{{1},{header_level}}}\s+\S"
                next_match = re.search(next_pattern, remaining, re.MULTILINE)

                if next_match:
                    section_end = match.end() + next_match.start()
                else:
                    section_end = len(content)

                # SAFETY: Refuse if replacement would affect more than 40% of document
                replacement_ratio = (section_end - section_start) / len(content)
                if replacement_ratio > 0.4:
                    logger.warning(
                        f"Refusing fuzzy replacement: would affect {replacement_ratio*100:.0f}% "
                        f"of document ({section_end - section_start}/{len(content)} chars)"
                    )
                    return content

                logger.debug(f"Fuzzy match found header '{first_line}' at {section_start}:{section_end}")
                return (
                    content[:section_start] +
                    revised_section +
                    content[section_end:]
                )

        # Check if first line is a bullet point (- **項目名**)
        bullet_match = re.match(r'^\s*-\s+\*\*(.+?)\*\*', first_line)
        if bullet_match:
            bullet_title = bullet_match.group(1).strip()

            # Try to find this bullet in the original content
            bullet_pattern = rf"(^\s*-\s+\*\*{re.escape(bullet_title)}\*\*)"
            match = re.search(bullet_pattern, content, re.MULTILINE)

            if match:
                # Found bullet point - extract and replace that section
                section_start = match.start()

                # Detect indentation level
                indent_match = re.match(r'^(\s*)', content[section_start:])
                indent_level = len(indent_match.group(1)) if indent_match else 0

                # Find where this bullet section ends
                remaining = content[match.end():]
                next_bullet_pattern = r"^[ ]{0," + str(indent_level) + r"}- \*\*"
                next_header_pattern = r"^#{1,3}\s+\S"

                next_bullet_match = re.search(next_bullet_pattern, remaining, re.MULTILINE)
                next_header_match = re.search(next_header_pattern, remaining, re.MULTILINE)

                end_positions = []
                if next_bullet_match:
                    end_positions.append(match.end() + next_bullet_match.start())
                if next_header_match:
                    end_positions.append(match.end() + next_header_match.start())

                if end_positions:
                    section_end = min(end_positions)
                else:
                    section_end = len(content)

                # SAFETY: Refuse if replacement would affect more than 40% of document
                replacement_ratio = (section_end - section_start) / len(content)
                if replacement_ratio > 0.4:
                    logger.warning(
                        f"Refusing fuzzy replacement: would affect {replacement_ratio*100:.0f}% "
                        f"of document ({section_end - section_start}/{len(content)} chars)"
                    )
                    return content

                logger.debug(f"Fuzzy match found bullet point '{bullet_title}' at {section_start}:{section_end}")
                return (
                    content[:section_start] +
                    revised_section +
                    content[section_end:]
                )

        # If location hint is provided, try partial matching
        if location:
            # Try to find a section containing the location keyword
            for keyword in location.split():
                if len(keyword) < 3:
                    continue

                # Try header match
                pattern = rf"(^#{1,3}\s+[^\n]*{re.escape(keyword)}[^\n]*$)"
                match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
                if match:
                    header_level = match.group(1).count('#')
                    section_start = match.start()

                    remaining = content[match.end():]
                    next_pattern = rf"^#{{{1},{header_level}}}\s+\S"
                    next_match = re.search(next_pattern, remaining, re.MULTILINE)

                    if next_match:
                        section_end = match.end() + next_match.start()
                    else:
                        section_end = len(content)

                    logger.debug(f"Fuzzy match found keyword '{keyword}' in header at {section_start}:{section_end}")
                    return (
                        content[:section_start] +
                        revised_section +
                        content[section_end:]
                    )

                # Try bullet point match
                bullet_pattern = rf"(^\s*-\s+\*\*[^\*\n]*{re.escape(keyword)}[^\*\n]*\*\*)"
                match = re.search(bullet_pattern, content, re.MULTILINE | re.IGNORECASE)
                if match:
                    section_start = match.start()

                    # Detect indentation level
                    indent_match = re.match(r'^(\s*)', content[section_start:])
                    indent_level = len(indent_match.group(1)) if indent_match else 0

                    # Find where this bullet section ends
                    remaining = content[match.end():]
                    next_bullet_pattern = r"^[ ]{0," + str(indent_level) + r"}- \*\*"
                    next_header_pattern = r"^#{1,3}\s+\S"

                    next_bullet_match = re.search(next_bullet_pattern, remaining, re.MULTILINE)
                    next_header_match = re.search(next_header_pattern, remaining, re.MULTILINE)

                    end_positions = []
                    if next_bullet_match:
                        end_positions.append(match.end() + next_bullet_match.start())
                    if next_header_match:
                        end_positions.append(match.end() + next_header_match.start())

                    if end_positions:
                        section_end = min(end_positions)
                    else:
                        section_end = len(content)

                    logger.debug(f"Fuzzy match found keyword '{keyword}' in bullet at {section_start}:{section_end}")
                    return (
                        content[:section_start] +
                        revised_section +
                        content[section_end:]
                    )

        # No match found - return original
        logger.warning(f"Fuzzy replacement failed for location '{location}'")
        return content
