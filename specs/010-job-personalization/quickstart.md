# Quickstart Guide: Job Personalization

**Feature**: Job Personalization
**Version**: 1.0.0
**Created**: 2026-01-09

## Overview

The job personalization feature allows you to tailor resume review feedback to specific job postings. Instead of generic advice based on a role title (e.g., "Backend Engineer"), you get targeted suggestions based on the actual requirements, skills, and responsibilities listed in a specific job description.

**What You Get**:
- ✅ Match score (0-100%) showing how well your resume fits the job
- ✅ List of matched skills (required vs. preferred)
- ✅ Critical skill gaps that need addressing
- ✅ Emphasis suggestions (what to highlight in your resume)
- ✅ Keyword recommendations for ATS optimization
- ✅ All agent feedback contextualized to the job requirements

---

## Prerequisites

- Existing `resume-review` CLI tool installed and working
- A resume file in QMD format (e.g., `resume-ja.qmd`)
- A job posting (either as a local file or URL)

**No Additional Setup Required**: The job personalization feature uses the same LLM infrastructure as the standard review. No new API keys or dependencies are needed.

---

## Basic Usage

### Option 1: Job Posting File

If you have the job description saved as a text or Markdown file:

```bash
resume-review review \
  --input resume/resume-ja.qmd \
  --job-posting ./jobs/backend-engineer.md \
  --target-role "Backend Engineer"
```

**Supported File Formats**:
- Plain text (`.txt`)
- Markdown (`.md`)
- Any text-based format (no PDF support in v1)

**Example Job File** (`jobs/backend-engineer.md`):

```markdown
# Senior Backend Engineer

## Requirements
- 5+ years Python experience
- Experience with FastAPI or Django
- PostgreSQL or MySQL
- RESTful API design
- CI/CD (GitHub Actions, GitLab CI)

## Nice to Have
- LangGraph or LangChain experience
- Multi-agent systems
- Docker/Kubernetes
- Japanese language (N2+)

## Responsibilities
- Design and implement backend services
- Optimize API performance
- Mentor junior engineers
```

### Option 2: Job Posting URL

If the job is posted online:

```bash
resume-review review \
  --input resume/resume-ja.qmd \
  --job-url "https://example.com/careers/backend-engineer" \
  --target-role "Backend Engineer"
```

**Supported Sites**:
- Major job boards (LinkedIn, Indeed, Glassdoor)
- Company career pages with standard HTML structure
- Any publicly accessible URL (no authentication required)

**Limitations**:
- Cannot access pages requiring login
- JavaScript-heavy SPAs may not work (e.g., dynamic React apps)
- For problematic URLs, save the content to a file instead

---

## Understanding the Output

### 1. Standard Review Output

You'll see the familiar review output:

```text
=== RESUME REVIEW SUMMARY ===

Session ID: 20260109_143022

Target Role: Backend Engineer
Iterations: 1
Final Score: 8.5/10.0 ✓ (threshold: 8.0)

ITERATION 1 FEEDBACK:
...
```

### 2. Personalization Section (NEW)

After the standard feedback, you'll see the personalization analysis:

```text
=== JOB PERSONALIZATION ANALYSIS ===

Job Source: https://example.com/careers/backend-engineer
Job Title: Senior Backend Engineer
Company: Example Inc.

MATCH SCORE: 75.0% (Good)
├── Required Skills: 80.0% (4/5 matched)
└── Preferred Skills: 50.0% (2/4 matched)

✅ MATCHED REQUIRED SKILLS (4/5):
  • Python (100% confidence) - Multiple Python projects
  • FastAPI (90% confidence) - Resume mentions FastAPI in LangGraph project
  • PostgreSQL (85% confidence) - Database experience in 職務経歴
  • RESTful API design (95% confidence) - API design mentioned in projects

❌ MISSING REQUIRED SKILLS (1/5 - CRITICAL):
  • CI/CD (GitHub Actions, GitLab CI)

✅ MATCHED PREFERRED SKILLS (2/4):
  • LangGraph (100% confidence) - Resume review project
  • Japanese N2+ (80% confidence) - Native speaker

❌ MISSING PREFERRED SKILLS (2/4):
  • Docker/Kubernetes
  • Multi-agent systems (partial - mentioned but not emphasized)

💡 EMPHASIS SUGGESTIONS:
  1. Highlight FastAPI experience in your 職務経歴 section
  2. Add specific metrics for database work (e.g., "optimized queries handling 10k req/s")
  3. Mention any CI/CD experience, even if informal (e.g., GitHub Actions for personal projects)
  4. Emphasize leadership/mentoring experiences

🔑 KEYWORD ADDITIONS (for ATS optimization):
  • "パフォーマンス最適化" (performance optimization)
  • "RESTful API設計" (RESTful API design)
  • "チームリーダー" (team lead)
```

### 3. Personalized Agent Feedback

All agent feedback now references the job requirements:

**Recruiter**:
```text
Strengths:
  • Strong match for required Python and FastAPI skills ✓
  • Relevant LangGraph experience aligns with "nice to have" ✓

Issues:
  - Missing CI/CD experience (required) - consider adding GitHub Actions usage
  - Mentoring experience not clearly highlighted for "Mentor junior engineers" responsibility
```

**Technical Writer**:
```text
Recommendations:
  - Expand FastAPI section to emphasize RESTful API design patterns
  - Add database performance metrics (PostgreSQL optimization mentioned in job)
```

**Copywriter**:
```text
Suggestions:
  - Use job keywords naturally: "RESTful API設計", "パフォーマンス最適化"
  - Reframe "コードレビュー" as "チーム育成・メンタリング" to match responsibility
```

---

## Integration with Existing Options

Job personalization works seamlessly with all existing CLI options:

### Dry Run (Preview Only)

```bash
resume-review review \
  --input resume/resume-ja.qmd \
  --job-posting ./jobs/backend.md \
  --dry-run
```

**Output**: Shows personalized feedback and match score WITHOUT modifying the resume file.

### Save Iterations

```bash
resume-review review \
  --input resume/resume-ja.qmd \
  --job-posting ./jobs/backend.md \
  --save-iterations
```

**Output**: Saves personalization results in `review_*/session.json` along with standard review data.

### Verbose Mode

```bash
resume-review review \
  --input resume/resume-ja.qmd \
  --job-url "https://example.com/jobs/123" \
  --verbose
```

**Output**: Shows detailed parsing logs, skill matching confidence scores, and score calculation breakdown.

### Combined Example

```bash
resume-review review \
  --input resume/resume-ja.qmd \
  --job-posting ./jobs/backend.md \
  --dry-run \
  --save-iterations \
  --verbose
```

---

## Common Workflows

### 1. Quick Match Check

Before spending time tailoring your resume, check if you're a good match:

```bash
resume-review review \
  --input resume/resume-ja.qmd \
  --job-url "https://example.com/jobs/123" \
  --dry-run
```

**Decision Guide**:
- **80%+ match**: Excellent fit, apply with confidence
- **60-79% match**: Good fit, minor tailoring needed
- **40-59% match**: Moderate fit, significant gaps to address
- **<40% match**: Consider if this role aligns with your experience

### 2. Tailored Resume Creation

Apply personalized feedback to create a job-specific resume:

```bash
# Step 1: Run personalized review (modifies resume)
resume-review review \
  --input resume/resume-ja.qmd \
  --job-posting ./jobs/target-role.md \
  --save-iterations

# Step 2: Generate PDF/HTML
pnpm resume:build

# Step 3: Review output
open resume/output/resume-ja.pdf
```

### 3. Batch Job Analysis

Compare your resume against multiple jobs:

```bash
# Create job files
mkdir jobs
# Save job postings as: jobs/job1.md, jobs/job2.md, jobs/job3.md

# Run analysis on each (dry-run to avoid modifications)
for job in jobs/*.md; do
  echo "Analyzing: $job"
  resume-review review \
    --input resume/resume-ja.qmd \
    --job-posting "$job" \
    --dry-run \
    | grep "MATCH SCORE"
done
```

**Output**:
```text
Analyzing: jobs/job1.md
MATCH SCORE: 82.0% (Excellent)

Analyzing: jobs/job2.md
MATCH SCORE: 68.0% (Good)

Analyzing: jobs/job3.md
MATCH SCORE: 45.0% (Moderate)
```

---

## Troubleshooting

### Error: "Cannot parse job posting"

**Cause**: File is empty, invalid format, or URL returned no content.

**Solution**:
1. Check file exists and has content: `cat jobs/your-job.md`
2. For URLs, verify it's publicly accessible: `curl "https://..."`
3. Try saving URL content manually to a file

### Error: "No structured data extracted"

**Cause**: Job posting lacks clear sections (requirements, skills, etc.).

**Solution**:
1. Ensure job posting has at least one of:
   - "Requirements" or "必須スキル" section
   - "Responsibilities" or "業務内容" section
   - Clear skill list
2. If posting is pure prose, LLM will try to extract info but may fail
3. Consider manually formatting the job posting into clear sections

### Warning: "Match score may be inaccurate"

**Cause**: Job posting has very few skills listed or unusual format.

**Solution**:
- This is informational; review is still valid
- Treat match score as approximate
- Focus on the qualitative feedback from agents

### Error: "Failed to fetch URL"

**Cause**: URL requires authentication, uses heavy JavaScript, or is invalid.

**Solution**:
1. Verify URL in browser: `open "https://..."`
2. If page requires login, copy content to a file instead
3. For JavaScript-heavy pages, view source and save HTML to file
4. Use `--job-posting file.html` instead of `--job-url`

### Issue: "Match score seems wrong"

**Cause**: LLM skill matching may have false positives/negatives.

**Solution**:
1. Use `--verbose` to see confidence scores for each match
2. Review matched skills in output - are they reasonable?
3. If match is clearly wrong, the scoring algorithm can be improved
4. Match score is a guide, not absolute truth - trust agent feedback

### Error: "Cannot provide both --job-posting and --job-url"

**Cause**: Mutual exclusivity violation.

**Solution**:
- Choose one: either local file OR URL, not both
- If you have both, prefer file for reliability

---

## Tips for Best Results

### 1. Clean Job Postings

**Good** (clear structure):
```markdown
## Requirements
- Python 3.11+
- FastAPI
- PostgreSQL

## Responsibilities
- Design APIs
- Optimize queries
```

**Problematic** (prose):
```text
We're looking for someone with Python, maybe FastAPI, and definitely some database experience.
You'll be designing stuff and making things faster.
```

**Solution**: Reformat prose into bullet points before analysis.

### 2. Use Target Role Consistently

Always provide `--target-role` even with job personalization:

```bash
resume-review review \
  --input resume/resume-ja.qmd \
  --job-posting ./jobs/backend.md \
  --target-role "Backend Engineer"  # Matches job context
```

This ensures agents understand the broader role context.

### 3. Iterate on Feedback

```bash
# First pass: See what gaps exist
resume-review review --input resume.qmd --job-posting job.md --dry-run

# Edit resume manually based on emphasis suggestions

# Second pass: Apply agent improvements
resume-review review --input resume.qmd --job-posting job.md
```

### 4. Save Personalization Results

```bash
resume-review review \
  --input resume.qmd \
  --job-posting job.md \
  --save-iterations
```

Then review `review_*/session.json` for detailed match data:

```json
{
  "personalization": {
    "match_score": 75.0,
    "matched_required_skills": [...],
    "missing_required_skills": [...]
  }
}
```

---

## Performance Expectations

| Operation | Time | Cost |
|-----------|------|------|
| Parse job file | <2 seconds | $0.01 |
| Fetch job URL | 2-5 seconds | $0.02 |
| Calculate match score | 5-10 seconds | $0.03 |
| Full personalized review | <5 minutes | ~$0.70 |

**Note**: Total cost is similar to standard review (~$0.55) since job parsing/matching is inexpensive compared to full agent analysis.

---

## Next Steps

1. **Try it**: Run a personalized review on your resume with a real job posting
2. **Iterate**: Use emphasis suggestions and keyword recommendations to improve
3. **Compare**: Run multiple job analyses to find your best matches
4. **Feedback**: Report issues or suggestions to improve the feature

---

## FAQ

**Q: Does personalization work for Japanese job postings?**
A: Yes! The system handles both English and Japanese job postings.

**Q: Can I use this for freelance contracts?**
A: Yes, it works for any job type (full-time, contract, 業務委託, etc.).

**Q: Will this change my resume without asking?**
A: Only if you omit `--dry-run`. Always preview first.

**Q: What if the job has 30+ required skills?**
A: The match score will reflect reality (likely low). The system prioritizes the most frequently mentioned skills in suggestions.

**Q: Can I use this for cover letters?**
A: Not directly, but the emphasis suggestions and keyword additions are useful for cover letter content.

**Q: Does this replace manual resume tailoring?**
A: No, it augments it. Use this to identify gaps and get suggestions, but human judgment is still essential.

---

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Review verbose output: `--verbose`
3. Report bugs at: [GitHub Issues](https://github.com/your-repo/issues)
