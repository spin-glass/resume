import asyncio
import click
from pathlib import Path
from typing import Optional

from ..reconciliation.graph import build_reconciliation_workflow
from ..reconciliation.state import InterviewSessionState
from ..services.qmd_parser import QMDParser
from ..utils.config import get_config, setup_logging

def robust_input(prompt: str = "") -> str:
    """
    Reads input from stdin, attempting to handle UnicodeDecodeErrors gracefully.
    Falls back to raw buffer reading/decoding if the standard input() fails.
    """
    import sys
    
    # Try standard input() first to support line editing (arrow keys)
    try:
        return input(prompt)
    except EOFError:
        raise
    except UnicodeDecodeError:
        # Fallback to reading raw bytes and decoding with error replacement
        # This loses line editing but prevents the crash
        print("\n[Warning] Input encoding error detected. Switching to raw input mode (line editing disabled for this line).", file=sys.stderr)
        try:
            line_bytes = sys.stdin.buffer.readline()
            return line_bytes.decode('utf-8', errors='replace').strip()
        except Exception:
            return ""
    except KeyboardInterrupt:
        raise

def run_reconcile_command(
    input_file: Path,
    project_name: str,
    target_year: Optional[int],
    gemini_api_key: Optional[str],
    openai_api_key: Optional[str],
    anthropic_api_key: Optional[str],
    verbose: bool
):
    """
    Orchestrates the interactive reconciliation session.
    """
    logger = setup_logging(verbose=verbose)
    
    # Load resume
    try:
        parser = QMDParser()
        resume = parser.load_resume(input_file)
        # For simplicity, we just use the whole resume or would search for the project.
        # Ideally we parse out the specific project section.
        # For this prototype, we pass the parsed text but let the agent know we focus on 'project_name'.
        
        context = f"Full Resume:\n{resume.content}\n\nFocus Project: {project_name}"
        
    except Exception as e:
        click.echo(f"Error loading resume: {e}", err=True)
        return

    # Initialize State
    config = get_config()
    state = InterviewSessionState(
        resume_context=context,
        target_year=target_year,
        gemini_api_key=gemini_api_key or config.get_gemini_api_key(),
        openai_api_key=openai_api_key or config.get_openai_api_key(),
        anthropic_api_key=anthropic_api_key or config.get_anthropic_api_key(),
    )
    
    workflow = build_reconciliation_workflow()
    
    click.echo(f"Starting reconciliation interview for '{project_name}' ({target_year or 'Unknown Year'})...")
    click.echo("Type 'exit' to quit.\n")
    
    async def _loop():
        current_state = state
        while True:
            click.echo("Thinking...", err=True)
            
            result = await workflow.ainvoke(current_state)
            current_state = result
            
            # Update local state reference with result
            if isinstance(result, dict):
                current_state_dict = result
            else:
                current_state_dict = result.model_dump()

            if current_state_dict.get("is_complete"):
                star = current_state_dict.get("generated_star")
                click.echo("\n\n=== GENERATED STAR STORY ===\n")
                if star:
                    click.echo(f"Situation: {star.situation}")
                    click.echo(f"Task:      {star.task}")
                    click.echo(f"Action:    {star.action}")
                    click.echo(f"Result:    {star.result}")
                    click.echo(f"Tech:      {', '.join(star.tech_stack)}")
                else:
                    click.echo("Failed to generate STAR story.")
                break

            # Get latest agent message
            # Handle both dict and Pydantic object
            # Get latest agent message
            # Handle both dict and Pydantic object
            if isinstance(current_state, dict):
                messages = current_state.get("messages", [])
            else:
                messages = getattr(current_state, "messages", [])
                
            if not messages:
                # Should not happen if interview node runs
                click.echo("Agent did not return a message.")
                break
                
            last_agent_msg = messages[-1]
            click.echo(f"\n{last_agent_msg}\n")
            
            # User Input
            try:
                user_response = robust_input("You: ")
            except (EOFError, KeyboardInterrupt):
                break

            if not user_response.strip():
              user_response = robust_input("You: ")
            
            if user_response.lower() in ["exit", "quit", "q"]:
                break
            
            # Manual termination command
            if user_response.lower() in ["finish", "done", "完了"]:
                click.echo("Finishing interview manually...", err=True)
                # We need to update the state to trigger force_completion
                # Depending on how the state object is managed
                if isinstance(current_state, dict):
                    current_state["force_terminate"] = True
                    current_state["user_answer"] = "（ユーザーによる強制終了）" # Ensure we have something
                    messages = current_state.get("messages", [])
                    messages.append(f"Result: {user_response}") # Add to history
                else:
                    # Assuming Pydantic model
                    current_state.force_terminate = True
                    current_state.user_answer = "（ユーザーによる強制終了）"
                    current_state.messages.append(f"Result: {user_response}")
            else:
                # Normal flow
                # Add user answer to state
                if isinstance(current_state, dict):
                    messages = current_state.get("messages", [])
                    messages.append(f"Result: {user_response}")
                    current_state["messages"] = messages
                    current_state["user_answer"] = user_response
                else:
                    current_state.messages.append(f"Result: {user_response}")
                    current_state.user_answer = user_response
            
            # Update state for next turn
            # Convert Pydantic model to dict for modification if needed
            if hasattr(current_state, "model_dump"):
                 current_state_dict = current_state.model_dump()
            elif hasattr(current_state, "dict"):
                 current_state_dict = current_state.dict()
            else:
                 current_state_dict = dict(current_state)
            
            # Append user message
            current_state_dict["messages"].append(f"User: {user_response}")
            current_state = current_state_dict

            # Run next step
            try:
                click.echo("\nThinking...", err=True)
                current_state = await workflow.ainvoke(current_state)
            except Exception as e:
                click.echo(f"Error during agent execution: {e}", err=True)
                break

    asyncio.run(_loop())
