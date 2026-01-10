# Contract: CSSGeneratorAgent

**Module**: `packages/resume-review/src/agents/css_generator.py`
**Purpose**: Generate CSS modifications from design feedback
**Extends**: `BaseAgent`

---

## Interface

### Class Definition

```python
from ..agents.base import BaseAgent
from ..models.design import CSSModification, DesignIssueType
from ..models.feedback import Feedback
from ..services.llm_client import BaseLLMClient

class CSSGeneratorAgent(BaseAgent):
    """Agent that generates CSS modifications from design feedback."""

    def __init__(self, llm_client: BaseLLMClient, agent_name: str = "css_generator"):
        """
        Initialize CSS generator agent.

        Args:
            llm_client: Pre-configured LLM client (injected, provider-agnostic)
            agent_name: Agent identifier (default: "css_generator")
        """
        super().__init__(llm_client, agent_name)

    def get_system_prompt(self, target_role: str) -> str:
        """
        Get CSS generation system prompt.

        Args:
            target_role: Target position (for context, usually not used in CSS generation)

        Returns:
            System prompt for CSS generation
        """
        pass

    async def generate_css(
        self,
        design_feedback: list[Feedback],
        current_css: str = "",
        target_role: str = "LLM/Multi-Agent Engineer"
    ) -> CSSModification:
        """
        Generate CSS modifications from design feedback.

        Args:
            design_feedback: List of feedback from UX and Visual Designer agents
            current_css: Existing CSS content (if any) to build upon
            target_role: Target position (for context)

        Returns:
            CSSModification with generated CSS, changes, and validation status

        Raises:
            ValueError: If design_feedback is empty
            LLMError: If LLM call fails after retries
        """
        pass
```

---

## Inputs

### design_feedback (Required)

**Type**: `list[Feedback]`

**Source**: `ReviewState.design_feedback` (output from design_review node)

**Validation**:
- MUST NOT be empty
- Each feedback MUST have `agent_name` in `["ux_designer", "visual_designer"]`
- Each feedback MUST have at least one issue with non-empty description

**Example**:
```python
[
    Feedback(
        agent_name="visual_designer",
        score=6.5,
        issues=[
            Issue(
                description="Heading font size too small, lacks hierarchy",
                severity=Severity.HIGH,
                location="All headings"
            ),
            Issue(
                description="Spacing between sections cramped",
                severity=Severity.MEDIUM,
                location="Section gaps"
            )
        ]
    ),
    Feedback(
        agent_name="ux_designer",
        score=7.0,
        issues=[
            Issue(
                description="Skills section should be more prominent",
                severity=Severity.HIGH,
                location="Skills section"
            )
        ]
    )
]
```

### current_css (Optional)

**Type**: `str`

**Source**: Read from `styles/resume-custom.css` if exists, otherwise empty string

**Purpose**: Build upon existing CSS rather than replacing entirely

**Example**:
```css
:root {
  --primary-color: #2c3e50;
  --section-gap: 1.5rem;
}

h2 {
  color: var(--primary-color);
  margin-top: var(--section-gap);
}
```

### target_role (Optional)

**Type**: `str`

**Default**: `"LLM/Multi-Agent Engineer"`

**Purpose**: Provide context to LLM (though rarely affects CSS generation)

---

## Outputs

### CSSModification

**Type**: `CSSModification` (Pydantic model)

**Fields**:
- `css_content`: Generated CSS as string
- `target_file`: Output path (default: `styles/resume-custom.css`)
- `changes`: List of human-readable change descriptions
- `issue_types`: List of `DesignIssueType` addressed
- `validation_passed`: Whether CSS passed validation
- `validation_errors`: List of validation errors (empty if passed)

**Guarantees**:
1. `css_content` MUST be valid CSS (verified by cssutils)
2. `css_content` MUST include `@media print` rules for any layout-affecting properties
3. `css_content` MUST use CSS custom properties (--variables) for magic numbers
4. `css_content` MUST include comments explaining each rule
5. `changes` list MUST have at least one entry per addressed issue
6. `validation_passed` MUST be True before CSS can be applied

**Example**:
```python
CSSModification(
    css_content='''
/* Issue: Heading font size too small, lacks hierarchy */
h2 {
  font-size: 1.4rem;        /* Was: 1.2rem */
  font-weight: 600;         /* Was: 500 */
  border-bottom: 2px solid var(--primary-color);
  padding-bottom: 0.5rem;
}

/* Issue: Spacing between sections cramped */
:root {
  --section-gap: 2rem;      /* Was: 1.5rem */
}

.section {
  margin-bottom: var(--section-gap);
}

@media print {
  h2 {
    page-break-after: avoid;
  }
}
''',
    target_file=Path("styles/resume-custom.css"),
    changes=[
        "Increased h2 font size from 1.2rem to 1.4rem",
        "Added bottom border to h2 for hierarchy",
        "Increased section gap from 1.5rem to 2rem"
    ],
    issue_types=[
        DesignIssueType.TYPOGRAPHY,
        DesignIssueType.SPACING,
        DesignIssueType.HIERARCHY
    ],
    validation_passed=True,
    validation_errors=[]
)
```

---

## Behavior

### CSS Generation Logic

1. **Parse Feedback**: Extract design issues from each Feedback object
2. **Classify Issues**: Map issue descriptions to DesignIssueType (spacing/typography/color/hierarchy/layout)
3. **Generate Prompt**: Create structured LLM prompt with:
   - Current CSS (if any)
   - Categorized issues with severity
   - Constraints (minimal changes, CSS variables, print compatibility, BEM naming)
   - Output format (raw CSS with comments)
4. **Call LLM**: Use `self.llm_client.generate()` with CSS generation prompt
5. **Extract CSS**: Parse LLM response to extract CSS code block
6. **Validate**: Run cssutils validation:
   - Check syntax errors
   - Verify no forbidden properties in @media print
   - Confirm custom properties defined in :root
7. **Build Result**: Create CSSModification with validated CSS and metadata

### Error Handling

**Empty Feedback**:
```python
if not design_feedback:
    raise ValueError("design_feedback cannot be empty")
```

**LLM Failure**:
- Retry up to 3 times (inherited from BaseAgent)
- If all retries fail, raise LLMError
- Do NOT return empty CSS (fail loudly)

**Validation Failure**:
- Set `validation_passed = False`
- Populate `validation_errors` with specific issues
- Return CSSModification (don't raise exception)
- Caller decides whether to apply or reject

---

## Prompt Template

**System Prompt** (from `get_system_prompt`):

```python
SYSTEM_PROMPT = """You are an expert CSS designer specializing in professional document styling.

Given design feedback for a resume, generate CSS modifications that address the issues.

CONSTRAINTS:
1. Generate MINIMAL, targeted CSS changes - don't rewrite everything
2. Use CSS custom properties (--var) for values that users might override
3. Prioritize readability and professionalism over creativity
4. Ensure print compatibility - include @media print rules where needed
5. Follow BEM naming convention for any new classes
6. Include comments explaining each rule's purpose

FORBIDDEN in @media print:
- position: fixed/absolute
- transform properties
- break-inside: avoid (use page-break-inside)
- complex animations

OUTPUT FORMAT:
Return ONLY valid CSS (no markdown code blocks, no explanations before/after).
Include comments within CSS to explain changes.

Example output:
/* Issue: Headings lack visual weight (high severity) */
h2 {{
  font-size: 1.4rem;        /* Was: 1.2rem */
  font-weight: 600;         /* Was: 500 */
  border-bottom: 2px solid var(--primary-color);
  padding-bottom: 0.5rem;
}}

@media print {{
  h2 {{
    page-break-after: avoid;
  }}
}}
"""
```

**User Prompt** (generated in `generate_css`):

```python
user_prompt = f"""
Current CSS (may be empty):
```css
{current_css or "/* No existing CSS */"}
```

Design Issues to Address:
{self._format_issues_for_prompt(design_feedback)}

Generate CSS modifications to address these issues.
"""
```

**Issue Formatting Helper**:

```python
def _format_issues_for_prompt(self, design_feedback: list[Feedback]) -> str:
    """Format design issues for LLM prompt."""
    lines = []
    for feedback in design_feedback:
        lines.append(f"\n## {feedback.agent_name.upper()} FEEDBACK (score: {feedback.score}/10)")
        for issue in feedback.issues:
            lines.append(f"- [{issue.severity.value.upper()}] {issue.description}")
            if issue.location:
                lines.append(f"  Location: {issue.location}")
    return '\n'.join(lines)
```

---

## Validation Rules

### Pre-Generation Validation

```python
# In generate_css() method
if not design_feedback:
    raise ValueError("design_feedback cannot be empty")

if not any(
    feedback.agent_name in ["ux_designer", "visual_designer"]
    for feedback in design_feedback
):
    raise ValueError("design_feedback must include UX or Visual Designer feedback")
```

### Post-Generation Validation

```python
import cssutils

def _validate_css(self, css_content: str) -> tuple[bool, list[str]]:
    """
    Validate generated CSS.

    Returns:
        (passed, errors): validation status and error list
    """
    errors = []

    # Parse CSS
    try:
        sheet = cssutils.parseString(css_content)
    except cssutils.css.CSSException as e:
        return (False, [f"CSS syntax error: {e}"])

    # Check for forbidden print properties
    forbidden_in_print = {
        'position': ['fixed', 'absolute'],
        'transform': ['*'],  # Any transform
    }

    for rule in sheet:
        if isinstance(rule, cssutils.css.CSSMediaRule):
            if 'print' in rule.media.mediaText:
                # Check properties in print rules
                for style_rule in rule.cssRules:
                    if isinstance(style_rule, cssutils.css.CSSStyleRule):
                        for prop in style_rule.style:
                            if prop.name in forbidden_in_print:
                                allowed = forbidden_in_print[prop.name]
                                if '*' in allowed or prop.value in allowed:
                                    errors.append(
                                        f"Forbidden property in @media print: "
                                        f"{prop.name}: {prop.value}"
                                    )

    # Check for custom properties definition
    has_root_vars = False
    for rule in sheet:
        if isinstance(rule, cssutils.css.CSSStyleRule):
            if ':root' in rule.selectorText:
                has_root_vars = True
                break

    # Ensure CSS has some custom properties if it defines them
    css_lower = css_content.lower()
    if '--' in css_lower and not has_root_vars:
        errors.append("CSS uses custom properties (--var) but doesn't define them in :root")

    return (len(errors) == 0, errors)
```

---

## Dependencies

### Internal

- `..agents.base.BaseAgent` - Base agent functionality
- `..models.design.CSSModification` - Output model
- `..models.design.DesignIssueType` - Issue classification
- `..models.feedback.Feedback` - Input model
- `..services.llm_client.BaseLLMClient` - LLM abstraction

### External

- `cssutils` - CSS parsing and validation
- `pydantic` - Data validation
- `typing` - Type hints

---

## Testing

### Unit Tests

**File**: `tests/unit/agents/test_css_generator.py`

**Test Cases**:

1. `test_generate_css_success`:
   - Given valid design feedback
   - When generate_css() called
   - Then returns CSSModification with valid CSS

2. `test_generate_css_empty_feedback`:
   - Given empty design_feedback list
   - When generate_css() called
   - Then raises ValueError

3. `test_generate_css_with_current_css`:
   - Given existing CSS and new feedback
   - When generate_css() called
   - Then generated CSS builds upon existing (doesn't replace)

4. `test_css_validation_failure`:
   - Given LLM generates invalid CSS syntax
   - When generate_css() called
   - Then returns CSSModification with validation_passed=False

5. `test_print_compatibility`:
   - Given LLM generates CSS with forbidden print properties
   - When validation runs
   - Then validation_errors includes print property violations

6. `test_custom_properties_usage`:
   - Given generated CSS uses --variables
   - When validation runs
   - Then ensures :root definition exists

### Integration Tests

**File**: `tests/integration/test_css_generator_workflow.py`

**Test Cases**:

1. `test_end_to_end_css_generation`:
   - Given real design feedback from agents
   - When CSS generator runs
   - Then CSS is valid and addresses all issues

2. `test_css_renders_correctly`:
   - Given generated CSS
   - When applied to resume HTML
   - Then visual rendering improves (manual QA or snapshot testing)

---

## Performance

**Targets**:
- CSS generation: <5 seconds (LLM call + validation)
- Validation: <100ms (cssutils parsing)

**Optimization**:
- Cache LLM responses for identical feedback (optional)
- Parallel validation if multiple CSS variants generated

---

## Example Usage

```python
from packages.resume_review.src.agents.css_generator import CSSGeneratorAgent
from packages.resume_review.src.services.llm_factory import LLMClientFactory
from packages.resume_review.src.config.model_config import AgentName

# Create LLM client (injected)
llm_client = LLMClientFactory.create_client(
    agent_name=AgentName.CSS_GENERATOR,
    anthropic_api_key="sk-...",
)

# Initialize agent
css_agent = CSSGeneratorAgent(llm_client=llm_client)

# Generate CSS from design feedback
design_feedback = [...]  # From UX/Visual agents
css_mod = await css_agent.generate_css(
    design_feedback=design_feedback,
    current_css=Path("styles/resume-custom.css").read_text(),
    target_role="LLM Engineer"
)

# Check validation
if css_mod.validation_passed:
    print(f"Generated CSS: {css_mod.get_summary()}")
    # Apply CSS (handled by CSSService)
else:
    print(f"CSS validation failed: {css_mod.validation_errors}")
```

---

**Contract Version**: 1.0
**Last Updated**: 2026-01-09
