from typing import Dict, Any, List
import json
import logging

from ..config.model_config import AgentName
from ..services.llm_factory import LLMClientFactory
from .state import InterviewSessionState
from ..models.star_story import StarStory
from ..utils.parsing import extract_json

logger = logging.getLogger(__name__)

async def _get_client(state: InterviewSessionState, agent_name: AgentName):
    return LLMClientFactory.create_client(
        agent_name=agent_name,
        gemini_api_key=state.gemini_api_key,
        openai_api_key=state.openai_api_key,
        anthropic_api_key=state.anthropic_api_key,
        override_model=state.override_model,
    )

async def interview_node(state: InterviewSessionState) -> Dict[str, Any]:
    """
    Generates the next interview question based on the conversation history.
    """
    client = await _get_client(state, AgentName.RECONCILIATION_AGENT)
    
    # Construct history string
    history_text = "\n".join(state.messages) if state.messages else "No previous conversation."
    
    anachronism_note = ""
    if state.anachronisms_detected:
       anachronism_note = f"\n\nNOTE: The user previously mentioned technologies that might be anachronistic: {state.anachronisms_detected}. Please query them about this gently."

    system_prompt = f"""You are a gentle but technically rigorous interviewer helping a software engineer recall details about a past project.
    
    Current constraints:
    1. **LANGUAGE**: You must speak ONLY in **Japanese**.
    2. **STRATEGY**: Do NOT ask open-ended questions like "What did you do?". instead, **Infer** the likely technical actions, tools, or challenges based on the `Project Description` and common practices for that era/domain.
    3. **GOAL**: Present your inference to the user and ask for confirmation or correction. logic.
    4. **COMPLETENESS**: Ensure your response is complete and ends with a question mark. Do not stop mid-sentence.
    5. **CONCISENESS**: Keep your response concise (under 300 characters). Avoid overly long preambles.
    
    Context:
    Project Description: {state.resume_context}
    Target Year: {state.target_year if state.target_year else "Unknown"}
    
    Your goal is to help them flesh out the 'Action' and 'Result' parts of a STAR story.
    
    Example of desired behavior:
    "2024年のTVOD構築なら、高負荷予測でGo言語を採用されたのではありませんか？"
    
    Current Conversation History:
    {history_text}
    {anachronism_note}
    
    Output only the next response (Inference + Confirmation question). Do not output anything else.
    """
    
    response = await client.generate_async(
        system_prompt=system_prompt,
        user_prompt="Based on the context, infer the next likely technical detail and ask for confirmation in Japanese. Verify the sentence is complete.",
        max_tokens=2048
    )
    
    # Add question to messages
    return {
        "messages": [f"Agent: {response.content}"],
        "current_question": response.content,
        "turn_count": state.turn_count + 1
    }

async def fact_check_node(state: InterviewSessionState) -> Dict[str, Any]:
    """
    Checks the user's latest response for anachronisms.
    """
    if not state.messages or not state.target_year:
        return {}
    
    # Check only the last user message
    last_message = state.messages[-1]
    if last_message.startswith("Agent:"):
        return {} # Only check user messages
        
    client = await _get_client(state, AgentName.RECONCILIATION_AGENT) # Use a smarter model for fact checking? Or RECONCILIATION? Let's use RECONCILIATION for now or COPYWRITER (Claude).
    # Actually, model_config maps RECONCILIATION to Gemini Flash. For deep knowledge, maybe Claude or GPT-4o is better.
    # Let's stick to RECONCILIATION agent for now for simplicity, unless we want to define a generic fact checker role.
    
    system_prompt = f"""You are a Technology Historian. 
    Your job is to verify if the technologies mentioned in the text were available and commonly used in the year {state.target_year}.
    
    Text to check:
    "{last_message}"
    
    If you find a clear anachronism (e.g. using React Hooks in 2016, or Next.js 13 in 2020), output a JSON object with:
    {{
        "detected": true,
        "reason": "React Hooks were introduced in Feb 2019 (v16.8), but the year is 2016." (Write this reason in Japanese)
    }}
    
    If no anachronism, output:
    {{
        "detected": false
    }}
    
    Output ONLY valid JSON.
    """
    
    try:
        response = await client.generate_async(
            system_prompt="You are a JSON-speaking technology historian.",
            user_prompt=system_prompt,
            max_tokens=200
        )
        data = extract_json(response.content)
        
        if data and isinstance(data, dict) and data.get("detected"):
            return {"anachronisms_detected": [data["reason"]]}
            
    except Exception as e:
        logger.warning(f"Fact check failed: {e}")
        
    return {}

async def star_generator_node(state: InterviewSessionState) -> Dict[str, Any]:
    """
    Attempts to generate a STAR story from the conversation.
    """
    client = await _get_client(state, AgentName.RECONCILIATION_AGENT)
    
    history_text = "\n".join(state.messages)
    
    # Check if we should force completion based on turn count
    MAX_TURNS = 5 # Increased to 5 per user request
    force_completion = state.turn_count >= MAX_TURNS or getattr(state, "force_terminate", False)
    
    completion_instruction = ""
    if force_completion:
        completion_instruction = """
        IMPORTANT: This is the final turn. You MUST output a JSON object with the best STAR story you can construct from the available information.
        Do NOT return empty JSON. If specific details (like specific metrics in Result) are missing, infer reasonable placeholders or write "Details to be confirmed".
        Your priority is to close the interview loop.
        """
    else:
        completion_instruction = """
        If the information is NOT sufficient yet (e.g. Result is missing or vague), output empty JSON:
        {}
        """
    
    system_prompt = f"""You are a Resume Expert.
    Analyze the conversation below and try to extract a complete STAR (Situation, Task, Action, Result) story.
    
    Context:
    {state.resume_context}
    Year: {state.target_year}
    
    Conversation:
    {history_text}
    
    If the information is sufficient to build a STRONG STAR story (especially Action and Result), output a JSON object matching this schema.
    IMPORTANT: All text fields (situation, task, action, result, project_name) MUST be in **Japanese**.
    
    {{
        "situation": "...",
        "task": "...",
        "action": "...",
        "result": "...",
        "tech_stack": ["..."],
        "year": {state.target_year or "null"},
        "project_name": "..."
    }}
    
    {completion_instruction}
    
    Output ONLY valid JSON.
    """
    
    try:
        response = await client.generate_async(
            system_prompt="You are a JSON-speaking resume expert.",
            user_prompt=system_prompt,
            max_tokens=1000
        )
        
        data = extract_json(response.content)
        
        if data and isinstance(data, dict):
            # If we are forcing completion, we accept whatever we get as long as it has some content
            if force_completion or (data.get("situation") and data.get("result")):
                story = StarStory(**data)
                return {"generated_star": story, "is_complete": True}
        else:
            # If we requested JSON but didn't get it, it might be due to content filter or model refusal or just bad output
            logger.debug(f"STAR generation returned no valid JSON. Content: {response.content[:100]}...")
            
    except Exception as e:
        logger.warning(f"STAR generation failed: {e}")
    
    # Fallback for forced completion if JSON parsing failed or exception occurred
    if force_completion:
        logger.warning("Forcing completion with placeholder due to failure in final turn.")
        return {
            "generated_star": StarStory(
                situation="（会話から抽出できませんでした）",
                task="（会話から抽出できませんでした）",
                action="（会話から抽出できませんでした）",
                result="（会話から抽出できませんでした）",
                tech_stack=[],
                year=state.target_year,
                project_name="Unknown"
            ),
            "is_complete": True
        }
        
    return {}
