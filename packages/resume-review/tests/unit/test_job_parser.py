"""Unit tests for JobParserService (T079)."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from src.services.job_parser import JobParserService

@pytest.fixture
def mock_llm_client():
    return MagicMock()

@pytest.fixture
def job_parser(mock_llm_client):
    return JobParserService(llm_client=mock_llm_client)

@pytest.mark.asyncio
async def test_parse_file_success(job_parser, tmp_path):
    """Test successful file parsing."""
    # Create temp file
    f = tmp_path / "test_job.md"
    f.write_text("Job content must be at least fifty characters long to pass the validation check in the parser service.", encoding="utf-8")
    
    # Mock extract
    mock_posting = MagicMock()
    mock_posting.title = "Parsed Title"
    mock_posting.source = str(f)
    
    with patch.object(job_parser, "_extract_structured_data", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = mock_posting
        
        result = await job_parser.parse_file(f)
        
        assert result.title == "Parsed Title"
        assert result.source == str(f)
        mock_extract.assert_called_once()
        args, kwargs = mock_extract.call_args
        assert kwargs["raw_text"] == "Job content must be at least fifty characters long to pass the validation check in the parser service."
        assert kwargs["source"] == str(f)

@pytest.mark.asyncio
async def test_parse_file_not_found(job_parser):
    """Test non-existent file parsing."""
    with pytest.raises(FileNotFoundError):
        await job_parser.parse_file(Path("non_existent.md"))

@pytest.mark.asyncio
async def test_parse_file_empty(job_parser, tmp_path):
    """Test empty file parsing."""
    f = tmp_path / "empty.md"
    f.write_text("", encoding="utf-8")
    
    with pytest.raises(ValueError, match="is empty"):
        await job_parser.parse_file(f)

def test_extract_text_from_html_logic(job_parser):
    """Test HTML extraction logic specific handling."""
    # This overlaps with integration test coverage, but we can test specific filtering logic here
    # Test boilerplate removal
    html = """
    <html><body>
    <div class="job-description">
        Real content.
        Apply now!
        Share this job.
    </div>
    </body></html>
    """
    
    # Mock beautiful soup behavior or just duplicate logic testing?
    # Since we tested site selectors heavily in integration, let's focus on boilerplate removal here
    # if we can invoke the private method
    
    # Important: The method removes lines containing boilerplate phrases
    text = job_parser._extract_text_from_html(html, "https://linkedin.com/jobs/view/1")
    
    assert "Real content" in text
    assert "Apply now" not in text
    assert "Share this job" not in text
