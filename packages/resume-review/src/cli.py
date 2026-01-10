"""CLI entry point for resume review system."""

import sys
from pathlib import Path
from typing import Optional

import click

from .models.feedback import Resume
from .models.session import ReviewSession
from .workflow import ReviewWorkflow
from .services.qmd_parser import QMDParser
from .utils.config import get_config, setup_logging


def _display_design_changes(session: ReviewSession, verbose: bool = False) -> None:
    """Display design changes that were applied (T033).

    Args:
        session: Review session with design output data
        verbose: Whether to show detailed output
    """
    click.echo("\n" + "=" * 60)
    click.echo("DESIGN MODIFICATIONS")
    click.echo("=" * 60)

    if not session.design_changes_applied:
        click.echo("\nNo design changes were applied.")
        return

    # Display CSS modifications
    if session.css_modification:
        css_mod = session.css_modification
        target_file = css_mod.get("target_file", "unknown")
        click.echo(f"\n✓ CSS Generated: {target_file}")

        # Show issue types addressed
        issue_types = css_mod.get("issue_types", [])
        if issue_types:
            click.echo(f"  Issues addressed: {', '.join(issue_types)}")

        # Show changes list
        changes = css_mod.get("changes", [])
        if changes and verbose:
            click.echo("  Changes:")
            for change in changes[:5]:  # Show first 5 changes
                click.echo(f"    • {change}")

        # Show validation status
        if css_mod.get("validation_passed"):
            click.echo("  Validation: ✓ Passed")
        else:
            errors = css_mod.get("validation_errors", [])
            click.echo(f"  Validation: ✗ Failed ({len(errors)} errors)")
            if verbose:
                for error in errors[:3]:
                    click.echo(f"    - {error}")

    # Display section reorder if applied (T058)
    if session.section_reorder:
        reorder = session.section_reorder
        click.echo(f"\n✓ Section Reorder Applied")
        if reorder.get("original_order") and reorder.get("new_order"):
            click.echo(f"  Original: {' → '.join(reorder['original_order'])}")
            click.echo(f"  New:      {' → '.join(reorder['new_order'])}")
        if verbose and reorder.get("rationale"):
            click.echo(f"  Rationale: {reorder['rationale'][:100]}...")

    # Display backup paths
    if session.design_backup_paths:
        click.echo("\nBackups created:")
        for original, backup in session.design_backup_paths.items():
            click.echo(f"  {original} → {backup}")

    # Display summary of changes
    if session.design_changes_list:
        click.echo("\nChanges applied:")
        for change in session.design_changes_list:
            click.echo(f"  • {change}")

    # Display theme recommendation (T067) - advisory only
    if session.theme_recommendation:
        theme = session.theme_recommendation
        click.echo(f"\n💡 Theme Recommendation (Advisory):")
        click.echo(f"  Theme: {theme.get('theme_name')}")
        if theme.get('rationale'):
            click.echo(f"  Reason: {theme['rationale'][:100]}...")
        if theme.get('installation_command'):
            click.echo(f"  To apply: {theme['installation_command']}")
        if verbose and theme.get('preview_url'):
            click.echo(f"  Preview: {theme['preview_url']}")


def _display_design_preview(session: ReviewSession, verbose: bool = False) -> None:
    """Display design preview information without applying changes (T045).

    Args:
        session: Review session with pending design changes
        verbose: Whether to show detailed output
    """
    click.echo("\n" + "=" * 60)
    click.echo("DESIGN PREVIEW (Not Applied)")
    click.echo("=" * 60)

    if not session.design_changes_pending:
        click.echo("\nNo design changes to preview.")
        return

    # Display visual preview if available
    preview_paths = getattr(session, "design_preview_paths", None)
    if preview_paths:
        click.echo("\n📷 Visual Preview Generated:")
        if preview_paths.get("before"):
            click.echo(f"  Before: {preview_paths['before']}")
        if preview_paths.get("after"):
            click.echo(f"  After:  {preview_paths['after']}")
        if preview_paths.get("diff"):
            click.echo(f"  Diff:   {preview_paths['diff']}")
        if preview_paths.get("composite"):
            click.echo(f"  Composite: {preview_paths['composite']}")

    # Display diff statistics
    design_preview = getattr(session, "design_preview", None)
    if design_preview:
        diff_pct = design_preview.get("diff_percentage")
        diff_pixels = design_preview.get("diff_pixel_count")
        if diff_pct is not None:
            click.echo(f"\n📊 Change Statistics:")
            click.echo(f"  Pixels Changed: {diff_pixels:,} ({diff_pct:.2f}%)")
            if diff_pct > 5.0:
                click.echo("  ⚠ Significant visual changes detected")
            elif diff_pct > 0:
                click.echo("  ✓ Minor visual changes")
            else:
                click.echo("  ℹ No visual changes (CSS may not affect current page)")

    # Display CSS modifications preview
    if session.css_modification:
        css_mod = session.css_modification
        target_file = css_mod.get("target_file", "unknown")
        click.echo(f"\n📝 CSS Will Be Generated: {target_file}")

        # Show issue types that would be addressed
        issue_types = css_mod.get("issue_types", [])
        if issue_types:
            click.echo(f"  Issues to address: {', '.join(issue_types)}")

        # Show proposed changes
        changes = css_mod.get("changes", [])
        if changes:
            click.echo("  Proposed changes:")
            for change in changes[:5]:
                click.echo(f"    • {change}")

        # Show CSS content preview if verbose
        if verbose and css_mod.get("css_content"):
            css_content = css_mod.get("css_content", "")
            preview_lines = css_content.split("\n")[:15]
            click.echo("\n  CSS Preview:")
            for line in preview_lines:
                click.echo(f"    {line}")
            if len(css_content.split("\n")) > 15:
                click.echo("    ...")

    # Display proposed section reorder (T059)
    if session.section_reorder:
        reorder = session.section_reorder
        click.echo(f"\n🔄 Section Reorder Recommended:")
        if reorder.get("original_order") and reorder.get("new_order"):
            click.echo(f"  Current: {' → '.join(reorder['original_order'])}")
            click.echo(f"  Proposed: {' → '.join(reorder['new_order'])}")
        if verbose and reorder.get("rationale"):
            click.echo(f"  Rationale: {reorder['rationale'][:150]}...")

    # Display theme recommendation in preview (T068)
    if session.theme_recommendation:
        theme = session.theme_recommendation
        click.echo(f"\n💡 Theme Recommendation (Advisory):")
        click.echo(f"  Theme: {theme.get('theme_name')}")
        if theme.get('rationale'):
            click.echo(f"  Reason: {theme['rationale'][:100]}...")
        if theme.get('installation_command'):
            click.echo(f"  To apply: {theme['installation_command']}")

    # Instructions for applying
    click.echo("\n" + "-" * 40)
    click.echo("To apply these changes, run:")
    click.echo("  resume-review review --input <file> --auto-design")


@click.group()
def cli():
    """Resume Review Multi-Agent System CLI."""
    pass


@cli.command()
@click.option(
    "--input",
    "-i",
    "input_file",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to input QMD file",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to output QMD file (default: no automatic save)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview changes without modifying file (FR-010)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable verbose output (FR-012)",
)
@click.option(
    "--target-role",
    default="LLM/Multi-Agent Engineer",
    help="Target position for resume optimization",
)
@click.option(
    "--threshold",
    type=float,
    default=8.0,
    help="Minimum score threshold (1.0-10.0, default: 8.0)",
)
@click.option(
    "--max-iterations",
    type=int,
    default=3,
    help="Maximum revision iterations (default: 3)",
)
@click.option(
    "--screenshot-url",
    default=None,
    help="URL for visual design review (optional, FR-013)",
)
@click.option(
    "--save-iterations",
    is_flag=True,
    default=False,
    help="Save resume after each iteration for comparison",
)
@click.option(
    "--iterations-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory for iteration saves (default: same as input file)",
)
@click.option(
    "--api-key",
    envvar="ANTHROPIC_API_KEY",
    help="Anthropic API key (or set ANTHROPIC_API_KEY env var) [LEGACY]",
)
@click.option(
    "--anthropic-api-key",
    envvar="ANTHROPIC_API_KEY",
    help="Anthropic API key (or set ANTHROPIC_API_KEY env var)",
)
@click.option(
    "--gemini-api-key",
    envvar="GEMINI_API_KEY",
    help="Google Gemini API key (or set GEMINI_API_KEY env var)",
)
@click.option(
    "--openai-api-key",
    envvar="OPENAI_API_KEY",
    help="OpenAI API key (or set OPENAI_API_KEY env var)",
)
@click.option(
    "--model",
    default=None,
    help="Override model for all agents (e.g., 'gemini-3.0-flash', 'claude-sonnet-4-5-20250929')",
)
@click.option(
    "--max-validation-retries",
    type=int,
    default=None,
    help="Maximum validation retry attempts per iteration (default: 3). Set to 0 to skip retries.",
)
@click.option(
    "--strict-validation",
    is_flag=True,
    default=False,
    help="Exit workflow if Quarto validation fails after all retries (default: continue with warning)",
)
@click.option(
    "--auto-design",
    is_flag=True,
    default=False,
    help="Automatically apply design improvements from feedback (013-design-auto-fix)",
)
@click.option(
    "--design-preview",
    is_flag=True,
    default=False,
    help="Generate before/after preview without applying changes (013-design-auto-fix)",
)
@click.option(
    "--css-output",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    default=None,
    help="Custom output path for generated CSS (default: styles/resume-custom.css)",
)
def review(
    input_file: Path,
    output_file: Optional[Path],
    dry_run: bool,
    verbose: bool,
    target_role: str,
    threshold: float,
    max_iterations: int,
    screenshot_url: Optional[str],
    save_iterations: bool,
    iterations_dir: Optional[Path],
    api_key: Optional[str],
    anthropic_api_key: Optional[str],
    gemini_api_key: Optional[str],
    openai_api_key: Optional[str],
    model: Optional[str],
    max_validation_retries: Optional[int],
    strict_validation: bool,
    auto_design: bool,
    design_preview: bool,
    css_output: Optional[Path],
):
    """
    Run multi-agent resume review and improvement.

    IMPORTANT: This command NEVER overwrites the input file automatically.
    Results are saved in review_TIMESTAMP/ directories.
    Manually copy the desired iteration to apply changes.

    Examples:

        # Basic review with iteration saves
        resume-review review --input resume.qmd --save-iterations

        # Apply changes manually after review
        cp review_20260109_123456/iter3/resume.qmd resume.qmd

        # Dry-run preview (no saves)
        resume-review review --input resume.qmd --dry-run

        # Full review with design analysis
        resume-review review --input resume.qmd --screenshot-url http://localhost:3000/ja --save-iterations

        # Custom threshold and role
        resume-review review --input resume.qmd --threshold 9.0 --target-role "Senior Backend Engineer" --save-iterations

        # With custom validation retry settings
        resume-review review --input resume.qmd --max-validation-retries 1 --save-iterations

        # Strict validation mode (exit on validation failure)
        resume-review review --input resume.qmd --strict-validation --save-iterations

        # Skip validation retries entirely
        resume-review review --input resume.qmd --max-validation-retries 0 --save-iterations
    """
    # Setup logging
    logger = setup_logging(verbose=verbose)

    # Validate inputs
    if threshold < 1.0 or threshold > 10.0:
        click.echo("Error: Threshold must be between 1.0 and 10.0", err=True)
        sys.exit(2)

    # Validate max_validation_retries (T038)
    if max_validation_retries is not None and max_validation_retries < 0:
        click.echo("Error: max-validation-retries must be >= 0", err=True)
        sys.exit(2)

    if max_iterations < 1:
        click.echo("Error: Max iterations must be >= 1", err=True)
        sys.exit(2)

    # Validate design flags (T031)
    if auto_design and design_preview:
        click.echo(
            "Error: --auto-design and --design-preview are mutually exclusive. "
            "Use --design-preview to review changes first, then run with --auto-design to apply.",
            err=True,
        )
        sys.exit(2)

    if css_output and not (auto_design or design_preview):
        click.echo(
            "Error: --css-output requires either --auto-design or --design-preview",
            err=True,
        )
        sys.exit(2)

    # Dry run precedence over auto-design
    if dry_run and auto_design:
        click.echo(
            "Note: --dry-run enabled. Design modifications will be generated but not applied.",
            err=True,
        )
        auto_design = False

    # Warning for design-preview without screenshot-url
    if design_preview and not screenshot_url:
        click.echo(
            "Warning: --design-preview works best with --screenshot-url. "
            "Preview will be text-only without screenshots.",
            err=True,
        )

    # Get API keys from config if not provided
    if not anthropic_api_key and not api_key:
        try:
            config = get_config()
            anthropic_api_key = config.get_anthropic_api_key()
            if not gemini_api_key:
                gemini_api_key = config.get_gemini_api_key()
            if not openai_api_key:
                openai_api_key = config.get_openai_api_key()
        except ValueError as e:
            click.echo(f"Error: {e} Please create a .env file with your API key.", err=True)
            sys.exit(3)

    # Backward compatibility: use api_key if anthropic_api_key not set
    if not anthropic_api_key:
        anthropic_api_key = api_key

    # Display header
    if dry_run:
        click.echo("=== RESUME REVIEW (DRY RUN) ===\n")
    else:
        click.echo("=== RESUME REVIEW ===\n")

    click.echo(f"Input: {input_file}")
    click.echo(f"Target Role: {target_role}")
    click.echo(f"Score Threshold: {threshold}/10.0")
    click.echo(f"Max Iterations: {max_iterations}")
    if screenshot_url:
        click.echo(f"Screenshot URL: {screenshot_url}")

    # Verbose: Display model configuration
    if verbose:
        click.echo()
        if model:
            # Override mode
            click.echo(f"Mode: Override all agents with {model}")
        else:
            # Hybrid mode
            click.echo("Mode: Hybrid configuration (optimal model per agent)")
            from .config.model_config import AGENT_MODEL_MAP, AgentName
            click.echo("\nAgent Model Assignments:")
            for agent_name in [
                AgentName.RECRUITER,
                AgentName.TECHNICAL_WRITER,
                AgentName.COPYWRITER,
                AgentName.UX_DESIGNER,
                AgentName.VISUAL_DESIGNER,
                AgentName.REVISOR,
            ]:
                config = AGENT_MODEL_MAP.get(agent_name)
                if config:
                    click.echo(f"  {agent_name.value:20} → {config['model_id']:30} ({config['provider']})")

    click.echo()

    try:
        # Load resume
        logger.info(f"Loading resume from {input_file}")
        parser = QMDParser()
        resume = parser.load_resume(input_file)
        click.echo(f"✓ Resume loaded ({len(resume.content)} characters)")

        # Create review session
        from .config.settings import CSS_OUTPUT_DEFAULT, DEFAULT_MAX_VALIDATION_RETRIES

        session = ReviewSession(
            resume=resume,
            target_role=target_role,
            score_threshold=threshold,
            max_iterations=max_iterations,
            dry_run=dry_run,
            screenshot_url=screenshot_url,
            max_validation_retries=max_validation_retries if max_validation_retries is not None else DEFAULT_MAX_VALIDATION_RETRIES,
            strict_validation=strict_validation,
            auto_design_enabled=auto_design,
            design_preview_enabled=design_preview,
            css_output_path=str(css_output) if css_output else CSS_OUTPUT_DEFAULT,
        )

        # Run workflow
        logger.info("Starting review workflow")
        click.echo("\nReview starting...")

        # Callback for iteration saves
        def on_iteration_saved(iteration: int, score: float, path: Path):
            click.echo(f"  💾 Iteration {iteration} saved: {path.name} (score: {score:.1f})")

        workflow = ReviewWorkflow(
            api_key=anthropic_api_key,  # Legacy parameter (backward compat)
            save_iterations=save_iterations,
            output_dir=iterations_dir,
            on_iteration_complete=on_iteration_saved if save_iterations else None,
            gemini_api_key=gemini_api_key,
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            override_model=model,
        )
        session = workflow.run_review(session)

        # Display results
        click.echo("\n" + "=" * 60)
        click.echo("REVIEW SUMMARY")
        click.echo("=" * 60)

        final_score = session.final_score or 0.0
        click.echo(f"\nIntegrated Score: {final_score:.1f}/10.0")
        click.echo(f"Threshold: {session.score_threshold}/10.0")
        click.echo(f"Iterations Used: {session.current_iteration}/{session.max_iterations}")

        if final_score >= session.score_threshold:
            click.echo("\n✓ Threshold met!")
        else:
            click.echo(f"\n⚠ Threshold not met (gap: {session.score_threshold - final_score:.1f} points)")

        # Show revisions
        if session.applied_revisions:
            click.echo(f"\nChanges Applied: {len(session.applied_revisions)}")
            if verbose:
                for i, revision in enumerate(session.applied_revisions, 1):
                    click.echo(f"  {i}. {revision}")
        else:
            click.echo("\nChanges Applied: 0")

        # Show portfolio suggestions
        if session.portfolio_suggestions:
            click.echo(f"\nPortfolio Projects Suggested: {len(session.portfolio_suggestions)}")
            if verbose:
                for item in session.portfolio_suggestions:
                    click.echo(f"  • {item.repository_name}: {item.description}")
        else:
            click.echo("\nPortfolio Projects Suggested: 0")

        # Show design changes (T034: Call _display_design_changes after workflow)
        if session.design_changes_applied:
            _display_design_changes(session, verbose=verbose)
        elif session.design_changes_pending:
            _display_design_preview(session, verbose=verbose)

        # Show detailed feedback if verbose
        if verbose and session.feedback_history:
            click.echo("\n" + "=" * 60)
            click.echo("DETAILED FEEDBACK")
            click.echo("=" * 60)

            for iteration, feedback_list in enumerate(session.feedback_history, 1):
                click.echo(f"\n--- Iteration {iteration} ---")
                for feedback in feedback_list:
                    click.echo(f"\n{feedback.agent_name.upper()}: {feedback.score}/10.0")
                    if feedback.strengths:
                        click.echo("  Strengths:")
                        for s in feedback.strengths[:3]:  # Show first 3
                            click.echo(f"    • {s}")
                    if feedback.issues:
                        click.echo("  Issues:")
                        for issue in feedback.issues[:3]:  # Show first 3
                            click.echo(f"    • {issue.description}")

        # Display save information (no automatic overwriting)
        if dry_run:
            click.echo("\n[DRY RUN] No changes saved")
        elif save_iterations:
            click.echo(f"\n✓ All iterations saved in session directory")
            click.echo(f"📋 To apply changes: manually copy the desired iteration to {input_file}")
            click.echo(f"   Example: cp review_*/iter3/resume.qmd {input_file}")
        elif output_file:
            # Only save if explicit output file is specified
            output_file.parent.mkdir(parents=True, exist_ok=True)
            parser.save_resume(session.resume, output_file)
            click.echo(f"\n✓ Resume saved to: {output_file}")
            click.echo(f"📋 To apply: cp {output_file} {input_file}")
        else:
            click.echo("\n⚠️  No output file specified. Changes not saved.")
            click.echo(f"📋 To apply changes: specify --output or manually copy from session directory")

        # Exit code
        if final_score >= session.score_threshold:
            sys.exit(0)  # Success
        else:
            sys.exit(4)  # Threshold not met

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Validation Error: {e}", err=True)
        sys.exit(2)
    except Exception as e:
        logger.exception("Unexpected error during review")
        click.echo(f"Error: {e}", err=True)
        sys.exit(6)


@cli.command()
def version():
    """Display version information."""
    from . import __version__

    click.echo(f"Resume Review Multi-Agent System v{__version__}")
    click.echo("Powered by LangGraph and Claude Sonnet 4.5")


def main():
    """Entry point for console script."""
    cli()


if __name__ == "__main__":
    main()
