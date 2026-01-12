import json
import re
from typing import Any, Dict, List, Union

def extract_json(text: str) -> Union[Dict[str, Any], List[Any], None]:
    """
    Robustly extracts JSON from a string, handling markdown code blocks and surrounding text.
    """
    text = text.strip()
    
    # Try simple parsing first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Remove markdown code blocks
    # This regex matches ```json ... ``` or just ``` ... ```
    # It tries to capture the content inside.
    markdown_pattern = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
    match = markdown_pattern.search(text)
    if match:
        possible_json = match.group(1)
        try:
            return json.loads(possible_json)
        except json.JSONDecodeError:
            pass
            
    # Fallback: Find the first { and last } (for objects) or [ and ] (for arrays)
    # We prioritize objects as that's most common in this app
    
    # Calculate the range for {}
    start_brace = text.find('{')
    end_brace = text.rfind('}')
    
    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
        try:
            return json.loads(text[start_brace:end_brace+1])
        except json.JSONDecodeError:
            pass

    # Calculate the range for []
    start_bracket = text.find('[')
    end_bracket = text.rfind(']')
    
    if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
        try:
            return json.loads(text[start_bracket:end_bracket+1])
        except json.JSONDecodeError:
            pass
            
    return None
