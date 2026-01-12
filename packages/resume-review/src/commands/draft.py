import asyncio
import click
from pathlib import Path
from typing import Optional
import datetime

from ..services.llm_factory import LLMClientFactory
from ..config.model_config import AgentName
from ..services.qmd_parser import QMDParser
from ..utils.config import get_config, setup_logging

async def generate_draft(
    context: str,
    project_name: str,
    year: Optional[int],
    api_key: str
) -> str:
    from ..services.llm_client import LLMClient
    
    # Simple direct client usage for draft generation
    # We don't need the full graph state for this one-shot generation
    
    # We need to instantiate a client. 
    # Since we are inside a command, we can use the factory.
    # Note: Factory requires full config usually, but let's try to grab a client.
    
    # TODO: Refactor Factory to be easier to use without complex config if possible, 
    # but for now we follow the pattern.
    pass 

async def _run_draft_logic(
    input_file: Path,
    project_name: str,
    year: Optional[int],
    output_dir: Path,
    verbose: bool
):
    logger = setup_logging(verbose=verbose)
    config = get_config()
    
    # Load Resume Context
    try:
        parser = QMDParser()
        resume = parser.load_resume(input_file)
        logger.info(f"Loaded resume from {input_file}")
    except Exception as e:
        click.echo(f"Error loading resume: {e}", err=True)
        return

    # Prepare Prompt
    # We want a high-quality "Default" filled in
    context_text = f"Full Resume:\n{resume.content}\n\nFocus Project: {project_name}"
    if year:
        context_text += f"\nYear: {year}"

    prompt = f"""
    You are a Technical Resume Writer.
    Based on the resume context below, generate a detailed draft for the project '{project_name}'.
    
    Output Format: MUST be Markdown with YAML Frontmatter.
    Language: Japanese.
    
    Structure:
    ---
    project: {project_name}
    year: {year if year else "Unknown"}
    tech_stack:
      - (Extracted Technology 1)
      - (Extracted Technology 2)
    ---
    
    # Situation
    (Describe the background, team size, and high-level goal. Infer reasonable details if missing but mark them as [要確認].)
    
    # Task
    (Describe your specific role and the technical challenges.)
    
    # Action
    (Detail the technical actions taken. Architecture decisions, specific libraries used, optimization techniques, etc.)
    
    # Result
    (Quantitative and qualitative results. Impact on the business or system performance.)
    
    Context:
    {context_text}
    """

    # Initialize Client directly
    # Using factory static method
    try:
        client = LLMClientFactory.create_client(
            agent_name=AgentName.RECRUITER, # Use Recruiter or similar capability for drafting
            gemini_api_key=config.get_gemini_api_key(),
            anthropic_api_key=config.get_anthropic_api_key(),
            openai_api_key=config.get_openai_api_key()
        )
    except Exception as e:
        click.echo(f"Error creating LLM client: {e}", err=True)
        return
    
    click.echo(f"Generating draft for '{project_name}'...")
    
    try:
        response = await client.generate_async(
            system_prompt="You are a helpful expert technical writer.",
            user_prompt=prompt,
            max_tokens=2000
        )
        content = response.content
        
        # Clean up markdown block if present
        # Handle various code block formats
        lines = content.split('\n')
        if lines and lines[0].strip().startswith("```"):
            # Remove first line (code block start)
            lines = lines[1:]
            # Remove last line if it's code block end
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
        
        content = "\n".join(lines).strip()
        
        # Ensure Frontmatter starts with ---
        if not content.startswith("---"):
            if content.startswith("project:"): # Heuristic: looks like YAML
                content = "---\n" + content
        
        # Ensure Frontmatter ends with ---
        # The prompt asks for it, but let's be safe. 
        # Actually, let's rely on the prompt but just fix the start.
        
        # Save file
        # Create slug
        slug = project_name.lower().replace(" ", "-").replace("/", "-")
        # naive slugify for japanse might leave it as is or huge string. 
        # Let's use a simple heuristic or keep it simple.
        # Ideally we use a library but let's just sanitise path chars.
        import re
        safe_name = re.sub(r'[\\/*?:"<>|]', "", project_name)
        safe_name = safe_name.replace(" ", "_")
        
        filename = f"{year if year else 'draft'}-{safe_name}.md"
        output_path = output_dir / filename
        
        # Ensure dir exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        click.echo(f"Draft saved to: {output_path}")
        click.echo("Please edit this file to add more details before requesting feedback.")

    except Exception as e:
        click.echo(f"Error generating draft: {e}", err=True)

def run_draft_command(
    input_file: Path,
    project_name: str,
    year: Optional[int],
    output_dir: Path,
    verbose: bool
):
    """
    Generates a draft experience file.
    """
    asyncio.run(_run_draft_logic(input_file, project_name, year, output_dir, verbose))
