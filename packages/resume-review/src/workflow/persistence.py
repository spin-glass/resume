"""File persistence helpers for saving workflow artifacts."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from ..models.feedback import Feedback
from ..models.session import ReviewSession
from ..services.qmd_parser import QMDParser

logger = logging.getLogger("resume_review")

SEVERITY_EMOJI = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}


def create_session_directory(output_dir: Optional[Path], resume_file_path: Path) -> tuple[Path, str]:
    """Create a directory for review session outputs."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = output_dir or resume_file_path.parent
    session_dir = base_dir / f"review_{timestamp}"
    session_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created session directory: {session_dir}")
    return session_dir, timestamp


def save_iteration(session: ReviewSession, session_dir: Optional[Path],
                   output_dir: Optional[Path], iteration: int, label: str = "") -> Optional[Path]:
    """Save resume state at current iteration."""
    try:
        if session_dir is None:
            out_dir = output_dir or session.resume.file_path.parent
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            iteration_path = out_dir / f"{session.resume.file_path.stem}_{timestamp}_{label}.qmd"
        elif iteration == 0:
            iteration_path = session_dir / "original.qmd"
        else:
            iter_dir = session_dir / f"iter{iteration}"
            iter_dir.mkdir(exist_ok=True)
            iteration_path = iter_dir / "resume.qmd"
        QMDParser.save_resume(session.resume, iteration_path, create_backup=False)
        logger.info(f"Saved iteration {iteration}: {iteration_path}")
        return iteration_path
    except Exception as e:
        logger.error(f"Failed to save iteration {iteration}: {e}")
        return None


def save_feedback(session_dir: Path, feedback_list: list[Feedback],
                  iteration: int, integrated_score: float) -> Optional[Path]:
    """Save agent feedback as Markdown and JSON files."""
    if not feedback_list:
        return None
    try:
        iter_dir = session_dir / f"iter{iteration}"
        iter_dir.mkdir(exist_ok=True)
        feedback_path = iter_dir / "feedback.md"
        with open(feedback_path, "w", encoding="utf-8") as f:
            f.write(_format_feedback_markdown(feedback_list, iteration, integrated_score))
        json_path = iter_dir / "feedback.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(_format_feedback_json(feedback_list, iteration, integrated_score),
                      f, ensure_ascii=False, indent=2)
        logger.info(f"Saved feedback for iteration {iteration}: {feedback_path}")
        return feedback_path
    except Exception as e:
        logger.error(f"Failed to save feedback for iteration {iteration}: {e}")
        return None


def save_revisions(session_dir: Path, revisions: list[str], iteration: int) -> Optional[Path]:
    """Save applied revisions as Markdown file."""
    if not revisions:
        return None
    try:
        iter_dir = session_dir / f"iter{iteration}"
        iter_dir.mkdir(exist_ok=True)
        revisions_path = iter_dir / "revisions.md"
        with open(revisions_path, "w", encoding="utf-8") as f:
            f.write(_format_revisions_markdown(revisions, iteration))
        logger.info(f"Saved revisions for iteration {iteration}: {revisions_path}")
        return revisions_path
    except Exception as e:
        logger.error(f"Failed to save revisions for iteration {iteration}: {e}")
        return None


def _format_feedback_markdown(feedback_list: list[Feedback], iteration: int,
                               integrated_score: float) -> str:
    """Format feedback list as Markdown."""
    lines = [f"# Iteration {iteration} Feedback\n",
             f"**Integrated Score: {integrated_score:.2f}/10.0**\n",
             f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", "---\n"]
    for fb in feedback_list:
        lines.append(f"## {fb.agent_name.replace('_', ' ').title()}\n")
        lines.append(f"**Score: {fb.score:.1f}/10.0**\n\n### Strengths\n")
        lines.extend(f"- {s}\n" for s in fb.strengths)
        lines.append("\n### Issues\n")
        for issue in fb.issues:
            emoji = SEVERITY_EMOJI.get(issue.severity.value, "⚪")
            lines.append(f"- {emoji} **[{issue.severity.value.upper()}]** {issue.description}\n")
            if issue.location:
                lines.append(f"  - Location: {issue.location}\n")
            lines.append(f"  - Action: {issue.action_type.value}\n")
        lines.append("\n### Suggestions\n")
        lines.extend(f"- {s}\n" for s in fb.suggestions)
        lines.append("\n---\n\n")
    return "".join(lines)


def _format_feedback_json(feedback_list: list[Feedback], iteration: int,
                           integrated_score: float) -> dict[str, Any]:
    """Format feedback list as JSON-serializable dict."""
    return {
        "iteration": iteration, "integrated_score": integrated_score,
        "timestamp": datetime.now().isoformat(),
        "feedback": [{
            "agent_name": fb.agent_name, "score": fb.score, "strengths": fb.strengths,
            "issues": [{"description": i.description, "severity": i.severity.value,
                        "action_type": i.action_type.value, "location": i.location}
                       for i in fb.issues],
            "suggestions": fb.suggestions,
        } for fb in feedback_list],
    }


def _format_revisions_markdown(revisions: list[str], iteration: int) -> str:
    """Format revisions list as Markdown."""
    lines = [f"# Iteration {iteration} Revisions\n",
             f"**Total Revisions Applied: {len(revisions)}**\n",
             f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", "---\n"]
    for i, rev in enumerate(revisions, 1):
        if rev.startswith("[DRY RUN]"):
            lines.append(f"### {i}. (Dry Run) {rev[10:].strip()}\n\n")
        elif rev.startswith("Applied"):
            lines.append(f"### {i}. ✅ {rev}\n\n")
        elif rev.startswith("Failed"):
            lines.append(f"### {i}. ❌ {rev}\n\n")
        else:
            lines.append(f"### {i}. {rev}\n\n")
    return "".join(lines)
