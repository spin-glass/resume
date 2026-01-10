#!/usr/bin/env python3
"""Generate Studio-ready input JSON for LangGraph Studio testing.

Usage:
    python scripts/generate_studio_input.py > studio_input.json
    
Then copy the JSON output and paste it into Studio's input panel.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.workflow.studio import get_default_studio_input


def main():
    """Generate and print Studio input JSON."""
    input_data = get_default_studio_input()
    
    # Convert to JSON with proper formatting
    print(json.dumps(input_data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
