import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import agent

# Page Setup
st.set_page_config(
    page_title="AI Placement Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished, modern UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(120deg, #2563eb, #7c3aed, #db2777);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #64748b;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .job-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
        transition: transform 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
    }
    .job-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .badge-matched {
        display: inline-block;
        background-color: #dcfce7;
        color: #15803d;
        font-weight: 600;
        font-size: 0.8rem;
        padding: 4px 10px;
        border-radius: 9999px;
        margin: 2px 4px 2px 0;
    }
    .badge-gap {
        display: inline-block;
        background-color: #fee2e2;
        color: #b91c1c;
        font-weight: 600;
        font-size: 0.8rem;
        padding: 4px 10px;
        border-radius: 9999px;
        margin: 2px 4px 2px 0;
    }
    .tag-location {
        display: inline-block;
        background-color: #f1f5f9;
        color: #475569;
        font-size: 0.8rem;
        padding: 3px 8px;
        border-radius: 6px;
        margin-right: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=500&auto=format&fit=crop&q=80", use_container_width=True)
    st.title("⚙️ Agent Controls")
    
    # API Key Handling
    env_key = os.getenv("GEMINI_API_KEY", "")
    gemini_key = st.text_input("Gemini API Key", value=env_key, type="password", help="Loaded from .env by default")
    if gemini_key:
        agent.GEMINI_API_KEY = gemini_key
        
    st.divider()
    
    # Candidate Resume Selection
    st.subheader("📄 Candidate Resume")
    default_resume_path = "resume.pdf" if os.path.exists("resume.pdf") else None
    
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    active_resume_path = None
    
    if uploaded_file is not None:
        temp_path = os.path.join(".", "uploaded_resume.pdf")
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        active_resume_path = temp_path
        st.success(f"Uploaded: {uploaded_file.name}")
    elif default_resume_path:
        active_resume_path = default_resume_path
        st.info("Using detected default: `resume.pdf`")
    else:
        st.warning("Please upload a resume PDF to begin.")

    st.divider()
    
    # Role Search Parameters
    st.subheader("🎯 Search Target")
    job_query = st.text_input("Target Role / Goal", value="Data Analyst")
    region_choice = st.selectbox(
        "Target Market / Location",
        ["🇮🇳 India (Local & Hybrid/Remote)", "🌍 Worldwide Remote (Open to India)"],
        help="India mode queries live openings from Indian job portals (Indeed India, LinkedIn). Worldwide mode checks verified global remote boards."
    )
    search_limit = st.slider("Job Openings to Analyze", min_value=1, max_value=8, value=3)
    
    run_btn = st.button("🚀 Run Placement Agent", type="primary", use_container_width=True)

# Main Dashboard Header
st.markdown('<div class="main-header">🤖 AI Placement Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Autonomous ATS matcher, skill-gap diagnostician, and personalized application generator</div>', unsafe_allow_html=True)

# Resume Preview Tab / Expander
if active_resume_path and os.path.exists(active_resume_path):
    with st.expander("👁️ View Extracted Resume Content", expanded=False):
        try:
            resume_preview = agent.read_resume(active_resume_path)
            st.text_area("Extracted Text", resume_preview, height=220)
        except Exception as e:
            st.error(f"Error reading resume: {e}")

# Pipeline Execution
if run_btn:
    if not active_resume_path:
        st.error("Please upload or provide a resume.pdf first.")
    elif not agent.GEMINI_API_KEY and not agent.ANTHROPIC_API_KEY:
        st.error("Missing API key! Provide GEMINI_API_KEY in sidebar or .env file.")
    else:
        status_box = st.status("🤖 Agent actively searching and analyzing jobs...", expanded=True)
        
        try:
            status_box.write("📄 Reading and structuring candidate resume...")
            resume_text = agent.read_resume(active_resume_path)
            
            search_region = "India" if "India" in region_choice else "Worldwide Remote"
            status_box.write(f"🌐 Fetching live openings for **'{job_query}'** ({search_region})...")
            jobs = agent.search_jobs(job_query, limit=search_limit, region=search_region)
            
            if not jobs:
                status_box.update(label="No jobs found for query", state="error")
                st.warning(f"No active job postings found for '{job_query}' in {search_region}. Try broader terms like 'python', 'data', or 'developer'.")
            else:
                status_box.write(f"🔎 Found {len(jobs)} active job postings. Running deep ATS matching...")
                
                results = []
                progress_bar = st.progress(0.0)
                for idx, job in enumerate(jobs):
                    status_box.write(f"🧠 Evaluating `{job['title']} @ {job['company']}`...")
                    analysis = agent.analyze_job(resume_text, job)
                    results.append({**job, **analysis})
                    progress_bar.progress((idx + 1) / len(jobs))
                    
                results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
                st.session_state["placement_results"] = results
                st.session_state["last_query"] = job_query
                status_box.update(label=f"✅ Analysis Complete! {len(results)} jobs matched.", state="complete")
        except Exception as err:
            status_box.update(label="Error occurred during analysis", state="error")
            st.error(f"Execution Error: {err}")

# Display Results
if "placement_results" in st.session_state and st.session_state["placement_results"]:
    results = st.session_state["placement_results"]
    st.divider()
    
    # High-level Metrics Row
    col1, col2, col3 = st.columns(3)
    avg_score = round(sum(r.get("match_score", 0) for r in results) / len(results), 1)
    best_job = results[0]
    
    with col1:
        st.metric("Total Jobs Evaluated", len(results))
    with col2:
        st.metric("Average Match Score", f"{avg_score}%")
    with col3:
        st.metric("Top Opportunity Score", f"{best_job.get('match_score', 0)}%", delta=best_job['title'][:25])

    st.subheader(f"📊 Ranked Opportunities for '{st.session_state.get('last_query', 'Role')}'")
    
    for idx, r in enumerate(results, 1):
        score = r.get("match_score", 0)
        
        # Color badge for score
        if score >= 75:
            score_color = "#16a34a"  # Green
            badge_text = "🟢 Strong Fit"
        elif score >= 50:
            score_color = "#ca8a04"  # Amber
            badge_text = "🟡 Moderate Fit"
        else:
            score_color = "#dc2626"  # Red
            badge_text = "🔴 Low Fit"

        with st.container():
            st.markdown(f"""
            <div class="job-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h3 style="margin: 0; color: #1e293b;">{idx}. {r['title']}</h3>
                        <p style="margin: 4px 0 10px 0; font-size: 1.05rem; font-weight: 600; color: #475569;">
                            🏢 {r['company']} &nbsp;&nbsp;
                            <span class="tag-location">📍 {r.get('candidate_required_location', 'Remote')}</span>
                            <span class="tag-location">💼 {r.get('job_type', 'Full-time')}</span>
                        </p>
                    </div>
                    <div style="text-align: right; min-width: 130px;">
                        <span style="font-size: 1.8rem; font-weight: 800; color: {score_color};">{score}%</span><br/>
                        <span style="font-size: 0.85rem; font-weight: 600; color: {score_color};">{badge_text}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Interactive Details inside Tabs
            tab1, tab2, tab3 = st.tabs(["✨ Skills & Gap Breakdown", "✉️ Tailored Cold Message", "📄 Job Description"])
            
            with tab1:
                col_match, col_gap = st.columns(2)
                with col_match:
                    st.markdown("**✅ Matched Skills Detected:**")
                    matched_skills = r.get("matched_skills", [])
                    if matched_skills:
                        badges_html = "".join([f'<span class="badge-matched">{s}</span>' for s in matched_skills])
                        st.markdown(badges_html, unsafe_allow_html=True)
                    else:
                        st.caption("No direct keyword match found in resume.")
                        
                with col_gap:
                    st.markdown("**⚠️ Missing Skills / Gaps:**")
                    skill_gaps = r.get("skill_gaps", [])
                    if skill_gaps:
                        gaps_html = "".join([f'<span class="badge-gap">{s}</span>' for s in skill_gaps])
                        st.markdown(gaps_html, unsafe_allow_html=True)
                    else:
                        st.caption("No significant skill gaps identified!")

                st.markdown(f"**💡 Action Plan to Bridge Gap:**")
                st.info(r.get("gap_plan", "Review core job responsibilities and align project bullet points."))

            with tab2:
                st.markdown("**Crafted Cold Outreach Message (<120 words):**")
                cold_msg = r.get("application_message", "")
                st.code(cold_msg, language="markdown")
                
            with tab3:
                st.write(r.get("description", "No description provided."))
                if r.get("url"):
                    st.link_button("🌐 Apply on Company Site", r["url"], type="primary")

            st.write("") # Spacer

    # Download Report Option
    st.divider()
    report_content = f"# AI Placement Report: {st.session_state.get('last_query', 'Jobs')}\n\n"
    for r in results:
        report_content += f"## {r['title']} @ {r['company']} ({r.get('match_score', 0)}%)\n"
        report_content += f"- URL: {r.get('url', '')}\n"
        report_content += f"- Matched Skills: {', '.join(r.get('matched_skills', []))}\n"
        report_content += f"- Skill Gaps: {', '.join(r.get('skill_gaps', []))}\n"
        report_content += f"- Plan: {r.get('gap_plan', '')}\n\n"
        report_content += f"### Message:\n{r.get('application_message', '')}\n\n---\n\n"
        
    st.download_button(
        label="📥 Download Full Placement Report (Markdown)",
        data=report_content,
        file_name="placement_report.md",
        mime="text/markdown"
    )
