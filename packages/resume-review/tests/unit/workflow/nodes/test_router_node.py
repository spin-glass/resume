"""Unit tests for router_node."""

import pytest

from src.workflow.nodes.routing import router_node


@pytest.mark.asyncio
async def test_router_node_returns_empty_dict():
    """Router node returns empty dict (stateless pass-through)."""
    # Setup
    state = {
        "current_iteration": 0,
        "resume": None,  # Not used by router
        "target_role": "Engineer",
    }

    # Execute
    result = await router_node(state)

    # Verify
    assert result == {}, "Router should return empty dict"


@pytest.mark.asyncio
async def test_router_node_logs_iteration():
    """Router node logs iteration number."""
    # Setup
    state = {
        "current_iteration": 2,
        "resume": None,
        "target_role": "Engineer",
    }

    # Execute (logging is verified via logger output in integration tests)
    result = await router_node(state)

    # Verify
    assert result == {}, "Router should return empty dict regardless of iteration"
