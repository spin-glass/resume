# Feature Specification: StateGraph Agent Node Separation

**Feature Branch**: `011-stategraph-node-separation`
**Created**: 2026-01-09
**Status**: Draft
**Input**: User description: "Separate LangGraph supervisor node into individual agent nodes for better visibility, debugging, and monitoring"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-time Agent Monitoring (Priority: P1)

As a developer running resume reviews, I want to see which agent (Recruiter, Technical Writer, Copywriter) is currently executing and how long each takes, so I can identify performance bottlenecks and debug failures quickly.

**Why this priority**: Core value proposition - enables developers to understand the workflow execution in real-time. Without this, the system remains a black box, making debugging and optimization impossible.

**Independent Test**: Can be fully tested by running a resume review with verbose logging enabled and verifying that each agent's execution is logged separately with timing information. Delivers immediate value by exposing previously hidden execution details.

**Acceptance Scenarios**:

1. **Given** a resume review is initiated with verbose mode, **When** the workflow executes, **Then** logs show "Starting recruiter node", "Starting tech_writer node", "Starting copywriter node" with timestamps
2. **Given** the recruiter agent takes 15 seconds to complete, **When** viewing the logs, **Then** "Recruiter node completed in 15.2s" is displayed
3. **Given** the tech_writer agent encounters an error, **When** viewing the logs, **Then** the error message clearly indicates "Error in tech_writer node" with the specific agent name
4. **Given** three agents run in parallel, **When** viewing execution timeline, **Then** overlapping execution periods are visible for all three agents

---

### User Story 2 - LangSmith Trace Analysis (Priority: P2)

As a developer analyzing review quality, I want each agent (Recruiter, Technical Writer, Copywriter) to appear as a separate node in LangSmith traces, so I can analyze per-agent performance, token usage, and error rates independently.

**Why this priority**: Enables data-driven optimization of agent prompts and model selection. Critical for cost optimization and quality improvements, but the feature works without LangSmith integration.

**Independent Test**: Can be tested by running a review with LangSmith tracing enabled and verifying that three separate nodes (recruiter, tech_writer, copywriter) appear in the trace with individual metrics. Delivers value by enabling per-agent cost and performance analysis.

**Acceptance Scenarios**:

1. **Given** LangSmith tracing is enabled, **When** a review completes, **Then** the trace shows three separate nodes: "recruiter", "tech_writer", "copywriter"
2. **Given** a review trace in LangSmith, **When** examining the recruiter node, **Then** token counts and execution time are shown separately from other agents
3. **Given** the copywriter agent fails, **When** viewing the LangSmith trace, **Then** the error is attributed specifically to the "copywriter" node, not to a generic "supervisor" node
4. **Given** multiple review sessions, **When** analyzing trends, **Then** per-agent average execution times can be calculated across sessions

---

### User Story 3 - Workflow Visualization (Priority: P3)

As a developer understanding the system architecture, I want to see a visual graph showing agents running in parallel (recruiter, tech_writer, copywriter → aggregator), so I can understand workflow structure without reading code.

**Why this priority**: Improves onboarding and architectural understanding. Nice-to-have for documentation and communication, but not essential for core functionality.

**Independent Test**: Can be tested by generating a workflow graph visualization (using LangGraph's built-in graph export) and verifying that three parallel edges from router to the three agents are visible. Delivers value by making the architecture self-documenting.

**Acceptance Scenarios**:

1. **Given** the workflow graph is generated, **When** viewing the visualization, **Then** three parallel arrows are shown from "router" node to "recruiter", "tech_writer", and "copywriter" nodes
2. **Given** the workflow graph, **When** tracing from agents to aggregator, **Then** three separate edges converge at the "aggregator" node
3. **Given** a developer new to the codebase, **When** viewing the graph, **Then** the fan-out/fan-in pattern is immediately visible without reading Python code
4. **Given** design agents are also separated, **When** viewing the full graph, **Then** "ux_designer" and "visual_designer" nodes are also visible as separate entities

---

### User Story 4 - Agent-Specific Retry Logic (Priority: P4)

As a developer handling transient failures, I want the ability to retry only the failed agent (e.g., just recruiter) without re-running successful agents, so I can reduce cost and execution time when recovering from temporary errors.

**Why this priority**: Future enhancement for resilience. The current implementation works correctly without per-agent retry, making this a lower priority optimization.

**Independent Test**: Can be tested by simulating a recruiter agent failure, triggering a retry, and verifying that only the recruiter node re-executes while tech_writer and copywriter results are preserved. Delivers value by improving cost-efficiency during error recovery.

**Acceptance Scenarios**:

1. **Given** recruiter agent fails with a transient API error, **When** retry is triggered, **Then** only the recruiter node re-executes
2. **Given** tech_writer and copywriter completed successfully, **When** recruiter retry executes, **Then** their previous results are reused from state
3. **Given** a failed agent retry succeeds, **When** workflow continues, **Then** aggregator receives the retried result combined with cached successful results
4. **Given** a retry limit of 3 is configured, **When** an agent fails 3 times, **Then** the workflow fails and reports which specific agent exhausted retries

---

### Edge Cases

- What happens when one agent completes in 2 seconds but another takes 60 seconds? (fan-in node waits for all agents)
- How does the system handle partial state when agents are separated? (each agent writes to dedicated state fields)
- What if LangGraph's parallel execution limit is reached? (queue agents or fail with clear error message)
- How are agent results collected if they write to the same state key? (use distinct keys: `recruiter_feedback`, `tech_writer_feedback`, `copywriter_feedback`)
- What happens if the aggregator node starts before all agents complete? (LangGraph's fan-in semantics prevent this - aggregator only runs after all incoming edges complete)
- How does error handling work when agents are separate nodes? (errors are attributed to specific node names, enabling targeted debugging)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST execute recruiter, tech_writer, and copywriter agents as separate LangGraph nodes (named "recruiter", "tech_writer", "copywriter") instead of within a single "supervisor" node
- **FR-002**: System MUST create a "router" node that fans out to the three agent nodes via parallel edges
- **FR-003**: System MUST create an "aggregator" node that collects results from the three agents via fan-in edges
- **FR-004**: System MUST store each agent's feedback in a dedicated state field (`recruiter_feedback`, `tech_writer_feedback`, `copywriter_feedback`)
- **FR-005**: Aggregator node MUST combine the three separate feedback objects into the existing `current_feedback` list for backward compatibility
- **FR-006**: System MUST maintain parallel execution behavior - all three agents run concurrently, not sequentially
- **FR-007**: System MUST preserve all existing conditional routing logic (aggregator → revisor or portfolio based on score threshold)
- **FR-008**: System MUST maintain backward compatibility - CLI interface, State schema extensions, and ReviewSession output format remain unchanged
- **FR-009**: System MUST log each agent node's start, completion, and duration as separate log entries
- **FR-010**: System MUST expose individual agent nodes to LangSmith tracing when tracing is enabled
- **FR-011**: Optional design agents (ux_designer, visual_designer) MAY be separated using the same pattern in future enhancements
- **FR-012**: System MUST handle fan-in coordination - aggregator node only executes after all three agent nodes complete
- **FR-013**: System MUST preserve error attribution - failures in specific agents are traceable to the correct node name

### Key Entities *(include if feature involves data)*

- **ReviewState**: Workflow state object extended with new fields `recruiter_feedback`, `tech_writer_feedback`, `copywriter_feedback` (each of type `Optional[Feedback]`)
- **Router Node**: Stateless fan-out node that triggers parallel execution of three agent nodes
- **Agent Nodes**: Three independent nodes (recruiter, tech_writer, copywriter) that each execute one agent and write to dedicated state fields
- **Aggregator Node**: Fan-in node that waits for all agent nodes to complete, then merges their feedback into `current_feedback` list and calculates integrated score

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can identify which specific agent (recruiter, technical writer, or copywriter) is executing at any given time by viewing real-time logs
- **SC-002**: Per-agent execution time is measurable and logged separately for each of the three agents
- **SC-003**: LangSmith traces (when enabled) display three separate nodes for recruiter, tech_writer, and copywriter with individual metrics
- **SC-004**: Workflow visualization (graph export) shows a clear fan-out pattern from router to three agents and fan-in to aggregator
- **SC-005**: Resume review output (scores, feedback, session data) remains identical to the previous supervisor-based implementation for the same input
- **SC-006**: All existing tests pass without modification (except tests that explicitly check node names)
- **SC-007**: Error messages indicate the specific agent node where a failure occurred (e.g., "Error in tech_writer node" instead of "Error in supervisor node")
- **SC-008**: Total workflow execution time remains within 5% of the previous implementation (parallel execution is preserved)

## Assumptions *(optional)*

- LangGraph's fan-out semantics automatically execute parallel edges concurrently (no explicit thread pool management required)
- LangGraph's fan-in semantics ensure aggregator waits for all incoming edges to complete before executing
- Existing agent classes (RecruiterAgent, TechnicalWriterAgent, CopywriterAgent) do not need modification - only node function wrappers change
- State field names can be extended without breaking existing code (TypedDict with `total=False` allows optional fields)
- LangSmith tracing integration works automatically with new node names (no additional configuration required)

## Out of Scope *(optional)*

- Changing agent evaluation logic or prompts (content remains the same)
- Implementing per-agent retry policies (future enhancement in Story 4)
- Separating design agents (ux_designer, visual_designer) - covered in Phase 4 of future-specs.md but not in this feature
- Modifying CLI interface or adding new command-line options
- Changing the scoring algorithm or weights
- Implementing dynamic agent selection (all three agents always run)
- Adding new agent types beyond the existing three
- Implementing agent result caching across review sessions
- Adding agent health checks or circuit breaker patterns

## Dependencies *(optional)*

- LangGraph 1.0.0+ must be installed (already a project dependency)
- Existing ReviewState TypedDict schema must support adding optional fields
- Existing workflow tests must be updated to reflect new node names
- Future validation retry loop (009-quarto-retry-loop) should work with the new node structure without modification

## Open Questions *(optional)*

None - the feature is well-defined in docs/future-specs.md with a complete implementation plan.
