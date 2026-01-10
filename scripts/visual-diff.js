#!/usr/bin/env node
/**
 * Visual diff script using pixelmatch.
 * Generates a diff image from before/after screenshots.
 *
 * Usage: node visual-diff.js <before.png> <after.png> <output-diff.png>
 *
 * Output: JSON to stdout with format:
 *   { "diffPixels": 1234, "totalPixels": 100000, "diffPercentage": 1.234 }
 *
 * Exit codes:
 *   0: Success
 *   1: Error (message to stderr)
 */

const fs = require('fs');
const { PNG } = require('pngjs');
const pixelmatch = require('pixelmatch');

async function main() {
  const args = process.argv.slice(2);

  if (args.length !== 3) {
    console.error('Usage: visual-diff.js <before.png> <after.png> <output-diff.png>');
    process.exit(1);
  }

  const [beforePath, afterPath, outputPath] = args;

  // Validate input files exist
  if (!fs.existsSync(beforePath)) {
    console.error(`Error: Before image not found: ${beforePath}`);
    process.exit(1);
  }
  if (!fs.existsSync(afterPath)) {
    console.error(`Error: After image not found: ${afterPath}`);
    process.exit(1);
  }

  try {
    // Read images
    const beforeImg = PNG.sync.read(fs.readFileSync(beforePath));
    const afterImg = PNG.sync.read(fs.readFileSync(afterPath));

    // Validate dimensions match
    if (beforeImg.width !== afterImg.width || beforeImg.height !== afterImg.height) {
      console.error(
        `Error: Image dimensions don't match. ` +
        `Before: ${beforeImg.width}x${beforeImg.height}, ` +
        `After: ${afterImg.width}x${afterImg.height}`
      );
      process.exit(1);
    }

    const { width, height } = beforeImg;

    // Create diff image
    const diff = new PNG({ width, height });

    // Run pixelmatch
    const diffPixels = pixelmatch(
      beforeImg.data,
      afterImg.data,
      diff.data,
      width,
      height,
      {
        threshold: 0.1,        // Sensitivity (0 = exact, 1 = loose)
        includeAA: false,      // Ignore anti-aliasing differences
        diffColor: [255, 0, 0], // Red for differences
        diffColorAlt: [0, 255, 0], // Green for anti-aliased differences
      }
    );

    // Write diff image
    fs.writeFileSync(outputPath, PNG.sync.write(diff));

    // Calculate stats
    const totalPixels = width * height;
    const diffPercentage = (diffPixels / totalPixels) * 100;

    // Output JSON result
    const result = {
      diffPixels,
      totalPixels,
      diffPercentage: Math.round(diffPercentage * 1000) / 1000,
      width,
      height,
      outputPath,
    };

    console.log(JSON.stringify(result));
    process.exit(0);

  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

main();
