import pytest
from src.reconciliation.graph import build_reconciliation_workflow
from src.reconciliation.state import InterviewSessionState

@pytest.mark.asyncio
async def test_workflow_build():
    workflow = build_reconciliation_workflow()
    assert workflow is not None

@pytest.mark.asyncio
async def test_state_init():
    state = InterviewSessionState(resume_context="Test context", target_year=2020)
    assert state.resume_context == "Test context"
    assert state.target_year == 2020
    assert state.messages == []
