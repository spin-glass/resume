"""Integration tests for job URL fetching (US2)."""

from unittest.mock import MagicMock, AsyncMock, patch

import pytest
import requests
from src.services.job_parser import JobParserService


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = MagicMock()
    return client


@pytest.fixture
def job_parser(mock_llm_client):
    """Job parser instance."""
    return JobParserService(llm_client=mock_llm_client)


@pytest.mark.integration
def test_fetch_html_success(job_parser):
    """Test successful HTML fetching."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Job Content</body></html>"
        mock_get.return_value = mock_response
        
        html = job_parser._fetch_html("https://example.com/job")
        assert html == "<html><body>Job Content</body></html>"
        mock_get.assert_called_once()
        # Verify user agent header
        call_kwargs = mock_get.call_args[1]
        assert "User-Agent" in call_kwargs["headers"]


@pytest.mark.integration
def test_fetch_html_timeout(job_parser):
    """Test timeout handling."""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout
        
        with pytest.raises(ValueError, match="timed out"):
            job_parser._fetch_html("https://example.com/job")


@pytest.mark.integration
def test_fetch_html_404(job_parser):
    """Test 404 handling."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response
        
        with pytest.raises(ValueError, match="not found"):
            job_parser._fetch_html("https://example.com/job")


@pytest.mark.integration
def test_extract_text_linkedin(job_parser):
    """Test extraction from LinkedIn HTML."""
    html = """
    <html>
        <body>
            <div class="description__text">
                This is a LinkedIn job description that needs to be long enough to pass validation.
                It should contain at least 50 characters of text to be considered valid.
                We are looking for a software engineer to join our team.
            </div>
            <footer>Apply now</footer>
        </body>
    </html>
    """
    text = job_parser._extract_text_from_html(html, "https://linkedin.com/jobs/view/123")
    assert "This is a LinkedIn job description" in text
    assert "Apply now" not in text  # Accessing boilerplate logic


@pytest.mark.integration
def test_extract_text_indeed(job_parser):
    """Test extraction from Indeed HTML."""
    html = """
    <html>
        <body>
            <div id="jobDescriptionText">
                This is an Indeed job description that needs to be long enough to pass validation.
                It should contain at least 50 characters of text to be considered valid.
                We are looking for an python developer for this position.
            </div>
            <div>Share this job</div>
        </body>
    </html>
    """
    text = job_parser._extract_text_from_html(html, "https://indeed.com/viewjob?jk=123")
    assert "This is an Indeed job description" in text
    assert "Share this job" not in text


@pytest.mark.integration
def test_extract_text_fallback(job_parser):
    """Test fallback extraction for unknown sites."""
    html = """
    <html>
        <body>
            <h1>Job Title</h1>
            <p>This is a generic job description that needs to be long enough to pass validation.</p>
            <ul>
                <li>Requirement 1: Must be able to write python code</li>
                <li>Requirement 2: Must be able to debug complex systems</li>
                <li>Requirement 3: Must be able to write unit tests</li>
            </ul>
        </body>
    </html>
    """
    text = job_parser._extract_text_from_html(html, "https://unknown-site.com/job")
    assert "This is a generic job description" in text
    assert "Requirement 1" in text
    assert "Requirement 2" in text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_parse_url_integration(job_parser):
    """Test full URL parsing flow (mocked network and LLM)."""
    html_content = "<html><body><p>Some job description that is definitely longer than fifty characters so it passes validation logic.</p></body></html>"
    
    # Mock return for _extract_structured_data (which calls LLM)
    mock_job_posting = MagicMock()
    mock_job_posting.title = "Test Job"
    
    with patch.object(job_parser, "_fetch_html", return_value=html_content) as mock_fetch, \
         patch.object(job_parser, "_extract_structured_data", new_callable=AsyncMock) as mock_extract:
        
        mock_extract.return_value = mock_job_posting
        
        result = await job_parser.parse_url("https://example.com/job")
        
        assert result == mock_job_posting
        mock_fetch.assert_called_once_with("https://example.com/job")
        mock_extract.assert_called_once()
        # Verify raw text passed to extract was non-empty
        call_args = mock_extract.call_args[1]
        assert "raw_text" in call_args
