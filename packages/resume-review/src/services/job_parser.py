"""
Job posting parser service.

This module provides services for parsing job descriptions from files and URLs,
extracting structured data using LLM-based semantic extraction.
"""

import json
import logging
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from ..models.job_posting import JobPosting
from ..services.llm_client import BaseLLMClient

logger = logging.getLogger(__name__)


class JobParserService:
    """Service for parsing job descriptions from files and URLs."""

    def __init__(self, llm_client: BaseLLMClient):
        """
        Initialize job parser service.

        Args:
            llm_client: LLM client for semantic extraction
        """
        self.llm_client = llm_client

    async def _extract_structured_data(
        self, raw_text: str, source: str
    ) -> JobPosting:
        """
        Extract structured data from raw job posting text using LLM.

        Args:
            raw_text: Raw job description text
            source: File path or URL source

        Returns:
            JobPosting with extracted structured data

        Raises:
            ValueError: If extraction fails or required fields are missing
        """
        system_prompt = """You are an expert at analyzing job postings.
Extract structured information from the job description.

IMPORTANT:
- Categorize skills into required (must-have) vs preferred (nice-to-have)
- Expand acronyms and normalize terminology (e.g., "K8s" -> "Kubernetes")
- Identify responsibilities vs qualifications clearly
- Extract salary/rate information only if explicitly mentioned
- Return ONLY valid JSON that matches the schema exactly"""

        user_prompt = f"""Analyze this job posting and extract structured data.
Return a JSON object with these exact fields:

{{
  "title": "Job title string (required)",
  "company": "Company name or null",
  "required_skills": ["skill1", "skill2"],
  "preferred_skills": ["skill1", "skill2"],
  "responsibilities": ["resp1", "resp2"],
  "qualifications": ["qual1", "qual2"],
  "salary_range": "Salary string or null",
  "contract_type": "Full-time/Contract/etc or null"
}}

Job Posting:
{raw_text}

Return ONLY the JSON object, no additional text."""

        try:
            logger.info(f"Extracting structured data from job posting: {source}")

            # Call LLM for extraction
            response = await self.llm_client.generate_async(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=4000,
                temperature=0.3,  # Lower temperature for more consistent extraction
            )

            # Parse JSON response
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            parsed_data = json.loads(content)

            # Create JobPosting with extracted data
            job_posting = JobPosting(
                title=parsed_data.get("title", "Untitled Position"),
                company=parsed_data.get("company"),
                required_skills=parsed_data.get("required_skills", []),
                preferred_skills=parsed_data.get("preferred_skills", []),
                responsibilities=parsed_data.get("responsibilities", []),
                qualifications=parsed_data.get("qualifications", []),
                salary_range=parsed_data.get("salary_range"),
                contract_type=parsed_data.get("contract_type"),
                raw_text=raw_text,
                source=source,
            )

            logger.info(
                f"Successfully extracted job posting: {job_posting.title} "
                f"({job_posting.get_skill_count()['total']} total skills)"
            )
            return job_posting

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response content: {response.content[:500]}")
            raise ValueError(
                f"Failed to parse job posting: LLM returned invalid JSON. "
                f"This may be a temporary issue - please try again."
            ) from e
        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            raise ValueError(
                f"Failed to extract job posting data: {str(e)}"
            ) from e

    async def parse_file(self, file_path: Path) -> JobPosting:
        """
        Parse job posting from a local file.

        Supports .txt and .md formats.

        Args:
            file_path: Path to job posting file

        Returns:
            JobPosting with extracted data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty or parsing fails
        """
        # Validate file exists
        if not file_path.exists():
            raise FileNotFoundError(f"Job posting file not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        # Validate file extension
        if file_path.suffix not in [".txt", ".md"]:
            logger.warning(
                f"Unexpected file extension: {file_path.suffix}. "
                f"Supported: .txt, .md. Attempting to parse anyway."
            )

        # Read file content
        try:
            raw_text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                raw_text = file_path.read_text(encoding="latin-1")
                logger.warning(
                    f"File encoding issue - used latin-1 fallback for {file_path}"
                )
            except Exception as e:
                raise ValueError(
                    f"Failed to read file with supported encodings: {e}"
                ) from e

        # Validate content is not empty
        if not raw_text.strip():
            raise ValueError(f"Job posting file is empty: {file_path}")

        if len(raw_text.strip()) < 50:
            raise ValueError(
                f"Job posting file is too short ({len(raw_text)} chars). "
                f"Expected at least 50 characters."
            )

        logger.info(f"Parsing job posting from file: {file_path}")

        # Extract structured data using LLM
        return await self._extract_structured_data(
            raw_text=raw_text,
            source=str(file_path)
        )

    def _fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from URL.

        Args:
            url: Job posting URL

        Returns:
            HTML content as string

        Raises:
            ValueError: If fetch fails or times out
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        try:
            logger.info(f"Fetching job posting from URL: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text

        except requests.exceptions.Timeout:
            raise ValueError(
                f"Request timed out after 10 seconds. The server may be slow or unreachable. "
                f"Try using --job-posting with a file instead."
            )
        except requests.exceptions.ConnectionError:
            raise ValueError(
                f"Failed to connect to {url}. Check your internet connection or try using --job-posting with a file."
            )
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code == 404:
                raise ValueError(f"Job posting not found (404). The URL may be incorrect or the posting may have been removed.")
            elif status_code == 403:
                raise ValueError(f"Access denied (403). The website may be blocking automated access. Try using --job-posting with a file.")
            elif status_code >= 500:
                raise ValueError(f"Server error ({status_code}). The website may be temporarily unavailable. Try again later or use --job-posting with a file.")
            else:
                raise ValueError(f"HTTP error {status_code}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to fetch URL: {str(e)}")

    def _extract_text_from_html(self, html: str, url: str) -> str:
        """
        Extract job description text from HTML.

        Args:
            html: HTML content
            url: Source URL for site-specific logic

        Returns:
            Extracted job description text

        Raises:
            ValueError: If extraction fails
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Site-specific selectors
            job_text = None

            if "linkedin.com" in url:
                job_desc = soup.select_one(".job-description, .jobs-description, .description__text")
                if job_desc:
                    job_text = job_desc.get_text(separator="\n", strip=True)

            elif "indeed.com" in url:
                job_desc = soup.select_one(".jobsearch-JobComponent-description, #jobDescriptionText")
                if job_desc:
                    job_text = job_desc.get_text(separator="\n", strip=True)

            elif "glassdoor.com" in url:
                job_desc = soup.select_one(".desc, .jobDescriptionContent")
                if job_desc:
                    job_text = job_desc.get_text(separator="\n", strip=True)

            # Fallback: extract all <p> and <li> elements
            if not job_text:
                logger.warning(f"No site-specific selector matched for {url}, using fallback extraction")
                paragraphs = soup.find_all(["p", "li"])
                job_text = "\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

            if not job_text or len(job_text.strip()) < 50:
                raise ValueError("Extracted text is too short or empty. The page may not contain a job description.")

            # Remove common boilerplate
            boilerplate_phrases = [
                "Apply now",
                "Share this job",
                "Cookie policy",
                "Privacy policy",
                "Terms of service",
                "Follow us on",
                "Sign up for job alerts",
            ]

            lines = job_text.split("\n")
            filtered_lines = [
                line for line in lines
                if not any(phrase.lower() in line.lower() for phrase in boilerplate_phrases)
            ]

            cleaned_text = "\n".join(filtered_lines).strip()

            logger.info(f"Extracted {len(cleaned_text)} characters from HTML")
            return cleaned_text

        except Exception as e:
            raise ValueError(f"Failed to parse HTML: {str(e)}")

    async def parse_url(self, url: str) -> JobPosting:
        """
        Parse job posting from URL.

        Args:
            url: Job posting URL

        Returns:
            JobPosting with extracted data

        Raises:
            ValueError: If fetch, extraction, or parsing fails
        """
        html = self._fetch_html(url)
        raw_text = self._extract_text_from_html(html, url)

        if len(raw_text.strip()) < 50:
            raise ValueError(
                f"Extracted text is too short ({len(raw_text)} chars). "
                f"The page may not contain a valid job description. "
                f"Try using --job-posting with a file instead."
            )

        return await self._extract_structured_data(
            raw_text=raw_text,
            source=url
        )
