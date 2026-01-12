import asyncio
import click
from pathlib import Path
from typing import Optional

from ..services.llm_factory import LLMClientFactory
from ..config.model_config import AgentName
from ..utils.config import get_config, setup_logging

async def _run_feedback_logic(
    input_file: Path,
    verbose: bool
):
    logger = setup_logging(verbose=verbose)
    config = get_config()
    
    # Path resolution logic (support running from subdirectory)
    if not input_file.exists():
        # Try finding it relative to project root if we are in packages/resume-review
        fallback_path = Path("../../") / input_file
        if fallback_path.exists():
            if verbose:
                click.echo(f"Info: Found file at fallback path: {fallback_path}")
            input_file = fallback_path
        else:
            click.echo(f"Error: Input file '{input_file}' not found (checked relative paths).", err=True)
            return

    # Read Content
    try:
        content = input_file.read_text(encoding="utf-8")
        logger.info(f"Loaded content from {input_file}")
    except Exception as e:
        click.echo(f"Error reading file: {e}", err=True)
        return

    prompt = f"""
    You are a Senior Technical Recruiter and Engineering Manager acting as a mentor.
    Review the following "Experience Description" (STAR format) for a resume.
    
    Goal: Make it impactful, quantifying results, and ensuring technical depth matches the role.
    
    Input Content:
    {content}
    
    Output Format: Markdown.
    
    Please provide:
    1. **Overall Score (1-5)**: With brief justification.
    2. **Strengths**: What is good?
    3. **Areas for Improvement**:
       - Ambiguous actions?
       - Lacking metrics?
       - Tech stack mentioned but not explained how it was used?
    4. **Refinement Suggestions**:
       - rewrite specific sentences or sections to be more professional or impactful.
    
    Language: Japanese.
    """

    # Initialize Client
    try:
        client = LLMClientFactory.create_client(
            agent_name=AgentName.RECRUITER, 
            gemini_api_key=config.get_gemini_api_key(),
            anthropic_api_key=config.get_anthropic_api_key(),
            openai_api_key=config.get_openai_api_key()
        )
    except Exception as e:
        click.echo(f"Error creating LLM client: {e}", err=True)
        return
    
    click.echo(f"Generating feedback for '{input_file.name}'...")
    
    try:
        response = await client.generate_async(
            system_prompt="You are a strict but helpful technical resume reviewer.",
            user_prompt=prompt,
            max_tokens=2000
        )
        feedback_content = response.content
        
        # Save feedback file
        feedback_filename = input_file.stem + "_feedback.md"
        output_path = input_file.parent / feedback_filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# Feedback for {input_file.name}\n\n")
            f.write(feedback_content)
            
        click.echo(f"Feedback saved to: {output_path}")

    except Exception as e:
        click.echo(f"Error generating feedback: {e}", err=True)

def run_feedback_command(
    input_file: Path,
    verbose: bool
):
    """
    Generates feedback for a STAR draft.
    """
    asyncio.run(_run_feedback_logic(input_file, verbose))
