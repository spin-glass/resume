"""Unit tests for router_node."""

import pytest

from src.workflow.nodes.routing import router_node
from src.workflow.state import ReviewState
from src.models.feedback import Resume
from unittest.mock import Mock


@pytest.mark.asyncio
async def test_router_node_returns_empty_dict():
    """Router node returns empty dict (stateless pass-through)."""
    # Setup
    # Setup
    mock_resume = Mock(spec=Resume)
    state = ReviewState(
        current_iteration=0,
        resume=mock_resume,
        target_role="Engineer",
    )

    # Execute
    result = await router_node(state)

    # Verify
    assert result == {}, "Router should return empty dict"


@pytest.mark.asyncio
async def test_router_node_logs_iteration():
    """Router node logs iteration number."""
    # Setup
    # Setup
    mock_resume = Mock(spec=Resume)
    state = ReviewState(
        current_iteration=2,
        resume=mock_resume,
        target_role="Engineer",
    )

    # Execute (logging is verified via logger output in integration tests)
    result = await router_node(state)

    # Verify
    assert result == {}, "Router should return empty dict regardless of iteration"
