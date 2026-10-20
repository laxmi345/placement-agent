import os
import sys
import re
import json
import requests
from dotenv import load_dotenv
from pypdf import PdfReader

# Load .env configuration
load_dotenv()

# Force UTF-8 on Windows terminal to prevent cp1252 encoding crashes
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


def read_resume(pdf_path: str) -> str:
    """Extract text from a resume PDF."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Resume file not found at: {pdf_path}")
    
    reader = PdfReader(pdf_path)
    text_content = []
    for idx, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            text_content.append(page_text.strip())
            
    full_text = "\n\n".join(text_content)
    if not full_text.strip():
        raise ValueError(f"Could not extract readable text from '{pdf_path}'. Ensure it's not a scanned image PDF.")
    return full_text


def clean_html(raw_html: str) -> str:
    """Strip HTML tags and convert entities for clean job description text."""
    if not raw_html:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw_html)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", " ", text).strip()


def search_jobs(query: str, limit: int = 5, region: str = "India", **kwargs) -> list:
    """Fetch live jobs targeting India (via JobSpy / Indeed India) or Worldwide Remote (Remotive/RemoteOK)."""
    jobs = []
    
    # Mode 1: Search India-specific Jobs (Naukri/Indeed India/LinkedIn via JobSpy)
    if "india" in region.lower():
        try:
            from jobspy import scrape_jobs
            print(f"[*] Querying live Indian job boards (Indeed India / LinkedIn) for '{query}'...")
            df = scrape_jobs(
                site_name=["indeed", "linkedin"],
                search_term=query,
                location="India",
                results_wanted=limit,
                country_indeed="india"
            )
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    desc = str(row.get("description") or "")
                    if len(desc.strip()) < 100:
                        continue
                    jobs.append({
                        "id": str(row.get("id", "")),
                        "title": str(row.get("title", "Role")),
                        "company": str(row.get("company", "Company")),
                        "url": str(row.get("job_url", "")),
                        "category": str(row.get("site", "India Job Board")),
                        "job_type": str(row.get("job_type", "Full-time")),
                        "candidate_required_location": str(row.get("location", "India")),
                        "description": clean_html(desc)[:4500]
                    })
                    if len(jobs) >= limit:
                        break
        except Exception as e:
            print(f"[!] Info: JobSpy India search note ({e}). Falling back to global feeds.")

    # Mode 2: Fetch from Remotive / RemoteOK (Strictly filter for Worldwide / India friendly)
    if len(jobs) < limit:
        needed = limit - len(jobs)
        # Check Remotive
        try:
            url = "https://remotive.com/api/remote-jobs"
            params = {"search": query, "limit": 25}
            headers = {"User-Agent": "AIPlacementAgent/1.0"}
            response = requests.get(url, params=params, headers=headers, timeout=20)
            if response.status_code == 200:
                raw_jobs = response.json().get("jobs", [])
                for j in raw_jobs:
                    loc = (j.get("candidate_required_location") or "").lower()
                    # Filter OUT US-only / Americas-only jobs if looking for India
                    if any(us_tag in loc for us_tag in ["usa only", "us only", "americas only", "latin america"]):
                        continue
                    # Accept Worldwide, Anywhere, India, APAC, or no restriction
                    if any(ok_tag in loc for ok_tag in ["worldwide", "anywhere", "india", "apac", "global"]) or not loc:
                        jobs.append({
                            "id": j.get("id"),
                            "title": j.get("title", "Untitled Role"),
                            "company": j.get("company_name", "Unknown Company"),
                            "url": j.get("url", ""),
                            "category": j.get("category", "Remote"),
                            "job_type": j.get("job_type", "Full-time"),
                            "candidate_required_location": j.get("candidate_required_location", "Worldwide Remote"),
                            "description": clean_html(j.get("description", ""))[:4500]
                        })
                        if len(jobs) >= limit:
                            break
        except Exception as e:
            print(f"[!] Warning: Remotive query failed: {e}")

    # Fallback to RemoteOK if still needed
    if len(jobs) < limit:
        try:
            r = requests.get("https://remoteok.com/api", headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            if r.status_code == 200:
                r_jobs = r.json()
                for j in r_jobs[1:]:
                    pos = str(j.get("position", "")).lower()
                    desc = str(j.get("description", "")).lower()
                    loc = str(j.get("location", "")).lower()
                    if query.lower() in pos or query.lower() in desc:
                        if "usa only" not in loc and "us only" not in loc:
                            jobs.append({
                                "id": j.get("id"),
                                "title": j.get("position", "Untitled"),
                                "company": j.get("company", "Company"),
                                "url": j.get("url", "https://remoteok.com"),
                                "category": "Remote Tech",
                                "job_type": "Full-time",
                                "candidate_required_location": j.get("location") or "Worldwide Remote",
                                "description": clean_html(j.get("description", ""))[:4500]
                            })
                            if len(jobs) >= limit:
                                break
        except Exception:
            pass

    return jobs[:limit]



import time

def call_llm_json(prompt: str) -> dict:
    """Call Google Gemini (or Claude fallback) with retries and parse JSON output."""
    # 1. Primary Provider: Google Gemini
    if GEMINI_API_KEY:
        candidate_models = [GEMINI_MODEL, "gemini-3.1-flash-lite", "gemini-flash-latest"]
        # Remove duplicates while preserving order
        candidate_models = list(dict.fromkeys(candidate_models))
        
        last_error = None
        for model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [
                    {
                        "parts": [{"text": prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json"
                }
            }
            
            # Retry loop for transient 503 / 429
            for attempt in range(3):
                try:
                    resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
                    if resp.status_code in (503, 429):
                        time.sleep(2 * (attempt + 1))
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise RuntimeError(f"No response generated by Gemini: {data}")
                    raw_text = candidates[0]["content"]["parts"][0]["text"].strip()
                    
                    cleaned = re.sub(r"^```(json)?\s*", "", raw_text, flags=re.MULTILINE)
                    cleaned = re.sub(r"```\s*$", "", cleaned, flags=re.MULTILINE).strip()
                    return json.loads(cleaned)
                except Exception as e:
                    last_error = e
                    if attempt < 2:
                        time.sleep(1.5)
                        
        raise RuntimeError(f"Gemini API failed after model fallbacks: {last_error}")

    # 2. Fallback Provider: Anthropic Claude
    elif ANTHROPIC_API_KEY:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = resp.content[0].text.strip()
        cleaned = re.sub(r"^```(json)?\s*", "", raw_text, flags=re.MULTILINE)
        cleaned = re.sub(r"```\s*$", "", cleaned, flags=re.MULTILINE).strip()
        return json.loads(cleaned)

    else:
        raise ValueError("Neither GEMINI_API_KEY nor ANTHROPIC_API_KEY found in .env or environment!")


def analyze_job(resume_text: str, job: dict) -> dict:
    """Compare candidate resume with a specific job posting."""
    prompt = f"""You are an elite AI Placement Specialist and ATS Matching Agent.
Analyze how well the candidate's resume fits the target job description.

CANDIDATE RESUME:
{resume_text[:6000]}

JOB ROLE: {job['title']} at {job['company']}
LOCATION: {job.get('candidate_required_location', 'Remote')}
JOB DESCRIPTION:
{job['description']}

Provide an objective, ATS-accurate evaluation.
Return ONLY a valid JSON object with the following exact keys:
{{
  "match_score": <integer between 0 and 100 based on core hard skills, relevant tech stack, and experience alignment>,
  "match_level": "<High (>=75%) | Moderate (50-74%) | Low (<50%)>",
  "matched_skills": [<list of specific skills/tools the candidate definitely possesses that match this job>],
  "skill_gaps": [<list of crucial skills or qualifications requested in the job that are missing or weak in the resume>],
  "gap_plan": "<concrete 1-sentence action plan explaining how the candidate can bridge the top gap (e.g. project to build or certification)>",
  "application_message": "<a tailored, punchy, cold email/application note (under 120 words). Highlight candidate's exact matching achievements from resume. Sound confident and human, NOT generic AI boilerplate.>"
}}
"""
    return call_llm_json(prompt)


def run_placement_pipeline(goal: str = "data analyst", resume_path: str = "resume.pdf", limit: int = 5, region: str = "India"):
    """Orchestrate end-to-end placement workflow."""
    print("=" * 65)
    print("🤖 AI PLACEMENT AGENT - AUTONOMOUS JOB MATCHING PIPELINE")
    print("=" * 65)
    print(f"[+] Target Role/Goal : {goal}")
    print(f"[+] Target Region    : {region}")
    print(f"[+] Candidate Resume : {resume_path}")
    print(f"[+] Job Search Limit : {limit}")
    
    # 1. Parse Resume
    print("\n[Step 1/4] Reading candidate resume...")
    resume_text = read_resume(resume_path)
    print(f"  ✓ Resume parsed successfully ({len(resume_text)} characters)")

    # 2. Search Live Jobs
    print(f"\n[Step 2/4] Searching live job openings for '{goal}' in '{region}'...")
    jobs = search_jobs(goal, limit=limit, region=region)
    if not jobs:
        print("  ✗ No jobs found for query. Try broader keywords like 'data', 'developer', or 'analyst'.")
        return []
    print(f"  ✓ Found {len(jobs)} active opportunities.")

    # 3. Analyze & Match with LLM
    print("\n[Step 3/4] Running ATS Match & Skill-Gap Analysis with LLM Agent...")
    results = []
    for idx, job in enumerate(jobs, 1):
        print(f"  [{idx}/{len(jobs)}] Analyzing: {job['title']} @ {job['company']}...", end=" ", flush=True)
        try:
            analysis = analyze_job(resume_text, job)
            score = analysis.get("match_score", 0)
            level = analysis.get("match_level", "Moderate")
            print(f"-> Match: {score}% ({level})")
            results.append({**job, **analysis})
        except Exception as e:
            print(f"-> Failed: {e}")

    # Rank results descending by match score
    results.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    # 4. Save Markdown Report
    print("\n[Step 4/4] Generating Placement Intelligence Report (report.md)...")
    report_file = "report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"# 🎯 AI Placement Intelligence Report\n\n")
        f.write(f"- **Target Goal:** `{goal}`\n")
        f.write(f"- **Target Region:** `{region}`\n")
        f.write(f"- **Candidate Resume:** `{os.path.basename(resume_path)}`\n")
        f.write(f"- **Jobs Scanned:** {len(results)}\n")
        f.write(f"- **Generated By:** Autonomous AI Placement Agent\n\n")
        f.write("---\n\n")

        for idx, r in enumerate(results, 1):
            score = r.get("match_score", 0)
            f.write(f"### {idx}. {r['title']} — {r['company']}\n\n")
            f.write(f"- 📊 **Match Score:** **{score}%** ({r.get('match_level', 'N/A')})\n")
            f.write(f"- 📍 **Location:** {r.get('candidate_required_location', 'Remote')}\n")
            f.write(f"- 🔗 **Apply Link:** [{r['url']}]({r['url']})\n\n")

            matched = ", ".join(f"`{s}`" for s in r.get("matched_skills", [])) or "None identified"
            gaps = ", ".join(f"`{s}`" for s in r.get("skill_gaps", [])) or "None detected"

            f.write(f"**✅ Matched Skills:** {matched}\n\n")
            f.write(f"**⚠️ Missing Skill Gaps:** {gaps}\n\n")
            f.write(f"**💡 Action Plan to Bridge Gap:**\n> {r.get('gap_plan', 'Keep practicing core requirements.')}\n\n")
            f.write(f"**✉️ Cold Application Message:**\n```text\n{r.get('application_message', '')}\n```\n\n")
            f.write("---\n\n")

    print(f"  ✓ Comprehensive report saved to: {report_file}")
    print("\n[🎉] Pipeline execution finished successfully!")
    return results


if __name__ == "__main__":
    target_goal = sys.argv[1] if len(sys.argv) > 1 else "data analyst"
    target_resume = sys.argv[2] if len(sys.argv) > 2 else "resume.pdf"
    search_limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    target_region = sys.argv[4] if len(sys.argv) > 4 else "India"
    
    run_placement_pipeline(goal=target_goal, resume_path=target_resume, limit=search_limit, region=target_region)

