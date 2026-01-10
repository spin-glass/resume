"""Studio-specific graph wrapper with default inputs for LangGraph Studio testing."""

import os
from pathlib import Path

from typing import Any
from langgraph.graph.state import CompiledStateGraph
from .graph import build_review_workflow
from .state import ReviewState
from ..services.qmd_parser import QMDParser


def build_studio_workflow() -> CompiledStateGraph[ReviewState, Any, Any]:
    """
    Build workflow with default inputs pre-loaded for LangGraph Studio testing.
    
    This wrapper loads the actual resume file and provides sensible defaults
    so that Studio users can test without manually entering all required fields.
    """
    # Build the base workflow
    return build_review_workflow()


def get_default_studio_input() -> dict[str, Any]:
    """
    Get default input state for Studio testing.
    
    Returns a dictionary that can be used as initial state in Studio.
    This loads the actual resume from the repository.
    """
    # Find the resume file (relative to package root)
    package_root = Path(__file__).parent.parent.parent
    resume_path = package_root.parent.parent / "resume" / "resume-ja.qmd"
    
    if resume_path.exists():
        parser = QMDParser()
        resume = parser.load_resume(resume_path)
        resume_dict = {
            "file_path": str(resume.file_path),
            "content": resume.content,
            "yaml_frontmatter": resume.yaml_frontmatter,
            "full_text": resume.full_text,
        }
    else:
        # Fallback minimal resume for testing
        resume_dict = {
            "file_path": "test.qmd",
            "content": "# テスト履歴書\n\n## 職務要約\nソフトウェアエンジニア\n\n## スキル\n- Python\n- LangChain",
            "yaml_frontmatter": {"title": "テスト"},
            "full_text": "---\ntitle: テスト\n---\n# テスト履歴書\n\n## 職務要約\nソフトウェアエンジニア",
        }
    
    return {
        "resume": resume_dict,
        "resume_content": resume_dict["content"],
        "target_role": "LLM/Multi-Agent Engineer",
        "score_threshold": 8.0,
        "max_iterations": 1,
        "dry_run": True,
        "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    }
