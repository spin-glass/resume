"""Configuration management and logging setup."""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class Config:
    """Configuration manager for the resume review system."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load .env file if it exists
        load_dotenv()

        # API Configuration
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required. "
                "Please create a .env file with your API key."
            )

        # Model Configuration
        self.default_model = os.getenv("RESUME_REVIEW_MODEL", "claude-opus-4-5-20251101")
        self.haiku_model = os.getenv("RESUME_REVIEW_HAIKU_MODEL", "claude-haiku-3-5-20250219")

        # Thresholds and Limits
        self.default_threshold = float(os.getenv("RESUME_REVIEW_THRESHOLD", "8.0"))
        self.default_max_iterations = int(os.getenv("RESUME_REVIEW_MAX_ITERATIONS", "3"))
        self.default_timeout = int(os.getenv("RESUME_REVIEW_TIMEOUT", "300"))  # 5 minutes

        # Logging Configuration
        self.log_level = os.getenv("RESUME_REVIEW_LOG_LEVEL", "INFO").upper()
        self.log_dir = Path.home() / ".resume-review"
        self.log_file = self.log_dir / "error.log"

        # Create log directory if it doesn't exist
        self.log_dir.mkdir(exist_ok=True)

        # Target Role
        self.default_target_role = os.getenv(
            "RESUME_REVIEW_TARGET_ROLE", "LLM/Multi-Agent Engineer"
        )

    def get_api_key(self) -> str:
        """Get Anthropic API key."""
        return self.anthropic_api_key


def setup_logging(verbose: bool = False, log_file: Optional[Path] = None) -> logging.Logger:
    """
    Setup logging infrastructure with console and file handlers.

    Args:
        verbose: Enable verbose (DEBUG) logging
        log_file: Optional custom log file path

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("resume_review")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Remove existing handlers
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler for errors
    if log_file is None:
        log_file = Path.home() / ".resume-review" / "error.log"

    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.ERROR)
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger


def get_config() -> Config:
    """Get or create singleton configuration instance."""
    if not hasattr(get_config, "_instance"):
        get_config._instance = Config()
    return get_config._instance
