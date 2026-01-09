# Revision Service Contract

**Branch**: `001-resume-review-agents` | **Date**: 2026-01-09 | **Related**: [spec.md](../spec.md), [plan.md](../plan.md)

## Overview

The Revision Service is responsible for converting agent feedback (Issues and Suggestions) into concrete edits to the resume QMD file. It acts as the bridge between evaluation agents and the actual file modification.

**Key Distinction**: This is a **service**, not an agent. It does not use LLM inference for decision-making; instead, it applies structured edits based on agent feedback.

---

## Service Interface

```python
from typing import Protocol
from pathlib import Path

class RevisionService(Protocol):
    """
    Service for applying structured revisions to resume content.

    This service translates agent feedback into concrete QMD file edits
    while preserving YAML frontmatter and maintaining document structure.
    """

    async def apply_revisions(
        self,
        resume: Resume,
        feedback_list: list[Feedback],
        dry_run: bool = False
    ) -> RevisionResult:
        """
        Apply all suggested revisions from agent feedback.

        Args:
            resume: Resume entity with current content
            feedback_list: Aggregated feedback from all agents
            dry_run: If True, simulate changes without modifying file

        Returns:
            RevisionResult with applied changes and updated content

        Raises:
            RevisionError: If revision application fails
            YAMLPreservationError: If YAML frontmatter would be corrupted
        """
        pass
```

---

## Revision Strategy by Action Type

### 1. ADD_CONTENT

**Purpose**: Add missing information to existing sections

**Strategy**:
1. Identify target section via `location` field
2. Use LLM to generate new content matching the suggestion
3. Insert at appropriate position within section
4. Preserve existing formatting and style

**Example**:

```python
# Issue
Issue(
    description="Missing LLM project experience summary",
    action_type=ActionType.ADD_CONTENT,
    location="Experience → Acme Corp",
    severity=Severity.HIGH
)

# Revision
# Find "## Experience" section → "### Acme Corp" subsection
# Add bullet point: "- Led development of LLM-powered chatbot using GPT-4..."
```

---

### 2. ADD_PORTFOLIO

**Purpose**: Create portfolio section with suggested projects

**Strategy**:
1. Check if "## Portfolio" section exists; create if not
2. For each `PortfolioItem` in suggestions:
   - Format as markdown link: `[project-name](github-url)`
   - Add description and skills list
   - Ensure consistent formatting
3. Place portfolio section after Experience but before Skills

**Example**:

```markdown
## Portfolio

### [langgraph-multi-agent](https://github.com/spin-glass/langgraph-multi-agent)
Multi-agent research assistant using LangGraph for task orchestration and Claude Sonnet for analysis.

**Skills**: LangGraph, Multi-agent systems, Claude API

**Demo**: [langgraph-multi-agent.vercel.app](https://langgraph-multi-agent.vercel.app)
```

---

### 3. RESTRUCTURE

**Purpose**: Reorganize content for better flow or emphasis

**Strategy**:
1. Parse suggestion to identify source and target structure
2. Extract content blocks
3. Reorder according to new structure
4. Update heading levels if needed
5. Preserve all content (no deletion)

**Example**:

```python
# Issue
Issue(
    description="Move 'Key Skills' to top for better first impression",
    action_type=ActionType.RESTRUCTURE,
    location="Skills section",
    severity=Severity.MEDIUM
)

# Revision
# Move "## Skills" section from position 4 to position 2 (after Summary)
```

---

### 4. EMPHASIZE

**Purpose**: Make existing content more prominent

**Strategy**:
1. Add markdown emphasis: **bold**, *italic*, or `code`
2. Promote to higher heading level (### → ##)
3. Add visual separators (---, ***)
4. Move to more prominent position within section

**Example**:

```python
# Issue
Issue(
    description="LangGraph experience should be more prominent",
    action_type=ActionType.EMPHASIZE,
    location="Skills → AI/ML",
    severity=Severity.HIGH
)

# Revision
# Before: "- LangGraph"
# After:  "- **LangGraph** (multi-agent orchestration)"
```

---

### 5. QUANTIFY

**Purpose**: Add metrics and numbers to achievements

**Strategy**:
1. Use LLM to suggest realistic metrics based on context
2. Insert numbers inline: "Improved X by Y%", "Reduced Z from A to B"
3. Preserve original content, only augment with numbers
4. If specific numbers cannot be inferred, suggest placeholders

**Example**:

```python
# Issue
Issue(
    description="RAG evaluation results lack quantification",
    action_type=ActionType.QUANTIFY,
    location="Experience → Acme Corp → RAG project",
    severity=Severity.MEDIUM
)

# Revision
# Before: "Improved RAG retrieval accuracy"
# After:  "Improved RAG retrieval accuracy from 72% to 89% (+17pp)"
```

---

### 6. REMOVE

**Purpose**: Delete unnecessary or redundant content

**Strategy**:
1. Identify content block to remove via location
2. Verify removal doesn't break document structure
3. Clean up orphaned headings or list items
4. Log deleted content for audit trail

**Note**: Use sparingly - prefer RESTRUCTURE over deletion.

---

## LLM-Assisted Revision

For action types requiring content generation (ADD_CONTENT, QUANTIFY), the service uses a dedicated LLM call:

```python
async def _generate_content(
    self,
    action_type: ActionType,
    suggestion: str,
    context: str
) -> str:
    """
    Generate new content using LLM based on suggestion and context.

    Args:
        action_type: Type of revision
        suggestion: Agent's improvement suggestion
        context: Surrounding content for style matching

    Returns:
        Generated content matching existing style
    """
    prompt = f"""You are editing a professional resume.

Task: {action_type.value}
Suggestion: {suggestion}
Context (existing content): {context}

Generate new content that:
1. Implements the suggestion
2. Matches the tone and style of existing content
3. Is concise and professional
4. Uses appropriate markdown formatting

Output only the new content to add, without explanations.
"""

    response = await self._call_llm(prompt)
    return response.strip()
```

---

## YAML Frontmatter Preservation

**Critical Requirement** (FR-009): YAML frontmatter must be preserved exactly.

```python
def _preserve_frontmatter(self, original: str, revised_body: str) -> str:
    """
    Recombine YAML frontmatter from original with revised body.

    Args:
        original: Original QMD content with frontmatter
        revised_body: Revised markdown body (no frontmatter)

    Returns:
        Complete QMD file with preserved frontmatter
    """
    # Parse original frontmatter
    matter = frontmatter.loads(original)

    # Update last-modified timestamp
    matter.metadata['last_modified'] = datetime.now().isoformat()

    # Recombine
    return frontmatter.dumps(frontmatter.Post(revised_body, **matter.metadata))
```

**What is preserved**:
- All YAML keys and values
- Comments within YAML block
- Whitespace and indentation
- YAML formatting style

**What is updated**:
- `last_modified` timestamp (automatically)
- No other fields are touched

---

## Revision Conflict Resolution

When multiple agents suggest conflicting changes to the same location:

### Strategy 1: Priority by Severity

```python
def _resolve_conflicts(self, issues: list[Issue]) -> list[Issue]:
    """
    Resolve conflicts by prioritizing higher severity issues.
    """
    # Group by location
    by_location = defaultdict(list)
    for issue in issues:
        by_location[issue.location].append(issue)

    # For each location, keep only highest severity
    resolved = []
    for location, group in by_location.items():
        highest = max(group, key=lambda x: x.severity)
        resolved.append(highest)

    return resolved
```

### Strategy 2: Agent Weight Priority

If severities are equal, use agent weights (recruiter > copywriter > technical_writer).

### Strategy 3: Manual Review

If conflicts are complex, flag for user review in verbose mode.

---

## Revision Result

```python
from dataclasses import dataclass

@dataclass
class RevisionResult:
    """Result of applying revisions to resume."""

    success: bool
    revised_content: str | None
    applied_changes: list[str]  # Human-readable change descriptions
    failed_changes: list[tuple[Issue, str]]  # (Issue, error_message)
    diff: str  # Unified diff for review

    @property
    def change_count(self) -> int:
        return len(self.applied_changes)
```

---

## Error Handling

### YAMLPreservationError

Raised if YAML frontmatter would be corrupted by revision:

```python
class YAMLPreservationError(Exception):
    """Raised when YAML frontmatter cannot be preserved."""

    def __init__(self, original: str, attempted: str):
        self.original = original
        self.attempted = attempted
        super().__init__(
            "YAML frontmatter would be corrupted. "
            "Revision aborted to preserve data integrity."
        )
```

**Mitigation**: Always validate YAML after revision before saving.

---

### RevisionError

Raised if a specific revision cannot be applied:

```python
class RevisionError(Exception):
    """Raised when a revision fails to apply."""

    def __init__(self, issue: Issue, reason: str):
        self.issue = issue
        self.reason = reason
        super().__init__(f"Failed to apply revision: {reason}")
```

**Handling**: Log failed revision, continue with remaining revisions, report in `RevisionResult.failed_changes`.

---

## Dry-Run Mode

When `dry_run=True`:

1. All revision logic executes normally
2. Changes are accumulated in `RevisionResult`
3. Diff is generated for preview
4. **File is never written**
5. Return `revised_content` for display only

```python
async def apply_revisions(
    self,
    resume: Resume,
    feedback_list: list[Feedback],
    dry_run: bool = False
) -> RevisionResult:
    # ... apply all revisions to in-memory content ...

    result = RevisionResult(
        success=True,
        revised_content=new_content,
        applied_changes=changes,
        failed_changes=[],
        diff=unified_diff(resume.content, new_content)
    )

    if not dry_run:
        # Only write file if not dry-run
        resume.save(new_content)

    return result
```

---

## Integration with Workflow

### LangGraph Node

The revision service is called from a LangGraph node:

```python
async def revision_node(state: ReviewState) -> ReviewState:
    """
    Apply revisions based on current feedback.
    """
    service = RevisionService()

    result = await service.apply_revisions(
        resume=state["resume"],
        feedback_list=state["current_feedback"],
        dry_run=state.get("dry_run", False)
    )

    # Update state
    state["revised_content"] = result.revised_content
    state["applied_revisions"].extend(result.applied_changes)
    state["revision_success"] = result.success

    return state
```

### Workflow Position

```
[Evaluation Agents] → [Score Integration] → [Revision Service] → [Threshold Check]
                                                   ↓
                                            (if threshold not met)
                                                   ↓
                                         [Evaluation Agents] (next iteration)
```

---

## Testing Strategy

### Unit Tests

```python
@pytest.mark.asyncio
async def test_add_content_revision():
    service = RevisionService()

    issue = Issue(
        description="Add LLM project summary",
        action_type=ActionType.ADD_CONTENT,
        location="Experience → Acme Corp",
        severity=Severity.HIGH
    )

    result = await service._apply_single_revision(
        content=load_fixture("sample-resume.md"),
        issue=issue,
        suggestion="Add bullet point about GPT-4 chatbot project"
    )

    assert "GPT-4" in result.revised_content
    assert result.success is True

@pytest.mark.asyncio
async def test_yaml_preservation():
    service = RevisionService()

    original = load_fixture("resume-with-frontmatter.qmd")

    result = await service.apply_revisions(
        resume=Resume.from_file(original),
        feedback_list=[...],
        dry_run=False
    )

    # Parse YAML from both
    original_yaml = frontmatter.loads(original).metadata
    revised_yaml = frontmatter.loads(result.revised_content).metadata

    # All keys except last_modified should be identical
    for key in original_yaml:
        if key != 'last_modified':
            assert original_yaml[key] == revised_yaml[key]
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_revision_cycle():
    """Test complete workflow: feedback → revision → validation"""

    # Setup
    resume = Resume.from_file("fixtures/sample.qmd")
    feedback = [
        # Create mock feedback from multiple agents
    ]

    # Execute
    service = RevisionService()
    result = await service.apply_revisions(resume, feedback)

    # Validate
    assert result.success is True
    assert result.change_count > 0
    assert len(result.failed_changes) == 0

    # Ensure QMD is still valid
    assert validate_qmd_syntax(result.revised_content) is True
```

---

## Performance Considerations

- **LLM Calls**: Minimize by batching content generation where possible
- **Caching**: Cache generated content for identical suggestions across iterations
- **Timeout**: Set 30-second timeout per revision to prevent hangs

---

## Implementation Checklist

- [ ] Implement base `RevisionService` class
- [ ] Add handlers for each `ActionType`
- [ ] Implement YAML frontmatter preservation
- [ ] Add conflict resolution logic
- [ ] Create `RevisionResult` dataclass
- [ ] Implement dry-run mode
- [ ] Add error handling (YAMLPreservationError, RevisionError)
- [ ] Write unit tests for each action type
- [ ] Write integration tests for full workflow
- [ ] Add logging for audit trail
- [ ] Document in source code with examples
