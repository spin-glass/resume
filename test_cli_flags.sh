#!/bin/bash
# Test script for design auto-fix CLI flags

echo "🧪 Testing Design Auto-Fix CLI Flags"
echo "======================================"
echo

cd packages/resume-review

echo "1️⃣  Test: --auto-design and --design-preview mutual exclusivity"
python -m src.cli review \
  --input ../../resume/resume-ja.qmd \
  --auto-design \
  --design-preview \
  2>&1 | grep -q "mutually exclusive"

if [ $? -eq 0 ]; then
  echo "   ✓ Mutual exclusivity check works"
else
  echo "   ❌ Mutual exclusivity check failed"
fi

echo

echo "2️⃣  Test: --css-output requires design flag"
python -m src.cli review \
  --input ../../resume/resume-ja.qmd \
  --css-output custom.css \
  2>&1 | grep -q "requires either"

if [ $? -eq 0 ]; then
  echo "   ✓ CSS output validation works"
else
  echo "   ❌ CSS output validation failed"
fi

echo

echo "3️⃣  Test: --design-preview without screenshot warning"
python -m src.cli review \
  --input ../../resume/resume-ja.qmd \
  --design-preview \
  --dry-run \
  2>&1 | head -20 | grep -q "Warning.*screenshot"

if [ $? -eq 0 ]; then
  echo "   ✓ Screenshot warning works"
else
  echo "   ❌ Screenshot warning not shown"
fi

echo

echo "4️⃣  Test: Help shows new options"
python -m src.cli review --help | grep -q "auto-design"
if [ $? -eq 0 ]; then
  echo "   ✓ --auto-design in help"
else
  echo "   ❌ --auto-design missing from help"
fi

python -m src.cli review --help | grep -q "design-preview"
if [ $? -eq 0 ]; then
  echo "   ✓ --design-preview in help"
else
  echo "   ❌ --design-preview missing from help"
fi

python -m src.cli review --help | grep -q "css-output"
if [ $? -eq 0 ]; then
  echo "   ✓ --css-output in help"
else
  echo "   ❌ --css-output missing from help"
fi

echo
echo "✅ CLI validation tests complete!"
