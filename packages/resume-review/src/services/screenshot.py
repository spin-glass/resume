"""Screenshot capture service using Playwright."""

import logging
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright

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

    async def capture(
        self,
        url: str,
        output_filename: Optional[str] = None,
        wait_time: int = 2000,
        full_page: bool = False,
        css: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Capture screenshot of URL using Playwright.

        Args:
            url: URL to capture
            output_filename: Optional output filename (default: auto-generated from URL)
            wait_time: Milliseconds to wait for page load (default: 2000ms)
            full_page: Whether to capture full page
            css: Optional CSS string to inject before capture

        Returns:
            Path to screenshot file, or None if capture failed
        """
        if output_filename is None:
            # Generate filename from URL
            import hashlib

            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            output_filename = f"screenshot_{url_hash}.png"

        output_path = self.cache_dir / output_filename

        # Check cache (Skip cache if injecting CSS)
        if output_path.exists() and css is None:
            logger.debug(f"Using cached screenshot: {output_path}")
            return output_path

        logger.info(f"Capturing screenshot: {url} -> {output_path} (css={'yes' if css else 'no'})")

        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(headless=True)
                # Create context with standard desktop viewport
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    device_scale_factor=1,
                )
                page = await context.new_page()

                # Navigate to URL
                logger.debug(f"Navigating to {url}")
                try:
                    response = await page.goto(url, wait_until="networkidle", timeout=30000)
                except Exception as e:
                    logger.error(f"Page navigation timed out or failed: {e}")
                    await browser.close()
                    return None

                if not response or response.status >= 400:
                    logger.error(f"Failed to load {url}: HTTP {response.status if response else 'None'}")
                    await browser.close()
                    return None

                # Inject CSS if provided
                if css:
                    logger.debug(f"Injecting {len(css)} bytes of custom CSS")
                    try:
                        await page.add_style_tag(content=css)
                        # Wait a bit for styles to apply and layout to shift
                        await page.wait_for_timeout(500)
                    except Exception as e:
                        logger.warning(f"Failed to inject CSS: {e}")

                # Wait for React/Next.js hydration to complete
                # Nextra uses React and may have layout shifts after initial load
                try:
                    # Wait for main content area to be visible
                    await page.wait_for_selector("main, article, .nextra-content", timeout=5000)
                    # Give additional time for any layout animations
                    await page.wait_for_timeout(1000)
                except Exception as e:
                    logger.debug(f"Selector wait timed out (may be fine): {e}")

                # Wait for additional render time
                await page.wait_for_timeout(wait_time)

                # Take screenshot
                logger.debug(f"Saving screenshot ({'full-page' if full_page else 'viewport'}) to {output_path}")
                await page.screenshot(path=str(output_path), full_page=full_page)

                await browser.close()

                if output_path.exists():
                    logger.info(f"Screenshot successfully saved: {output_path} ({output_path.stat().st_size} bytes)")
                    return output_path
                else:
                    logger.error(f"Screenshot file not found after capture: {output_path}")
                    return None

        except Exception as e:
            logger.error(f"Screenshot capture failed for {url}: {e}", exc_info=True)
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

    def generate_diff(
        self, before_path: Path, after_path: Path, output_path: Optional[Path] = None
    ) -> tuple[Optional[Path], dict]:
        """Generate visual diff between two screenshots using pixelmatch (T038).

        Resilient to dimension mismatches by padding the smaller image.

        Args:
            before_path: Path to before screenshot
            after_path: Path to after screenshot
            output_path: Optional output path for diff image

        Returns:
            Tuple of (diff_path, stats_dict)
        """
        import json
        import subprocess
        from PIL import Image

        if output_path is None:
            output_path = self.cache_dir / "diff.png"

        if not before_path.exists() or not after_path.exists():
            logger.error(f"Cannot generate diff: missing input images. Before: {before_path.exists()}, After: {after_path.exists()}")
            return None, {"error": "Missing input images"}

        # Check and handle dimension mismatch
        try:
            img_before = Image.open(before_path)
            img_after = Image.open(after_path)

            if img_before.size != img_after.size:
                logger.warning(
                    f"Dimension mismatch detected: Before {img_before.size}, After {img_after.size}. "
                    "Padding images to match."
                )
                
                # New size is max of both
                new_width = max(img_before.width, img_after.width)
                new_height = max(img_before.height, img_after.height)
                
                def pad_image(img, w, h, path):
                    if img.size == (w, h):
                        return path
                    new_img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
                    new_img.paste(img, (0, 0))
                    padded_path = path.parent / f"padded_{path.name}"
                    new_img.save(padded_path)
                    return padded_path

                before_path = pad_image(img_before, new_width, new_height, before_path)
                after_path = pad_image(img_after, new_width, new_height, after_path)
                logger.info(f"Using padded images for diff: {before_path.name}, {after_path.name}")
        except Exception as e:
            logger.error(f"Error while checking image dimensions: {e}")
            # Continue and let visual-diff.js fail gracefully if padding failed

        # Find visual-diff.js script
        script_path = Path(__file__).parent.parent.parent.parent.parent / "scripts" / "visual-diff.js"
        if not script_path.exists():
            script_path = Path("scripts/visual-diff.js")

        if not script_path.exists():
            logger.error(f"visual-diff.js not found at {script_path}")
            return None, {"error": "visual-diff.js script not found"}

        try:
            result = subprocess.run(
                ["node", str(script_path), str(before_path), str(after_path), str(output_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                logger.error(f"visual-diff.js failed: {result.stderr}")
                return None, {"error": result.stderr}

            stats = json.loads(result.stdout)
            logger.info(f"Diff generated: {stats['diffPercentage']:.2f}% different ({stats['diffPixels']} pixels)")
            return output_path, stats

        except subprocess.TimeoutExpired:
            logger.error("visual-diff.js timed out")
            return None, {"error": "Diff generation timed out"}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse visual-diff.js output: {e}")
            return None, {"error": f"Invalid JSON output: {result.stdout}"}
        except Exception as e:
            logger.error(f"Diff generation failed: {e}")
            return None, {"error": str(e)}

    def create_composite(
        self,
        before_path: Path,
        diff_path: Path,
        after_path: Path,
        output_path: Optional[Path] = None,
    ) -> Optional[Path]:
        """Create side-by-side composite image: before | diff | after (T039).

        Args:
            before_path: Path to before screenshot
            diff_path: Path to diff image
            after_path: Path to after screenshot
            output_path: Optional output path for composite

        Returns:
            Path to composite image, or None if failed
        """
        try:
            from PIL import Image

            # Load images
            before = Image.open(before_path)
            diff = Image.open(diff_path)
            after = Image.open(after_path)

            # Calculate composite dimensions
            # Scale down to reasonable size for viewing
            max_height = 800
            scale = min(1.0, max_height / before.height)

            new_width = int(before.width * scale)
            new_height = int(before.height * scale)

            before_scaled = before.resize((new_width, new_height), Image.Resampling.LANCZOS)
            diff_scaled = diff.resize((new_width, new_height), Image.Resampling.LANCZOS)
            after_scaled = after.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Create composite: before | diff | after
            padding = 10
            total_width = new_width * 3 + padding * 4
            total_height = new_height + padding * 2 + 30  # Extra for labels

            composite = Image.new("RGB", (total_width, total_height), (255, 255, 255))

            # Paste images
            y_offset = 30 + padding
            composite.paste(before_scaled, (padding, y_offset))
            composite.paste(diff_scaled, (new_width + padding * 2, y_offset))
            composite.paste(after_scaled, (new_width * 2 + padding * 3, y_offset))

            # Add labels using PIL's ImageDraw
            from PIL import ImageDraw

            draw = ImageDraw.Draw(composite)
            label_y = 5
            draw.text((padding + new_width // 3, label_y), "BEFORE", fill=(0, 0, 0))
            draw.text((new_width + padding * 2 + new_width // 3, label_y), "DIFF", fill=(255, 0, 0))
            draw.text((new_width * 2 + padding * 3 + new_width // 3, label_y), "AFTER", fill=(0, 128, 0))

            if output_path is None:
                output_path = self.cache_dir / "composite.png"

            composite.save(output_path)
            logger.info(f"Composite image saved: {output_path}")
            return output_path

        except ImportError:
            logger.error("PIL not available for composite creation")
            return None
        except Exception as e:
            logger.error(f"Composite creation failed: {e}")
            return None
