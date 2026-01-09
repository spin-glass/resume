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
    help="Anthropic API key (or set ANTHROPIC_API_KEY env var)",
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
    max_validation_retries: Optional[int],
    strict_validation: bool,
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

    # Get API key
    if not api_key:
        try:
            config = get_config()
            api_key = config.get_api_key()
        except ValueError as e:
            click.echo(f"Error: {e} Please create a .env file with your API key.", err=True)
            sys.exit(3)

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
    click.echo()

    try:
        # Load resume
        logger.info(f"Loading resume from {input_file}")
        parser = QMDParser()
        resume = parser.load_resume(input_file)
        click.echo(f"✓ Resume loaded ({len(resume.content)} characters)")

        # Create review session
        from .config.settings import DEFAULT_MAX_VALIDATION_RETRIES

        session = ReviewSession(
            resume=resume,
            target_role=target_role,
            score_threshold=threshold,
            max_iterations=max_iterations,
            dry_run=dry_run,
            screenshot_url=screenshot_url,
            max_validation_retries=max_validation_retries if max_validation_retries is not None else DEFAULT_MAX_VALIDATION_RETRIES,
            strict_validation=strict_validation,
        )

        # Run workflow
        logger.info("Starting review workflow")
        click.echo("\nReview starting...")

        # Callback for iteration saves
        def on_iteration_saved(iteration: int, score: float, path: Path):
            click.echo(f"  💾 Iteration {iteration} saved: {path.name} (score: {score:.1f})")

        workflow = ReviewWorkflow(
            api_key,
            save_iterations=save_iterations,
            output_dir=iterations_dir,
            on_iteration_complete=on_iteration_saved if save_iterations else None,
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
