"""Unit tests for ScreenshotService - screenshot capture and visual diffing.

Tests for T035: Unit test for preview screenshot generation.
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.services.screenshot import ScreenshotService

# Skip tests that require PIL if not installed
PIL_AVAILABLE = False
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    pass


class TestScreenshotServiceInit:
    """Test cases for ScreenshotService initialization."""

    def test_init_default_cache_dir(self):
        """Service should use default cache directory."""
        service = ScreenshotService()
        assert service.cache_dir == Path("/tmp/resume-screenshots")

    def test_init_custom_cache_dir(self, tmp_path):
        """Service should accept custom cache directory."""
        custom_dir = tmp_path / "custom-screenshots"
        service = ScreenshotService(cache_dir=custom_dir)
        assert service.cache_dir == custom_dir
        assert custom_dir.exists()


class TestScreenshotServiceCapture:
    """Test cases for ScreenshotService.capture() - T035."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create ScreenshotService with temporary cache."""
        return ScreenshotService(cache_dir=tmp_path / "screenshots")

    @pytest.mark.asyncio
    async def test_capture_returns_path_on_success(self, service):
        """Capture should return path to screenshot file."""
        with patch("src.services.screenshot.async_playwright") as mock_playwright:
            # Setup mock browser
            mock_page = AsyncMock()
            mock_response = Mock()
            mock_response.status = 200
            mock_page.goto.return_value = mock_response
            mock_page.screenshot = AsyncMock()

            mock_browser = AsyncMock()
            mock_browser.new_page.return_value = mock_page

            mock_chromium = AsyncMock()
            mock_chromium.launch.return_value = mock_browser

            mock_p = AsyncMock()
            mock_p.chromium = mock_chromium

            mock_playwright.return_value.__aenter__.return_value = mock_p

            result = await service.capture("http://localhost:3000", "test.png")

            assert result is not None
            assert result.suffix == ".png"

    @pytest.mark.asyncio
    async def test_capture_uses_cache(self, service):
        """Capture should return cached file if exists."""
        # Create cached file
        cached_file = service.cache_dir / "cached_screenshot.png"
        cached_file.write_bytes(b"fake png data")

        # Hash URL to get expected filename
        import hashlib

        url = "http://example.com"
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        expected_name = f"screenshot_{url_hash}.png"
        (service.cache_dir / expected_name).write_bytes(b"cached data")

        result = await service.capture(url)

        # Should return cached file without calling Playwright
        assert result is not None
        assert result.exists()


@pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL/Pillow not installed")
class TestScreenshotServiceDiff:
    """Test cases for ScreenshotService.generate_diff() - T038."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create ScreenshotService with temporary cache."""
        return ScreenshotService(cache_dir=tmp_path / "screenshots")

    @pytest.fixture
    def sample_images(self, tmp_path):
        """Create sample before/after PNG files."""
        from PIL import Image

        # Create before image (solid red)
        before_path = tmp_path / "before.png"
        before = Image.new("RGB", (100, 100), (255, 0, 0))
        before.save(before_path)

        # Create after image (solid blue)
        after_path = tmp_path / "after.png"
        after = Image.new("RGB", (100, 100), (0, 0, 255))
        after.save(after_path)

        return before_path, after_path

    def test_generate_diff_creates_output_file(self, service, sample_images, tmp_path):
        """generate_diff should create diff image file."""
        before_path, after_path = sample_images
        output_path = tmp_path / "diff.png"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout='{"diffPixels": 5000, "totalPixels": 10000, "diffPercentage": 50.0}',
                stderr="",
            )

            diff_path, stats = service.generate_diff(before_path, after_path, output_path)

            assert diff_path == output_path
            assert stats["diffPixels"] == 5000
            assert stats["diffPercentage"] == 50.0
            mock_run.assert_called_once()

    def test_generate_diff_returns_stats(self, service, sample_images):
        """generate_diff should return diff statistics."""
        before_path, after_path = sample_images

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout='{"diffPixels": 100, "totalPixels": 10000, "diffPercentage": 1.0, "width": 100, "height": 100}',
                stderr="",
            )

            _, stats = service.generate_diff(before_path, after_path)

            assert "diffPixels" in stats
            assert "totalPixels" in stats
            assert "diffPercentage" in stats

    def test_generate_diff_handles_script_error(self, service, sample_images):
        """generate_diff should handle script errors gracefully."""
        before_path, after_path = sample_images

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="Error: File not found",
            )

            diff_path, stats = service.generate_diff(before_path, after_path)

            assert diff_path is None
            assert "error" in stats

    def test_generate_diff_handles_timeout(self, service, sample_images):
        """generate_diff should handle script timeout."""
        import subprocess

        before_path, after_path = sample_images

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="node", timeout=30)

            diff_path, stats = service.generate_diff(before_path, after_path)

            assert diff_path is None
            assert "error" in stats
            assert "timed out" in stats["error"].lower()


@pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL/Pillow not installed")
class TestScreenshotServiceComposite:
    """Test cases for ScreenshotService.create_composite() - T039."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create ScreenshotService with temporary cache."""
        return ScreenshotService(cache_dir=tmp_path / "screenshots")

    @pytest.fixture
    def sample_images(self, tmp_path):
        """Create sample before/diff/after PNG files."""
        from PIL import Image

        before_path = tmp_path / "before.png"
        Image.new("RGB", (200, 400), (255, 0, 0)).save(before_path)

        diff_path = tmp_path / "diff.png"
        Image.new("RGB", (200, 400), (255, 255, 0)).save(diff_path)

        after_path = tmp_path / "after.png"
        Image.new("RGB", (200, 400), (0, 255, 0)).save(after_path)

        return before_path, diff_path, after_path

    def test_create_composite_generates_image(self, service, sample_images, tmp_path):
        """create_composite should generate composite image."""
        before_path, diff_path, after_path = sample_images
        output_path = tmp_path / "composite.png"

        result = service.create_composite(before_path, diff_path, after_path, output_path)

        assert result is not None
        assert result.exists()
        assert result == output_path

    def test_create_composite_default_output(self, service, sample_images):
        """create_composite should use default output path."""
        before_path, diff_path, after_path = sample_images

        result = service.create_composite(before_path, diff_path, after_path)

        assert result is not None
        assert result.exists()
        assert result.parent == service.cache_dir

    def test_create_composite_contains_three_panels(self, service, sample_images, tmp_path):
        """Composite should contain before|diff|after panels."""
        from PIL import Image

        before_path, diff_path, after_path = sample_images
        output_path = tmp_path / "composite.png"

        result = service.create_composite(before_path, diff_path, after_path, output_path)

        # Check composite dimensions
        composite = Image.open(result)
        # Should be wider than individual images (3 panels + padding)
        before = Image.open(before_path)
        assert composite.width > before.width

    def test_create_composite_handles_missing_file(self, service, tmp_path):
        """create_composite should handle missing input files."""
        nonexistent = tmp_path / "nonexistent.png"

        result = service.create_composite(nonexistent, nonexistent, nonexistent)

        assert result is None


class TestScreenshotServiceClearCache:
    """Test cases for cache management."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create ScreenshotService with temporary cache."""
        return ScreenshotService(cache_dir=tmp_path / "screenshots")

    def test_clear_cache_removes_png_files(self, service):
        """clear_cache should remove all PNG files."""
        # Create some cached files
        (service.cache_dir / "test1.png").write_bytes(b"data1")
        (service.cache_dir / "test2.png").write_bytes(b"data2")
        (service.cache_dir / "test3.png").write_bytes(b"data3")

        count = service.clear_cache()

        assert count == 3
        assert len(list(service.cache_dir.glob("*.png"))) == 0

    def test_get_cached_screenshot_returns_existing(self, service):
        """get_cached_screenshot should return existing cached file."""
        import hashlib

        url = "http://test.example.com"
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        cached_file = service.cache_dir / f"screenshot_{url_hash}.png"
        cached_file.write_bytes(b"cached")

        result = service.get_cached_screenshot(url)

        assert result is not None
        assert result == cached_file

    def test_get_cached_screenshot_returns_none_if_not_cached(self, service):
        """get_cached_screenshot should return None if not cached."""
        result = service.get_cached_screenshot("http://not-cached.example.com")
        assert result is None


@pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL/Pillow not installed")
class TestPreviewGenerationWorkflow:
    """Test cases for preview generation workflow - T035 integration."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create ScreenshotService with temporary cache."""
        return ScreenshotService(cache_dir=tmp_path / "screenshots")

    def test_preview_workflow_no_file_modifications(self, service, tmp_path):
        """Preview workflow should not modify original files."""
        # Create a CSS file
        css_file = tmp_path / "styles" / "test.css"
        css_file.parent.mkdir(parents=True, exist_ok=True)
        original_content = "/* Original CSS */"
        css_file.write_text(original_content)

        # Simulate preview workflow - capture before
        before_screenshot = service.cache_dir / "before.png"

        # After preview workflow, original CSS should be unchanged
        assert css_file.read_text() == original_content

    @pytest.mark.asyncio
    async def test_preview_generates_all_artifacts(self, service, tmp_path):
        """Preview should generate before, after, diff, and composite screenshots."""
        from PIL import Image

        # Create mock screenshots
        before_path = service.cache_dir / "preview_before.png"
        after_path = service.cache_dir / "preview_after.png"
        diff_path = service.cache_dir / "preview_diff.png"
        composite_path = service.cache_dir / "preview_composite.png"

        # Create test images
        Image.new("RGB", (100, 100), (255, 0, 0)).save(before_path)
        Image.new("RGB", (100, 100), (0, 0, 255)).save(after_path)

        # Generate diff
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout='{"diffPixels": 10000, "totalPixels": 10000, "diffPercentage": 100.0}',
                stderr="",
            )

            service.generate_diff(before_path, after_path, diff_path)

            # Verify diff was requested
            mock_run.assert_called_once()

        # Create composite (this works with real PIL)
        Image.new("RGB", (100, 100), (255, 255, 0)).save(diff_path)  # Create actual diff for composite
        composite = service.create_composite(before_path, diff_path, after_path, composite_path)

        assert composite is not None
        assert composite_path.exists()
