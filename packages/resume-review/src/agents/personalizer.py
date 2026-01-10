"""
Personalizer agent for resume-job matching analysis.

This agent calculates match scores, identifies skill gaps, and generates
personalized recommendations for tailoring resumes to specific job postings.
"""

import json
import logging
import re

from typing import cast
from ..models.feedback import Resume
from ..models.job_posting import JobPosting, PersonalizationResult, SkillMatch
from ..services.llm_client import BaseLLMClient

logger = logging.getLogger(__name__)


class PersonalizerAgent:
    """Agent for analyzing resume-job match and generating personalization insights."""

    def __init__(self, llm_client: BaseLLMClient):
        """Initialize personalizer agent."""
        self.llm_client = llm_client
        self.agent_name = "personalizer"

    def _normalize_skill(self, skill: str) -> str:
        """Normalize skill name for comparison."""
        return skill.lower().strip()

    def _extract_skills_from_resume(self, resume: Resume) -> list[str]:
        """Extract skills from resume content using simple pattern matching."""
        content_lower = resume.content.lower()
        skills = []

        # Programming languages
        prog_langs = [
            "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go",
            "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R"
        ]
        for lang in prog_langs:
            if lang.lower() in content_lower:
                skills.append(lang)

        # Frameworks
        frameworks = [
            "React", "Vue", "Angular", "Next.js", "Django", "Flask", "FastAPI",
            "Spring", "Node.js", "Express", "TensorFlow", "PyTorch", "Pandas",
            "LangChain", "LangGraph"
        ]
        for fw in frameworks:
            if fw.lower() in content_lower:
                skills.append(fw)

        # Tools
        tools = [
            "Docker", "Kubernetes", "Git", "AWS", "Azure", "GCP", "PostgreSQL",
            "MongoDB", "Redis", "Elasticsearch", "CI/CD", "Jenkins"
        ]
        for tool in tools:
            if tool.lower() in content_lower:
                skills.append(tool)

        return list(set([s for s in skills if s]))

    async def _match_skills_with_llm(
        self,
        resume_skills: list[str],
        job_required_skills: list[str],
        job_preferred_skills: list[str],
    ) -> tuple[list[SkillMatch], list[SkillMatch]]:
        """Use LLM to perform semantic skill matching."""
        system_prompt = """You are an expert at matching resume skills to job requirements.

MATCHING RULES:
1. Exact Match: Identical terms (confidence: 1.0)
2. Synonym Match: Different terms for same skill (confidence: 0.9-0.95)
3. Related Match: Related competency (confidence: 0.7-0.8)
4. No Match: Unrelated (confidence: 0.0)

Return ONLY valid JSON."""

        user_prompt = f"""Match resume skills against job requirements.

Resume Skills: {json.dumps(resume_skills, ensure_ascii=False)}
Job Required: {json.dumps(job_required_skills, ensure_ascii=False)}
Job Preferred: {json.dumps(job_preferred_skills, ensure_ascii=False)}

Return JSON with this structure:
{{
  "required_matches": [{{"skill": "X", "matched": true, "confidence": 1.0, "explanation": "..."}}],
  "preferred_matches": [...]
}}"""

        try:
            response = await self.llm_client.generate_async(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=6000,
                temperature=0.3,
            )

            # More robust JSON extraction
            # 1. Try to find JSON inside markdown code blocks first
            code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
            if code_block_block := code_block_match:
                json_str = code_block_block.group(1).strip()
            else:
                # 2. Fallback to finding the first { and last }
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if not json_match:
                    raise ValueError("No JSON found in response")
                json_str = json_match.group().strip()

            data = json.loads(json_str)
            required_matches = [SkillMatch(**m) for m in data.get("required_matches", [])]
            preferred_matches = [SkillMatch(**m) for m in data.get("preferred_matches", [])]

            return required_matches, preferred_matches

        except Exception as e:
            logger.error(f"Error in LLM skill matching: {e}")
            # Fallback
            required_matches = [
                SkillMatch(
                    skill=skill,
                    matched=any(self._normalize_skill(skill) == self._normalize_skill(rs) for rs in resume_skills),
                    confidence=1.0 if any(self._normalize_skill(skill) == self._normalize_skill(rs) for rs in resume_skills) else 0.0,
                    explanation="Exact match" if any(self._normalize_skill(skill) == self._normalize_skill(rs) for rs in resume_skills) else "Not found"
                )
                for skill in job_required_skills
            ]
            preferred_matches = [
                SkillMatch(
                    skill=skill,
                    matched=any(self._normalize_skill(skill) == self._normalize_skill(rs) for rs in resume_skills),
                    confidence=1.0 if any(self._normalize_skill(skill) == self._normalize_skill(rs) for rs in resume_skills) else 0.0,
                    explanation="Exact match" if any(self._normalize_skill(skill) == self._normalize_skill(rs) for rs in resume_skills) else "Not found"
                )
                for skill in job_preferred_skills
            ]
            return required_matches, preferred_matches

    def _calculate_match_scores(
        self,
        required_matches: list[SkillMatch],
        preferred_matches: list[SkillMatch],
    ) -> tuple[float, float]:
        """Calculate match scores as percentages."""
        if required_matches:
            required_points = sum(m.confidence for m in required_matches if m.matched)
            required_score = (required_points / len(required_matches)) * 100
        else:
            required_score = 100.0

        if preferred_matches:
            preferred_points = sum(m.confidence for m in preferred_matches if m.matched)
            preferred_score = (preferred_points / len(preferred_matches)) * 100
        else:
            preferred_score = 100.0

        return round(required_score, 1), round(preferred_score, 1)

    async def _generate_emphasis_suggestions(
        self,
        job_posting: JobPosting,
        matched_skills: list[SkillMatch],
        missing_skills: list[str],
    ) -> list[str]:
        """Generate prioritized emphasis suggestions using LLM."""
        system_prompt = """You are an expert resume consultant specializing in ATS optimization.
Generate 3-5 actionable emphasis suggestions for resume improvement based on job requirements.

Priority levels (use emoji prefix):
- 🔴 Critical: Missing required skills, major gaps in key responsibilities
- 🟡 Important: Underemphasized matched skills, quantification opportunities
- 🟢 Enhancement: Polish, additional details, nice-to-have improvements

Requirements:
- Focus on highlighting matched skills more prominently
- Suggest addressing missing required skills (if any)
- Recommend quantifying relevant achievements
- Prioritize suggestions by impact (critical → important → enhancement)
- Be specific and actionable

Return ONLY a JSON array of strings with priority emoji prefix:
["🔴 Critical suggestion", "🟡 Important suggestion", "🟢 Enhancement", ...]"""

        matched_list = [m.skill for m in matched_skills if m.matched and m.confidence >= 0.8][:8]
        missing_list = missing_skills[:5]

        responsibilities = job_posting.responsibilities[:5] if job_posting.responsibilities else []

        user_prompt = f"""Job Title: {job_posting.title}
Matched Skills: {matched_list}
Missing Required Skills: {missing_list}

Key Responsibilities:
{chr(10).join([f"- {r}" for r in responsibilities])}

Generate 3-5 prioritized emphasis suggestions."""

        try:
            response = await self.llm_client.generate_async(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=2000,
                temperature=0.7,
            )

            # More robust JSON extraction
            # 1. Try to find JSON inside markdown code blocks first
            code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
            if code_block_block := code_block_match:
                json_str = code_block_block.group(1).strip()
            else:
                # 2. Fallback to finding the first { and last }
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if not json_match:
                    raise ValueError("No JSON found in response")
                json_str = json_match.group().strip()

            suggestions = json.loads(json_str.strip())

            # Sort by priority (🔴 > 🟡 > 🟢)
            priority_order = {"🔴": 0, "🟡": 1, "🟢": 2}
            suggestions.sort(key=lambda s: priority_order.get(s[0] if s else "x", 3))

            return cast(list[str], suggestions[:5])

        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return [
                "🔴 Emphasize experience with matched technologies",
                "🟡 Quantify achievements related to job responsibilities",
                "🟢 Add examples demonstrating required competencies",
            ]

    async def _generate_keyword_additions(self, job_posting: JobPosting) -> list[str]:
        """Generate bilingual keyword suggestions using LLM."""
        system_prompt = """You are an ATS (Applicant Tracking System) optimization expert.
Generate 5-10 keyword additions for a Japanese resume based on the job description.

Requirements:
- Extract key technical terms, skills, frameworks, and methodologies
- For technical terms, provide BOTH English and Japanese translations
- Format: "English (日本語)" or "日本語 (English)"
- Prioritize terms that appear frequently in job requirements
- Focus on ATS-searchable terms (specific technologies, not vague descriptions)

Return ONLY a JSON array of bilingual keyword strings:
["Docker (コンテナ)", "Kubernetes (K8s)", "マイクロサービス (Microservices)", ...]"""

        skills = job_posting.get_all_skills()[:15]
        responsibilities = job_posting.responsibilities[:5] if job_posting.responsibilities else []

        user_prompt = f"""Job Title: {job_posting.title}

Skills: {', '.join(skills)}

Responsibilities:
{chr(10).join([f"- {r}" for r in responsibilities])}

Generate 5-10 bilingual ATS keywords."""

        try:
            response = await self.llm_client.generate_async(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1500,
                temperature=0.5,
            )

            # More robust JSON extraction
            # 1. Try to find JSON inside markdown code blocks first
            code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
            if code_block_block := code_block_match:
                json_str = code_block_block.group(1).strip()
            else:
                # 2. Fallback to finding the first { and last }
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if not json_match:
                    raise ValueError("No JSON found in response")
                json_str = json_match.group().strip()

            keywords = json.loads(json_str.strip())

            # Deduplicate and limit to 10
            return list(set(keywords))[:10]

        except Exception as e:
            logger.error(f"Error generating keywords: {e}")
            # Fallback: extract unique skills
            return list(set(job_posting.get_all_skills()))[:10]

    async def analyze_match(
        self,
        resume: Resume,
        job_posting: JobPosting,
    ) -> PersonalizationResult:
        """Perform complete match analysis."""
        logger.info(f"Analyzing resume match for: {job_posting.title}")

        resume_skills = self._extract_skills_from_resume(resume)
        logger.info(f"Extracted {len(resume_skills)} skills from resume")

        required_matches, preferred_matches = await self._match_skills_with_llm(
            resume_skills, job_posting.required_skills, job_posting.preferred_skills
        )

        required_score, preferred_score = self._calculate_match_scores(
            required_matches, preferred_matches
        )

        missing_required = [m.skill for m in required_matches if not m.matched]
        missing_preferred = [m.skill for m in preferred_matches if not m.matched]

        emphasis_suggestions = await self._generate_emphasis_suggestions(
            job_posting, required_matches + preferred_matches, missing_required
        )

        keyword_additions = await self._generate_keyword_additions(job_posting)

        result = PersonalizationResult(
            required_match_score=required_score,
            preferred_match_score=preferred_score,
            matched_required_skills=[m for m in required_matches if m.matched],
            matched_preferred_skills=[m for m in preferred_matches if m.matched],
            missing_required_skills=missing_required,
            missing_preferred_skills=missing_preferred,
            emphasis_suggestions=emphasis_suggestions,
            keyword_additions=keyword_additions,
        )

        logger.info(f"Match analysis complete: {result.match_score:.1f}% ({result.match_level})")

        return result
