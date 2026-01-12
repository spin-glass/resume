import re
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import frontmatter
from ..config.model_config import AgentName
from ..services.llm_factory import LLMClientFactory
from ..services.qmd_parser import QMDParser

logger = logging.getLogger(__name__)

class ExperienceIntegrator:
    def __init__(self, 
                 gemini_api_key: Optional[str] = None,
                 openai_api_key: Optional[str] = None,
                 anthropic_api_key: Optional[str] = None,
                 verbose: bool = False):
        self.gemini_api_key = gemini_api_key
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key
        self.client = LLMClientFactory.create_client(
            agent_name=AgentName.TECHNICAL_WRITER, # Use Technical Writer for summarization
            gemini_api_key=gemini_api_key,
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key
        )

    async def integrate_all(self, resume_path: Path, experiences_dir: Path) -> Path:
        """
        Integrates all experience files from the directory into the resume.
        Returns the path to the updated resume (backup created).
        """
        parser = QMDParser()
        resume = parser.load_resume(resume_path)
        content = resume.content
        
        # Load all experience files
        exp_files = list(experiences_dir.glob("*.md"))
        logger.info(f"Found {len(exp_files)} experience files.")

        updated_content = content
        
        for exp_file in exp_files:
            if exp_file.name.endswith("_feedback.md"):
                continue
                
            try:
                with open(exp_file, "r", encoding="utf-8") as f:
                    post = frontmatter.load(f)
                    project_name = post.metadata.get("project")
                    
                    if not project_name:
                        logger.warning(f"Skipping {exp_file.name}: No 'project' metadata found.")
                        continue
                        
                    logger.info(f"Processing project: {project_name}")
                    
                    # 1. Generate Resume Content from Experience File
                    new_section_content = await self._generate_resume_content(post.content, post.metadata)
                    
                    # 2. Replace in QMD
                    updated_content = self._replace_project_content(updated_content, project_name, new_section_content)
                    
            except Exception as e:
                logger.error(f"Failed to process {exp_file.name}: {e}")

        # Save result
        resume.content = updated_content
        parser.save_resume(resume, create_backup=True)
        return resume.file_path

    async def _generate_resume_content(self, detail_content: str, metadata: Dict[str, Any]) -> str:
        """
        Uses LLM to summarize detailed content into resume format.
        """
        tech_stack = ", ".join(metadata.get("tech_stack", []))
        
        system_prompt = """You are a Skilled Technical Resume Writer.
        Your task is to take a detailed project description (STAR format) and convert it into a concise, high-impact resume entry in Japanese.
        
        Format Requirements:
        - Use a Markdown list structure.
        - The first line MUST be the project title line formatted as: `- **{project_name}**`
        - Followed by specific fields: 期間, 概要, 担当, 環境・手法.
        - Then a `詳細:` or `成果:` section with bullet points using the STAR details.
        - Focus on quantitative results and specific technologies using the Action/Result information provided.
        - Keep it consistent with standard Japanese resume formats (see example).
        
        Example Output Format:
        - **Project Name**
          - 期間: 2023/01 - 2023/12
          - 概要: Project Summary...
          - 担当: Role...
          - 環境・手法: Python, AWS...
          - 詳細:
            - **Quantitative Result**: Achieved X% improvement...
            - **Technical Challenge**: Solved Y using Z...
        
        """
        
        user_prompt = f"""
        Project Name: {metadata.get('project')}
        Tech Stack: {tech_stack}
        
        Detailed Description:
        {detail_content}
        
        Generate the resume entry. Ensure the project title line matches `- **{metadata.get('project')}**` exactly so I can replace it easily.
        """
        
        response = await self.client.generate_async(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1000
        )
        content = response.content.strip()
        
        # Clean up potential JSON formatting artifacts
        if content.startswith("```"):
            # Remove code blocks
            content = re.sub(r"^```\w*\n", "", content)
            content = re.sub(r"\n```$", "", content)
            content = content.strip()
            
        # If it looks like a JSON string value (starting with quote or brace)
        # Check if the content is wrapped in braces (common with forced JSON mode artifacts)
        if content.startswith('{') and content.endswith('}'):
             # Naively strip braces. We assume the content inside is the text we want.
             # This handles cases where the model outputs {"key": "content"} or just {"content"}
             # But here we just want to strip the wrapper if it looks like a wrapper.
             # If it's a valid JSON with keys, we might be destroying it, but we expect Markdown.
             stripped = content[1:-1].strip()
             # If the stripped content starts with " or ', it might be a JSON string value.
             content = stripped

        # Specific fix for the " "- **Project" " pattern
        # Remove leading " or ' if followed by - **
        content = re.sub(r'^[\'"](- \*\*)', r'\1', content)


        # Specific fix for the " "- **Project" " pattern
        # Remove leading " or ' if followed by - **
        content = re.sub(r'^[\'"](- \*\*)', r'\1', content)
        # Remove trailing " or ' }
        content = re.sub(r'[\'"]\s*}?$', '', content)
        
        return content.strip()

    def _replace_project_content(self, full_text: str, project_name: str, new_content: str) -> str:
        """
        Replaces the section in full_text corresponding to project_name with new_content.
        """
        # Regex to find the start of the project section
        # Looking for `- **Project Name**`
        escaped_name = re.escape(project_name)
        pattern = re.compile(rf"-\s*\*\*{escaped_name}\*\*(.*?)(?=\n-\s*\*\*|\n###|\Z)", re.DOTALL)
        
        match = pattern.search(full_text)
        if match:
            logger.info(f"Found match for {project_name}. Replacing...")
            # We replace the whole match with new_content
            # Ensure new_content starts with the list item dash if the regex included it?
            # My prompt asks to include `- **Name**`, so we just replace the match.
            
            # Note: The regex captures from `- **Name**` up to the lookahead. 
            # So replacing the match is correct.
            return full_text.replace(match.group(0), new_content)
        else:
            logger.warning(f"Could not find section for '{project_name}' in resume text.")
            return full_text
