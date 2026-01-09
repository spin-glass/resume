"""Screenshot capture service using Playwright."""

import logging
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright

logger = logging.getLogger("resume_review")


class ScreenshotService:
    """Service for capturing screenshots of resume HTML using headless browser."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize screenshot service.

        Args:
            cache_dir: Directory for caching screenshots (default: /tmp/resume-screenshots/)
        """
        self.cache_dir = cache_dir or Path("/tmp/resume-screenshots")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def capture(
        self, url: str, output_filename: Optional[str] = None, wait_time: int = 2000
    ) -> Optional[Path]:
        """
        Capture screenshot of URL using Playwright.

        Args:
            url: URL to capture
            output_filename: Optional output filename (default: auto-generated from URL)
            wait_time: Milliseconds to wait for page load (default: 2000ms)

        Returns:
            Path to screenshot file, or None if capture failed

        Raises:
            Exception: If Playwright fails to capture screenshot
        """
        if output_filename is None:
            # Generate filename from URL
            import hashlib

            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            output_filename = f"screenshot_{url_hash}.png"

        output_path = self.cache_dir / output_filename

        # Check cache
        if output_path.exists():
            logger.debug(f"Using cached screenshot: {output_path}")
            return output_path

        logger.info(f"Capturing screenshot of {url}")

        try:
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(
                    viewport={"width": 1920, "height": 1080},  # Standard desktop resolution
                )

                # Navigate to URL
                logger.debug(f"Navigating to {url}")
                response = page.goto(url, wait_until="networkidle", timeout=30000)

                if not response or response.status >= 400:
                    logger.error(f"Failed to load {url}: HTTP {response.status if response else 'None'}")
                    browser.close()
                    return None

                # Wait for additional render time
                page.wait_for_timeout(wait_time)

                # Take screenshot
                logger.debug(f"Saving screenshot to {output_path}")
                page.screenshot(path=str(output_path), full_page=True)

                browser.close()

                logger.info(f"Screenshot saved: {output_path}")
                return output_path

        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return None

    def clear_cache(self) -> int:
        """
        Clear all cached screenshots.

        Returns:
            Number of files deleted
        """
        count = 0
        if self.cache_dir.exists():
            for file in self.cache_dir.glob("*.png"):
                file.unlink()
                count += 1
            logger.info(f"Cleared {count} cached screenshots")
        return count

    def get_cached_screenshot(self, url: str) -> Optional[Path]:
        """
        Get cached screenshot for URL if it exists.

        Args:
            url: URL to check

        Returns:
            Path to cached screenshot, or None if not cached
        """
        import hashlib

        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        output_path = self.cache_dir / f"screenshot_{url_hash}.png"

        if output_path.exists():
            return output_path
        return None
