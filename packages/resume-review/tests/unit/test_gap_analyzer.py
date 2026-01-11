import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.agents.gap_analyzer import GapAnalyzerAgent
from src.models.gap_analysis import GapAnalysisResult
from src.services.llm_client import BaseLLMClient


@pytest.fixture
def mock_llm_client():
    client = MagicMock(spec=BaseLLMClient)
    client.model = "test-model"  # Required by BaseAgent.__init__
    return client

def test_gap_analysis_parsing(mock_llm_client):
    """Test that GapAnalyzer correctly parses valid JSON response."""
    
    # Mock JSON response
    mock_response_json = {
        "match_score": 8.5,
        "summary": "Good match but missing Rust.",
        "missing_skills": [
            {
                "skill_name": "Rust",
                "urgency": "High",
                "context": "Core backend language",
                "action_items": [
                    {
                        "description": "Build a CLI in Rust",
                        "resource_url": "https://rust-lang.org"
                    }
                ]
            }
        ],
        "strong_points": ["Python", "System Design"],
        "overall_recommendation": "Learn Rust ASAP."
    }
    
    agent = GapAnalyzerAgent(mock_llm_client)
    
    # Test parse_result directly to avoid async complexity in this unit test
    result = agent.parse_result(json.dumps(mock_response_json))
    
    assert isinstance(result, GapAnalysisResult)
    assert result.match_score == 8.5
    assert len(result.missing_skills) == 1
    assert result.missing_skills[0].skill_name == "Rust"
    assert result.missing_skills[0].urgency == "High"
    assert result.strong_points == ["Python", "System Design"]

def test_gap_analysis_parsing_with_markdown(mock_llm_client):
    """Test parsing when LLM wraps JSON in markdown blocks."""
    json_str = json.dumps({
        "match_score": 5.0,
        "summary": "Test",
        "missing_skills": [],
        "strong_points": [],
        "overall_recommendation": "Test"
    })
    
    agent = GapAnalyzerAgent(mock_llm_client)
    
    # Case 1: ```json ... ```
    response1 = f"```json\n{json_str}\n```"
    result1 = agent.parse_result(response1)
    assert result1.match_score == 5.0
    
    # Case 2: ``` ... ```
    response2 = f"```\n{json_str}\n```"
    result2 = agent.parse_result(response2)
    assert result2.match_score == 5.0

@pytest.mark.asyncio
async def test_gap_analysis_execution(mock_llm_client):
    """Test full async execution flow."""
    agent = GapAnalyzerAgent(mock_llm_client)
    
    # Mock LLM response
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "match_score": 9.0,
        "summary": "Excellent",
        "missing_skills": [],
        "strong_points": [],
        "overall_recommendation": "Hire"
    })
    
    # Setup async mock
    mock_llm_client.generate_async = AsyncMock(return_value=mock_response)
    
    result = await agent.analyze_async("Resume Content", "Job Description")
    
    assert result.match_score == 9.0
    mock_llm_client.generate_async.assert_called_once()
