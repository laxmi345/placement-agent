import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Output PDF path
PDF_PATH = r"C:\Users\laxmi sahu\Downloads\AI_Projects_Interview_Cross_Questions_Master_Guide.pdf"

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page count."""
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Draw header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "AI Projects Master Interview & Cross-Questions Defense Guide")
            self.drawRightString(612 - 54, 755, "Candidate: Laxmi Sahu")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 747, 612 - 54, 747)
            
        # Draw footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 35, page_text)
        self.drawString(54, 35, "CONFIDENTIAL — Placement & Technical Viva Preparation")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 47, 612 - 54, 47)
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#475569'),
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#6B21A8'),
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )

    q_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    ans_style = ParagraphStyle(
        'AnswerStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )

    tip_style = ParagraphStyle(
        'TipStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#065F46')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1E293B')
    )

    story = []

    # ---------------------------------------------------------
    # COVER / HEADER BLOCK
    # ---------------------------------------------------------
    story.append(Paragraph("AI PROJECTS MASTER INTERVIEW & CROSS-QUESTIONS DEFENSE GUIDE", title_style))
    story.append(Paragraph("Comprehensive Technical Viva, System Design & Behavioral Preparation for Placement Rounds", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1E3A8A'), spaceBefore=0, spaceAfter=12))

    meta_data = [
        [
            Paragraph("<b>Candidate:</b> Laxmi Sahu", table_cell_style),
            Paragraph("<b>Target Roles:</b> AI/ML Engineer, Data Analyst, GenAI Developer", table_cell_style)
        ],
        [
            Paragraph("<b>Primary Projects:</b><br/>1. RAG Study Assistant (RGPV Notes Q&A)<br/>2. Autonomous AI Placement Agent", table_cell_style),
            Paragraph("<b>Key Skills:</b> RAG, ChromaDB, FastAPI, LLMs (Gemini), Web Scraping, Prompt Engineering, ATS Optimization", table_cell_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # Helper function to add QA blocks
    def add_qa(q_num, question, answer, pro_tip=None):
        q_p = Paragraph(f"<b>Q{q_num}: {question}</b>", q_style)
        ans_p = Paragraph(f"<b>Ideal Response:</b> {answer}", ans_style)
        items = [q_p, ans_p]
        if pro_tip:
            tip_data = [[Paragraph(f"💡 <b>Interviewer Trap / Pro Tip:</b> {pro_tip}", tip_style)]]
            tip_table = Table(tip_data, colWidths=[504])
            tip_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ECFDF5')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#A7F3D0')),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            items.append(tip_table)
            items.append(Spacer(1, 4))
        items.append(Spacer(1, 4))
        story.append(KeepTogether(items))

    # ---------------------------------------------------------
    # PART 1: RAG STUDY ASSISTANT
    # ---------------------------------------------------------
    story.append(Paragraph("PROJECT 1: 📚 RAG STUDY ASSISTANT (RGPV NOTES Q&A)", h1_style))
    story.append(Paragraph("<b>Tech Stack:</b> Python, FastAPI, ChromaDB, LangChain, Google Gemini API (1.5 Flash + text-embedding-004), PyPDF, Streamlit", ans_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceBefore=2, spaceAfter=8))

    # Architecture Overview Table
    rag_arch_data = [
        [Paragraph("Pipeline Stage", table_header_style), Paragraph("Component Used", table_header_style), Paragraph("Technical Purpose & Reason", table_header_style)],
        [Paragraph("1. Parsing", table_cell_style), Paragraph("PyPDF", table_cell_style), Paragraph("Extracts text while preserving page-number metadata for exact citations.", table_cell_style)],
        [Paragraph("2. Chunking", table_cell_style), Paragraph("RecursiveCharacterTextSplitter", table_cell_style), Paragraph("Chunk size 1000, overlap 150. Maintains semantic continuity across boundaries.", table_cell_style)],
        [Paragraph("3. Embedding", table_cell_style), Paragraph("Google text-embedding-004", table_cell_style), Paragraph("Generates 768-dim dense vector representations capturing engineering concepts.", table_cell_style)],
        [Paragraph("4. Vector Store", table_cell_style), Paragraph("ChromaDB (Local)", table_cell_style), Paragraph("Embedded vector DB. Zero cloud infrastructure cost, fast HNSW similarity search.", table_cell_style)],
        [Paragraph("5. Generation", table_cell_style), Paragraph("Gemini 1.5 Flash (temp=0.2)", table_cell_style), Paragraph("Strict RGPV exam persona (2/7/14 marks), ASCII block diagrams, page citations.", table_cell_style)]
    ]
    t1 = Table(rag_arch_data, colWidths=[80, 140, 284])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t1)
    story.append(Spacer(1, 10))

    story.append(Paragraph("🔥 Deep-Dive Cross Questions (Level 1 to 5)", h2_style))

    add_qa(
        1,
        "What is RAG, and why is it superior to fine-tuning an LLM for college notes?",
        "RAG (Retrieval-Augmented Generation) combines external document retrieval with an LLM's generative capability. Instead of baking syllabus facts into model weights via expensive fine-tuning (which costs compute, suffers catastrophic forgetting, and can still hallucinate), RAG acts like an 'open-book exam'. The system retrieves exact paragraphs from university notes and prompts the LLM to synthesize an answer based strictly on those passages. This guarantees 100% verifiable page citations, zero training cost, and instant note updates.",
        "Emphasize the 'open book vs closed book' analogy. Interviewers love this intuitive explanation."
    )

    add_qa(
        2,
        "Why did you choose a chunk size of 1000 characters with an overlap of 150?",
        "1000 characters (~180-220 words) is the optimal semantic grain for engineering concepts. A typical technical definition, theorem, or protocol mechanism fits comfortably in 1-2 paragraphs. If the chunk is too small (e.g., 200 chars), context is fragmented and equations lose their explanations. If too large (e.g., 4000 chars), multiple unrelated topics get merged into one vector, polluting the similarity search. The 150-character overlap ensures that sentences crossing boundary edges do not lose their semantic continuity.",
        "Be ready for: 'What if chunk size is 10,000?' Answer: Loss of retrieval precision and embedding dilution."
    )

    add_qa(
        3,
        "Why ChromaDB over enterprise vector databases like Pinecone, Milvus, or Weaviate?",
        "ChromaDB is a lightweight, embedded vector database running in-process via SQLite/DuckDB. For a student study assistant or on-prem university portal, ChromaDB requires zero external cloud infrastructure, eliminates API network latency, has zero monthly hosting bills, and provides high-performance HNSW (Hierarchical Navigable Small World) indexing for fast nearest-neighbor retrieval. For enterprise scale (millions of users), I would migrate to Pinecone or Qdrant with distributed sharding.",
        "Highlight that you understand the trade-off between simplicity/cost vs distributed enterprise scale."
    )

    add_qa(
        4,
        "How do you stop the LLM from hallucinating answers when a question is outside the syllabus?",
        "Through strict negative grounding and low temperature. The system prompt contains an explicit guardrail: 'Answer ONLY based on the retrieved context below. If the provided context does NOT contain enough information, respond honestly with: [Not found in uploaded unit notes] and do NOT speculate.' Furthermore, temperature is set to 0.2 to minimize creative randomness, ensuring the model sticks rigidly to the provided facts.",
        "Mention that without low temperature and negative constraint, LLMs will invent plausible-sounding engineering definitions."
    )

    add_qa(
        5,
        "What happens if two different units have overlapping topics (e.g., OOPS in C++ vs OOPS in Java)?",
        "This is solved via metadata filtering. When documents are ingested, each chunk stores rich metadata: {'subject': 'OOPM', 'unit': 'Unit_2', 'file_name': 'cpp_notes.pdf', 'page_number': 14}. During retrieval, the student query can be filtered by specific unit or subject tags (e.g., chroma.similarity_search(query, filter={'unit': 'Unit_2'})). This prevents vector collision and guarantees context isolation.",
        "This shows you know how to build production vector databases rather than naive toy demos."
    )

    add_qa(
        6,
        "How does the system format answers differently for 2, 7, and 14 marks in RGPV exams?",
        "University evaluators grade according to strict rubrics: 2 marks requires crisp 2-line definitions and formulas; 7 marks requires working principles, bulleted mechanisms, and an ASCII architecture diagram; 14 marks requires comprehensive mathematical derivation, pros/cons, and real-world case studies. My prompt dynamically injects the target marks schema: 'Format this as an RGPV [7-mark] answer. Include 1. Definition, 2. ASCII Block Diagram, 3. Step-by-Step Working, 4. Advantages.'",
        "This demonstrates domain empathy — you tailored the AI to actual user needs, not just generic answers."
    )

    add_qa(
        7,
        "What is the mathematical difference between Cosine Similarity, Euclidean Distance, and Dot Product?",
        "Cosine similarity measures the cosine of the angle between two vectors: (A · B) / (||A|| ||B||), ranging from -1 to 1. It evaluates directional alignment regardless of vector magnitude (length). Euclidean distance (L2 norm) measures the geometric distance between point coordinates: sqrt(sum((Ai - Bi)^2)). Dot product (A · B) considers both direction and magnitude. In normalized embeddings (like Google text-embedding-004), Cosine Similarity and Dot Product are mathematically equivalent because ||A|| = ||B|| = 1.",
        "This is a classic ML/NLP viva trap. Emphasize that normalized embeddings make Dot Product equal to Cosine."
    )

    story.append(PageBreak())

    # ---------------------------------------------------------
    # PART 2: AI PLACEMENT AGENT
    # ---------------------------------------------------------
    story.append(Paragraph("PROJECT 2: 🤖 AUTONOMOUS AI PLACEMENT AGENT", h1_style))
    story.append(Paragraph("<b>Tech Stack:</b> Python 3.11, pypdf, python-jobspy (Indeed India / LinkedIn), Remotive REST API, Google Gemini Flash, Streamlit", ans_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceBefore=2, spaceAfter=8))

    placement_arch_data = [
        [Paragraph("Pipeline Stage", table_header_style), Paragraph("Component Used", table_header_style), Paragraph("Technical Purpose & Reason", table_header_style)],
        [Paragraph("1. Resume Parsing", table_cell_style), Paragraph("pypdf", table_cell_style), Paragraph("Extracts multi-page candidate text without external OS binaries.", table_cell_style)],
        [Paragraph("2. Domestic Jobs", table_cell_style), Paragraph("python-jobspy (Indeed India)", table_cell_style), Paragraph("Scrapes live Indian tech postings (Wipro, TCS, tech startups) with browser TLS spoofing.", table_cell_style)],
        [Paragraph("3. Global Remote", table_cell_style), Paragraph("Remotive & RemoteOK APIs", table_cell_style), Paragraph("Fetches high-paying global remote roles, discarding 'USA Only' postings.", table_cell_style)],
        [Paragraph("4. ATS Match & Gap", table_cell_style), Paragraph("Gemini 3.1 Flash (JSON mode)", table_cell_style), Paragraph("Calculates 0-100% fit, skill gaps, 1-sentence action plan, tailored cold email.", table_cell_style)],
        [Paragraph("5. Fault Tolerance", table_cell_style), Paragraph("Exponential Backoff + Fallback", table_cell_style), Paragraph("Handles transient 503/429 errors by retrying and failing over to backup models.", table_cell_style)]
    ]
    t2 = Table(placement_arch_data, colWidths=[90, 140, 274])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6B21A8')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t2)
    story.append(Spacer(1, 10))

    story.append(Paragraph("🔥 Deep-Dive Cross Questions (Level 1 to 5)", h2_style))

    add_qa(
        8,
        "Is your ATS matching score based on keyword counting or semantic evaluation?",
        "It is 100% semantic matching. Keyword matchers fail on tech synonyms. If a job requests 'ETL Pipeline Architect' and the resume says 'Kafka, PySpark, and dbt batch processing', a keyword tool gives 0%. An LLM recognizes that Kafka and PySpark represent the exact modern data stack for ETL. Furthermore, the LLM evaluates the candidate's actual years of experience and project complexity, returning realistic fit scores (e.g., 65% for a student applying to a senior role rather than an inflated 95%).",
        "Give the Kafka vs ETL example! It proves you understand real-world resume engineering."
    )

    add_qa(
        9,
        "How did you fetch live jobs from India without paid API subscriptions to LinkedIn or Naukri?",
        "Indian portals lack open public APIs. I integrated 'python-jobspy', an open-source library that uses 'curl_cffi' to impersonate modern browser TLS/JA3 fingerprints. This bypasses anti-bot protections and queries Indeed India and LinkedIn directly for real-time postings (such as Wipro, Arting Digital, and Indian tech hubs). For global remote roles, I query public REST APIs like Remotive and RemoteOK.",
        "Mention 'TLS/JA3 fingerprint impersonation' — it shows deep technical awareness of modern web scraping."
    )

    add_qa(
        10,
        "How do you ensure the LLM outputs strict JSON and doesn't break your Python code with backticks?",
        "I implemented a two-tier defense: First, in the Gemini API payload, I set 'responseMimeType: application/json', which forces the LLM's decoding engine to adhere strictly to JSON grammar. Second, on the client side, I wrapped the parser in regex sanitization ('re.sub(r'^```(json)?\s*', ...)') to strip any markdown preambles before calling 'json.loads()'. In case of network drops, exponential retry loops catch exceptions gracefully.",
        "Emphasize that production LLM apps must NEVER trust raw text output without client-side sanitization."
    )

    add_qa(
        11,
        "Why were US jobs appearing initially, and how did you engineer the India-specific localization?",
        "Global job boards like Remotive are US/Europe centric; ~90% of their postings require US work authorization or Pacific timezone hours. To fix this, I engineered a dual-mode search layer: in 'India' mode, the agent prioritizes JobSpy/Indeed India. In 'Worldwide Remote' mode, the engine inspects the 'candidate_required_location' metadata and discards postings tagged with 'USA Only' or 'Americas Only', only passing postings open to 'Worldwide', 'Anywhere', or 'India'.",
        "This answers the exact real-world problem we tackled during development."
    )

    add_qa(
        12,
        "How does the agent generate the cold application pitch without hallucinating fake experience?",
        "The system prompt enforces strict anti-hallucination grounding: 'Draft a professional cold email (<120 words). Cite ONLY verified projects, metrics, and tools present in the candidate resume. Do NOT fabricate experience, companies, or credentials.' With temperature locked at 0.2, the model cites actual achievements—such as the candidate's Smart India Hackathon Top 10 finish and 200+ LeetCode problems—making the message authentically human.",
        "Interviewers love hearing that you kept cold outreach under 120 words — recruiters hate long essays."
    )

    add_qa(
        13,
        "What is the difference between a 'Fixed Pipeline' and an 'Autonomous ReAct Agent'?",
        "A fixed pipeline runs in rigid, deterministic order: Step 1 (Parse) -> Step 2 (Search) -> Step 3 (Analyze) -> Step 4 (Report). The code controls the flow. In a true ReAct (Reasoning + Acting) Agent, the LLM is equipped with tools (Tool Calling / Function Calling): 'search_jobs', 'fetch_details', 'evaluate_fit'. The LLM itself decides what tool to call based on observation. If a search query yields 0 results, the agent reasons: 'Let me broaden my query from Data Analyst to Business Intelligence Engineer and try again.'",
        "Know this distinction inside out! It is the most common question when 'AI Agent' is on a resume."
    )

    story.append(PageBreak())

    # ---------------------------------------------------------
    # PART 3: CROSS-PROJECT COMPARATIVE QUESTIONS
    # ---------------------------------------------------------
    story.append(Paragraph("PART 3: ⚖️ CROSS-PROJECT COMPARATIVE QUESTIONS (SENIOR ROUND)", h1_style))
    story.append(Paragraph("Senior interviewers love comparing your architectural choices across different projects to see if you genuinely understand AI system design.", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceBefore=2, spaceAfter=8))

    add_qa(
        14,
        "Why did you use Vector Embeddings (RAG) in Project 1, but passed the raw text directly in Project 2?",
        "This is an architectural decision based on the Context Window vs Search Space trade-off. In Project 1 (Study Assistant), a subject note can be 200+ pages (100,000+ words). Passing the entire textbook into the LLM context for every single query causes massive latency, high token costs, and 'Lost in the Middle' attention degradation. Vector embeddings allow precise top-4 chunk retrieval. In Project 2 (Placement Agent), a resume is only 1-2 pages (~800 words) and a job description is ~500 words. Since both fit comfortably within Gemini's context window, direct in-context prompting is faster, cheaper, and avoids embedding chunking artifacts.",
        "THIS IS A 10/10 ANSWER. Explaining when NOT to use RAG proves deep engineering maturity."
    )

    add_qa(
        15,
        "FastAPI in Project 1 vs pure Streamlit in Project 2 — why different architectures?",
        "Project 1 was designed as a decoupled client-server architecture: FastAPI serves headless REST endpoints (/ask, /upload) with Pydantic validation, allowing multiple frontend clients (mobile app, web app, LMS portal) to consume the study assistant backend. Project 2 was built as an integrated executive dashboard in Streamlit to deliver rapid interactive visualizations, dynamic score badges, and immediate recruitment insights without API overhead.",
        "Proves you select architectural patterns based on target use-case, not personal habit."
    )

    add_qa(
        16,
        "If you had to merge both projects into one unified university platform, how would you architect it?",
        "I would design a 'Campus AI Ecosystem' with 4 modular layers:<br/>"
        "1. <b>Core Ingestion Layer:</b> Unified document parser handling student resumes and syllabus notes.<br/>"
        "2. <b>Dual-Index Storage:</b> ChromaDB for student academic notes + PostgreSQL for job listings and candidate profiles.<br/>"
        "3. <b>Agentic Router:</b> An LLM router that directs student queries: If academic ('Explain OSI Model'), route to RAG Study Engine. If career-oriented ('Match me with internships for my Python skills'), route to Placement Agent.<br/>"
        "4. <b>Skill-Closing Loop:</b> If the Placement Agent identifies a skill gap (e.g., 'Candidate lacks SQL Stored Procedures'), it automatically queries the RAG Study Assistant to generate a targeted tutorial and practice quiz from the university notes!",
        "This answer will blow the interviewer away! Connecting career gaps with study notes shows visionary product thinking."
    )

    # ---------------------------------------------------------
    # PART 4: PRODUCTION SCALING & SYSTEM DESIGN
    # ---------------------------------------------------------
    story.append(Paragraph("PART 4: 🚀 SYSTEM DESIGN & SCALABILITY VIVA", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceBefore=2, spaceAfter=8))

    add_qa(
        17,
        "How would you scale these systems to handle 50,000 students during semester exam week?",
        "1. <b>Caching Layer:</b> Implement Redis caching for frequent RAG questions. If 200 students ask 'Explain Dijkstra Algorithm', serve the generated response from Redis in 5ms without calling the LLM.<br/>"
        "2. <b>Async Task Queues:</b> Use Celery with Redis/RabbitMQ message brokers to process PDF parsing and embedding generation in background worker pools.<br/>"
        "3. <b>Read Replicas & Sharding:</b> Run ChromaDB/Qdrant vector clusters with read replicas to distribute similarity search load across multiple nodes.<br/>"
        "4. <b>Rate Limit Throttling:</b> Token bucket rate limiters in FastAPI to prevent abusive burst queries.",
        "Mention Redis caching first — in college exams, 70% of questions are repeated!"
    )

    add_qa(
        18,
        "What was the most challenging technical bug you solved in these projects?",
        "In Project 2, two major challenges arose: First, Windows terminal encoding default (cp1252) crashed the script with 'UnicodeEncodeError' when printing emoji badges; I resolved it by programmatically reconfiguring 'sys.stdout.reconfigure(encoding=\"utf-8\", errors=\"replace\")'. Second, Google Gemini preview models were intermittently throwing 503 Overloaded errors; I engineered an exponential backoff retry loop with multi-model fallback ('[gemini-3.1-flash-lite, gemini-flash-latest]') ensuring zero unhandled crashes.",
        "Always talk about a REAL bug from code development rather than textbook theoretical bugs."
    )

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Master Interview PDF generated successfully at: {PDF_PATH}")

if __name__ == "__main__":
    build_pdf()
