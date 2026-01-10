"""Integration tests for screenshot capture."""

import pytest
from pathlib import Path

from src.services.screenshot import ScreenshotService


@pytest.mark.integration
@pytest.mark.asyncio
async def test_screenshot_capture():
    """
    Test T042: Verify Playwright captures image from URL.
    """
    service = ScreenshotService()

    # Use a reliable test URL
    url = "https://example.com"

    # Capture screenshot
    screenshot_path = await service.capture(url)

    # Verify screenshot was created
    assert screenshot_path is not None
    assert screenshot_path.exists()
    assert screenshot_path.suffix == ".png"

    # Verify file has content
    assert screenshot_path.stat().st_size > 0

    # Cleanup
    screenshot_path.unlink()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_screenshot_caching():
    """
    Test that screenshots are cached.
    """
    service = ScreenshotService()
    url = "https://example.com"

    # First capture
    path1 = await service.capture(url)
    assert path1 is not None
    assert path1.exists()

    # Second capture should use cache (same path)
    path2 = await service.capture(url)
    assert path2 == path1

    # Cleanup
    if path1 and path1.exists():
        path1.unlink()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_screenshot_invalid_url():
    """
    Test handling of invalid URL.
    """
    service = ScreenshotService()

    # Try to capture from invalid URL
    screenshot_path = await service.capture("http://this-url-does-not-exist-12345.invalid")

    # Should return None for failed captures
    assert screenshot_path is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_clear_cache():
    """
    Test clearing screenshot cache.
    """
    service = ScreenshotService()
    url = "https://example.com"

    # Capture a screenshot
    path = await service.capture(url)
    assert path is not None
    assert path.exists()

    # Clear cache
    count = service.clear_cache()
    assert count >= 1

    # Verify file was deleted
    assert not path.exists()
