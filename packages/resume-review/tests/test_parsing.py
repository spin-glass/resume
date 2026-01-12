import pytest
from src.utils.parsing import extract_json

def test_extract_simple_json():
    text = '{"key": "value"}'
    assert extract_json(text) == {"key": "value"}

def test_extract_markdown_json():
    text = '```json\n{"key": "value"}\n```'
    assert extract_json(text) == {"key": "value"}

def test_extract_markdown_no_lang():
    text = '```\n{"key": "value"}\n```'
    assert extract_json(text) == {"key": "value"}

def test_extract_json_with_text_around():
    text = 'Here is the JSON:\n{"key": "value"}\nHope this helps.'
    assert extract_json(text) == {"key": "value"}

def test_extract_json_partial_block_if_possible():
    # If regex fails, it might fallback to brace finding
    text = 'Foo {"key": "value"} Bar'
    assert extract_json(text) == {"key": "value"}

def test_invalid_json_returns_none():
    text = 'This is not json'
    assert extract_json(text) is None
    
def test_unbalanced_braces_handling():
    # It attempts to find outermost braces. 
    # {"a": {"b": "c"}} is valid
    text = 'Prefix {"a": {"b": "c"}} Suffix'
    assert extract_json(text) == {"a": {"b": "c"}}
