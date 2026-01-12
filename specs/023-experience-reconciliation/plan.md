# Implementation Plan: Experience Reconciliation Agent

## Phase 1: Core Agent Implementation (Backend)

### 1. Data Models
- Define `ExperienceReconciliationState` in `packages/agent/src/features/reconciliation/state.py` (or equivalent).
- Define `StarStory` schema in `packages/core`.

### 2. LangGraph Workflow
- **Nodes**:
    - `InterviewNode`: Generates questions based on context.
    - `FactCheckNode`: Validates tech stack timeline.
    - `StarGeneratorNode`: Synthesizes the STAR story.
- **Graph**:
    - `Input` -> `InterviewNode` <-> `UserInteraction`
    - `UserInteraction` -> `FactCheckNode` -> `InterviewNode` (Loop until sufficient)
    - `InterviewNode` -> `StarGeneratorNode` -> `Output`

### 3. Prompts
- Design prompts for "Historical context aware interviewer".
- Design prompts for "Tech stack fact checker".

## Phase 2: Interface Integration

### 1. CLI Command
- Add `resume-review reconcile` (or similar) command to trigger the agent.
- Allow selecting a project from `resume-ja.qmd` as input context.

## Phase 3: Verification

### 1. Unit Tests
- Test each node independently with mocked state.
- Test fact checker with known anachronisms.

### 2. Scenario Testing
- Mock entire conversation flows to verify STAR generation quality.
