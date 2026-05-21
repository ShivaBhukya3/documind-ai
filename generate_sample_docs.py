"""Generate realistic sample PDF documents for DocuMind AI demo."""

import os
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("reportlab not installed. Generating .txt files as fallback.")

OUTPUT_DIR = Path("data/raw/sample_docs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# PDF helper
# ─────────────────────────────────────────────────────────────────────────────

def build_pdf(filename: str, title: str, sections: list[dict]) -> None:
    """Build a styled PDF from a list of {heading, body} section dicts."""
    path = OUTPUT_DIR / filename
    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    accent = HexColor("#7C3AED")

    title_style = ParagraphStyle(
        "DocTitle", parent=styles["Title"],
        fontSize=24, textColor=accent,
        spaceAfter=12, alignment=TA_CENTER,
    )
    h1_style = ParagraphStyle(
        "H1", parent=styles["Heading1"],
        fontSize=16, textColor=accent, spaceBefore=18, spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=13, textColor=HexColor("#374151"), spaceBefore=12, spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, leading=16, alignment=TA_JUSTIFY, spaceAfter=8,
    )
    bullet_style = ParagraphStyle(
        "Bullet", parent=body_style,
        leftIndent=20, bulletIndent=10,
    )

    story = [
        Paragraph(title, title_style),
        HRFlowable(width="100%", thickness=2, color=accent, spaceAfter=20),
    ]

    for sec in sections:
        level = sec.get("level", 1)
        heading = sec.get("heading", "")
        body = sec.get("body", "")
        bullets = sec.get("bullets", [])

        if heading:
            style = h1_style if level == 1 else h2_style
            story.append(Paragraph(heading, style))

        if body:
            for para in body.split("\n\n"):
                para = para.strip()
                if para:
                    story.append(Paragraph(para, body_style))

        for bullet in bullets:
            story.append(Paragraph(f"- {bullet}", bullet_style))

        if sec.get("page_break"):
            story.append(PageBreak())
        else:
            story.append(Spacer(1, 6))

    doc.build(story)
    print(f"  OK  {path}")


def build_txt(filename: str, title: str, sections: list[dict]) -> None:
    """Fallback plain-text writer."""
    path = OUTPUT_DIR / filename.replace(".pdf", ".txt")
    lines = [title, "=" * len(title), ""]
    for sec in sections:
        if sec.get("heading"):
            lines += [sec["heading"], "-" * len(sec["heading"]), ""]
        if sec.get("body"):
            lines += [sec["body"], ""]
        for b in sec.get("bullets", []):
            lines.append(f"  • {b}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  OK  {path}")


def create_doc(filename: str, title: str, sections: list[dict]) -> None:
    if REPORTLAB_AVAILABLE:
        build_pdf(filename, title, sections)
    else:
        build_txt(filename, title, sections)


# ─────────────────────────────────────────────────────────────────────────────
# Document 1 — Company Policy
# ─────────────────────────────────────────────────────────────────────────────

def create_company_policy() -> None:
    create_doc(
        "company_policy.pdf",
        "TechCorp Solutions — Employee Policy Manual v3.2",
        [
            {
                "heading": "1. Introduction",
                "body": (
                    "Welcome to TechCorp Solutions. This Employee Policy Manual outlines the "
                    "standards, expectations, and guidelines that govern our workplace. Every "
                    "team member is expected to read, understand, and adhere to these policies. "
                    "This document supersedes all previous versions of the policy manual.\n\n"
                    "TechCorp Solutions was founded in 2010 and has grown to employ over 2,500 "
                    "professionals across 12 offices in India, USA, and Singapore. Our mission is "
                    "to deliver world-class software products while maintaining a respectful, "
                    "inclusive, and high-performance workplace."
                ),
            },
            {
                "heading": "2. Leave Policy",
                "level": 1,
                "body": (
                    "TechCorp Solutions offers a comprehensive leave policy designed to support "
                    "employee well-being and work-life balance."
                ),
                "bullets": [
                    "Annual Leave: 18 days per calendar year (pro-rated for new joiners)",
                    "Sick Leave: 12 days per year (requires medical certificate beyond 3 consecutive days)",
                    "Casual Leave: 6 days per year (max 3 consecutive days)",
                    "Maternity Leave: 26 weeks as per the Maternity Benefit Act 2017",
                    "Paternity Leave: 10 days within 6 months of childbirth",
                    "Bereavement Leave: 5 days for immediate family members",
                    "Public Holidays: 10 national + 3 optional holidays per year",
                    "Carry-forward: Up to 10 unused annual leave days may be carried to next year",
                ],
            },
            {
                "heading": "2.1 Leave Application Process",
                "level": 2,
                "body": (
                    "All leave requests must be submitted through the HR portal (hr.techcorp.internal) "
                    "at least 48 hours in advance for planned leave. Emergency leave must be notified "
                    "to the direct manager via phone or email within 2 hours of the start of the workday. "
                    "Leave requests are subject to manager approval based on business requirements. "
                    "Employees on extended sick leave (>5 days) must submit a fitness-to-return certificate."
                ),
            },
            {
                "heading": "3. Work From Home (WFH) Policy",
                "level": 1,
                "body": (
                    "TechCorp Solutions operates a hybrid work model effective January 2024. "
                    "Employees are expected to be present in office a minimum of 3 days per week "
                    "(Tuesday, Wednesday, Thursday are mandatory office days for most teams).\n\n"
                    "WFH eligibility is based on role classification:"
                ),
                "bullets": [
                    "Category A (Full Hybrid): Software Engineers, Data Scientists, Product Managers — up to 2 WFH days/week",
                    "Category B (Mostly Office): Sales, Support, Operations — up to 1 WFH day/week",
                    "Category C (Full Remote): Pre-approved remote employees — 5 days WFH",
                    "All WFH employees must maintain a dedicated workspace with reliable internet (min 25 Mbps)",
                    "Core hours for availability: 10:00 AM – 5:00 PM IST regardless of location",
                    "VPN must be used for all company system access from home",
                ],
            },
            {
                "heading": "4. Code of Conduct",
                "level": 1,
                "body": (
                    "TechCorp Solutions is committed to maintaining a workplace free from discrimination, "
                    "harassment, and intimidation. All employees must treat colleagues, clients, and "
                    "vendors with dignity and respect."
                ),
                "bullets": [
                    "Zero tolerance for sexual harassment (POSH Act compliance mandatory)",
                    "Discrimination based on race, gender, religion, disability or age is strictly prohibited",
                    "Workplace conflicts must be escalated to HR within 7 days of the incident",
                    "Confidential information must never be shared outside the organisation",
                    "Social media posts about the company require prior approval from the Communications team",
                    "Employees must not engage in moonlighting without written approval from HR",
                ],
            },
            {
                "heading": "5. IT Usage Policy",
                "level": 1,
                "body": (
                    "Company-provided devices and network infrastructure are for professional use only. "
                    "Personal use is permitted within reasonable limits but must not interfere with "
                    "work responsibilities or consume excessive bandwidth."
                ),
                "bullets": [
                    "Passwords must be at least 12 characters with mixed case, numbers, and symbols",
                    "Password rotation is mandatory every 90 days",
                    "Employees must lock screens when away from their desk (Win+L or Cmd+Ctrl+Q)",
                    "Installation of unauthorised software requires IT approval via the service desk",
                    "Downloading pirated content or visiting gambling/adult sites is prohibited",
                    "All company data must be stored in approved cloud platforms (Google Drive, Confluence)",
                    "USB drives are prohibited unless encrypted and registered with IT Security",
                    "Incidents must be reported to security@techcorp.com within 1 hour of detection",
                ],
            },
            {
                "heading": "6. Performance Review Process",
                "level": 1,
                "body": (
                    "TechCorp follows a bi-annual performance review cycle (April and October). "
                    "Performance is evaluated on a 5-point scale:\n\n"
                    "5 — Exceptional | 4 — Exceeds Expectations | 3 — Meets Expectations | "
                    "2 — Needs Improvement | 1 — Unsatisfactory\n\n"
                    "Reviews involve self-assessment, manager rating, and a calibration session "
                    "with senior leadership. Employees rated 4+ are eligible for accelerated "
                    "promotion tracks and spot bonuses. Employees rated below 2 for two consecutive "
                    "cycles are placed on a Performance Improvement Plan (PIP)."
                ),
                "bullets": [
                    "Goal-setting (OKRs) must be completed within the first 2 weeks of each half",
                    "Mid-cycle check-ins are mandatory in month 3 of each half",
                    "360-degree feedback is collected from peers and cross-functional stakeholders",
                    "Promotion decisions are finalised in May and November",
                    "Annual increment ranges: 0% (rating 1-2), 5-8% (rating 3), 10-15% (rating 4), 18-25% (rating 5)",
                ],
            },
            {
                "heading": "7. Grievance Redressal",
                "level": 1,
                "body": (
                    "Employees may raise grievances through the following channels:\n\n"
                    "1. Direct Manager → 2. HR Business Partner → 3. HR Head → 4. CHRO → 5. CEO\n\n"
                    "All grievances are acknowledged within 24 hours and resolved within 14 business days. "
                    "Retaliation against an employee for raising a genuine grievance is a terminable offence. "
                    "Anonymous feedback can be submitted at feedback.techcorp.internal."
                ),
            },
            {
                "heading": "8. Disciplinary Action",
                "level": 1,
                "body": "Violations of this policy may result in the following actions (in order of severity):",
                "bullets": [
                    "Verbal warning (documented in HR system)",
                    "Written warning (first offence for minor violations)",
                    "Final written warning with 30-day review period",
                    "Suspension without pay (up to 10 days)",
                    "Termination of employment",
                ],
            },
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Document 2 — Product Manual
# ─────────────────────────────────────────────────────────────────────────────

def create_product_manual() -> None:
    create_doc(
        "product_manual.pdf",
        "DocuMind AI — Product Documentation v1.0",
        [
            {
                "heading": "Overview",
                "body": (
                    "DocuMind AI is an enterprise-grade Retrieval-Augmented Generation (RAG) system "
                    "that enables organisations to query their internal documents using natural language. "
                    "The system combines state-of-the-art LLMs with vector search to deliver accurate, "
                    "cited answers from your document corpus.\n\n"
                    "Key capabilities: multi-document Q&A, real-time streaming responses, "
                    "source citations with page numbers, conversation memory, and a REST API."
                ),
            },
            {
                "heading": "1. System Requirements",
                "bullets": [
                    "Python 3.10 or higher",
                    "RAM: Minimum 8 GB (16 GB recommended for large document sets)",
                    "Disk: 10 GB free space for models and vector indexes",
                    "OS: Ubuntu 20.04+, macOS 12+, Windows 11",
                    "GPU: Optional — NVIDIA GPU with CUDA 11.8+ improves embedding speed by 10x",
                    "Internet: Required for OpenAI API (optional if using local models)",
                ],
            },
            {
                "heading": "2. Installation",
                "level": 1,
                "body": (
                    "Step 1 — Clone the repository:\n"
                    "  git clone https://github.com/yourusername/documind-ai.git\n"
                    "  cd documind-ai\n\n"
                    "Step 2 — Create virtual environment:\n"
                    "  python -m venv venv\n"
                    "  source venv/bin/activate  # Linux/Mac\n"
                    "  venv\\Scripts\\activate   # Windows\n\n"
                    "Step 3 — Install dependencies:\n"
                    "  pip install -r requirements.txt\n\n"
                    "Step 4 — Configure environment:\n"
                    "  cp .env.example .env\n"
                    "  # Edit .env with your API keys\n\n"
                    "Step 5 — Generate sample data:\n"
                    "  python generate_sample_docs.py\n\n"
                    "Step 6 — Run the dashboard:\n"
                    "  streamlit run dashboard/app.py"
                ),
            },
            {
                "heading": "3. Configuration Guide",
                "level": 1,
                "body": (
                    "All configuration is managed via config/config.yaml. Key settings:"
                ),
                "bullets": [
                    "llm.provider: 'openai' for GPT models, 'huggingface' for free models",
                    "llm.model_name: 'gpt-3.5-turbo' (default) or 'gpt-4' for higher quality",
                    "llm.temperature: 0.0 for factual responses, 0.7 for creative responses",
                    "embeddings.provider: 'openai' (ada-002) or 'huggingface' (MiniLM, free)",
                    "vector_store.top_k: Number of document chunks to retrieve (default: 5)",
                    "chunking.chunk_size: Text chunk size in characters (default: 1000)",
                    "retrieval.search_type: 'mmr' for diverse results, 'similarity' for pure relevance",
                    "FREE_MODE=true in .env enables fully local operation at no cost",
                ],
            },
            {
                "heading": "4. API Reference",
                "level": 1,
                "body": "The REST API is available at http://localhost:8000. Base path: /api/v1",
            },
            {
                "heading": "4.1 Chat Endpoints",
                "level": 2,
                "body": (
                    "POST /api/v1/chat\n"
                    "Request body: {\"question\": \"string\", \"session_id\": \"string\", \"stream\": bool}\n"
                    "Response: {\"answer\": \"string\", \"sources\": [], \"confidence\": float, "
                    "\"tokens_used\": int, \"response_time\": float}\n\n"
                    "POST /api/v1/chat/reset\n"
                    "Request body: {\"session_id\": \"string\"}\n"
                    "Clears conversation history for the given session.\n\n"
                    "GET /api/v1/chat/history/{session_id}\n"
                    "Returns the full conversation history with metadata."
                ),
            },
            {
                "heading": "4.2 Document Endpoints",
                "level": 2,
                "body": (
                    "POST /api/v1/documents/upload\n"
                    "Multipart form-data. Accepts PDF, DOCX, TXT, CSV, PPTX.\n"
                    "Response: {\"doc_id\": str, \"chunks_created\": int, \"processing_time\": float}\n\n"
                    "GET /api/v1/documents/list\n"
                    "Returns all indexed documents with metadata.\n\n"
                    "DELETE /api/v1/documents/{doc_id}\n"
                    "Removes a document and its vectors from the index.\n\n"
                    "GET /api/v1/documents/stats\n"
                    "Returns total vectors, index size, and per-document statistics."
                ),
            },
            {
                "heading": "5. Troubleshooting",
                "level": 1,
                "body": "Common issues and their resolutions:",
                "bullets": [
                    "Error 'No module named faiss': Run 'pip install faiss-cpu' (or faiss-gpu for GPU)",
                    "OpenAI AuthenticationError: Verify OPENAI_API_KEY in your .env file",
                    "Slow embedding speed: Set FREE_MODE=false to use OpenAI Ada-002 (much faster)",
                    "Empty answers: Lower score_threshold in config.yaml (default 0.3 → try 0.1)",
                    "Memory issues with large PDFs: Reduce chunk_size to 500 in config.yaml",
                    "Port 8501 already in use: Kill existing Streamlit with 'pkill -f streamlit'",
                    "FAISS index corrupt: Delete data/processed/embeddings/ and re-ingest documents",
                    "Rate limit from OpenAI: Implement exponential backoff or switch to gpt-3.5-turbo",
                ],
            },
            {
                "heading": "6. FAQ",
                "level": 1,
                "body": "",
                "bullets": [
                    "Q: Can I use DocuMind AI without an OpenAI API key? A: Yes, set FREE_MODE=true.",
                    "Q: What is the maximum document size? A: 50 MB per file (configurable).",
                    "Q: How many documents can I index? A: FAISS supports millions of vectors.",
                    "Q: Is my data sent to OpenAI? A: Only if using OpenAI APIs; FREE_MODE keeps data local.",
                    "Q: Can I use my own embedding model? A: Yes, set embeddings.provider to 'huggingface'.",
                    "Q: How do I improve answer quality? A: Increase top_k, use gpt-4, reduce chunk_size.",
                    "Q: Does it support multiple languages? A: Yes, but best results with English documents.",
                ],
            },
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Document 3 — Financial Report
# ─────────────────────────────────────────────────────────────────────────────

def create_financial_report() -> None:
    create_doc(
        "financial_report.pdf",
        "TechCorp Solutions — Annual Financial Report FY 2024",
        [
            {
                "heading": "Executive Summary",
                "body": (
                    "FY 2024 was a landmark year for TechCorp Solutions. The company reported its highest-ever "
                    "revenue of ₹45 Crore, representing a 32% year-over-year growth from ₹34.1 Crore in FY 2023. "
                    "EBITDA margin improved to 28% (₹12.6 Crore) from 22% in the prior year, driven by "
                    "operational efficiency initiatives and a favourable product mix shift toward high-margin "
                    "SaaS offerings.\n\n"
                    "Net profit after tax stood at ₹8.5 Crore, up 41% YoY. The company ended FY 2024 with "
                    "₹14 Crore in cash and equivalents, providing a strong runway for planned expansion into "
                    "the US and Southeast Asian markets in FY 2025."
                ),
            },
            {
                "heading": "Revenue Breakdown",
                "level": 1,
                "body": "Total Revenue: ₹45 Crore | Growth: +32% YoY",
                "bullets": [
                    "SaaS Products: ₹22.5 Crore (50% of revenue, +45% YoY)",
                    "Professional Services: ₹13.5 Crore (30% of revenue, +18% YoY)",
                    "Licensing & Support: ₹6.75 Crore (15% of revenue, +20% YoY)",
                    "Training & Certification: ₹2.25 Crore (5% of revenue, +67% YoY)",
                ],
            },
            {
                "heading": "Revenue by Geography",
                "level": 2,
                "bullets": [
                    "India: ₹27 Crore (60%) — Enterprise and SMB segments",
                    "USA: ₹9 Crore (20%) — Enterprise focus, 8 Fortune 500 clients",
                    "Singapore & APAC: ₹6.75 Crore (15%) — New market entry",
                    "Middle East & Others: ₹2.25 Crore (5%)",
                ],
            },
            {
                "heading": "Expense Summary",
                "level": 1,
                "body": "Total Operating Expenses: ₹32.4 Crore",
                "bullets": [
                    "Personnel Costs: ₹18.9 Crore (58.3% of expenses) — headcount grew from 180 to 250",
                    "Cloud Infrastructure (AWS/GCP): ₹4.86 Crore (15%) — optimised via Reserved Instances",
                    "Sales & Marketing: ₹4.53 Crore (14%) — 3 new markets entered",
                    "R&D Investment: ₹2.27 Crore (7%) — AI/ML product features",
                    "General & Administrative: ₹1.78 Crore (5.5%)",
                ],
            },
            {
                "heading": "Quarterly Performance",
                "level": 1,
                "body": "",
                "bullets": [
                    "Q1 FY24 (Apr–Jun 2023): Revenue ₹9.5 Crore | Net Profit ₹1.6 Crore",
                    "Q2 FY24 (Jul–Sep 2023): Revenue ₹10.8 Crore | Net Profit ₹1.9 Crore",
                    "Q3 FY24 (Oct–Dec 2023): Revenue ₹11.7 Crore | Net Profit ₹2.1 Crore",
                    "Q4 FY24 (Jan–Mar 2024): Revenue ₹13 Crore | Net Profit ₹2.9 Crore (best ever quarter)",
                ],
            },
            {
                "heading": "Key Financial Metrics",
                "level": 1,
                "bullets": [
                    "Gross Margin: 68% (up from 61% in FY23)",
                    "EBITDA: ₹12.6 Crore | EBITDA Margin: 28%",
                    "Net Profit: ₹8.5 Crore | Net Margin: 18.9%",
                    "Customer Acquisition Cost (CAC): ₹1.8 Lakh (down 15% from FY23)",
                    "Customer Lifetime Value (LTV): ₹22 Lakh | LTV:CAC Ratio: 12.2x",
                    "Annual Recurring Revenue (ARR): ₹24 Crore | Monthly Churn: 1.2%",
                    "Net Revenue Retention (NRR): 118%",
                    "Cash & Equivalents: ₹14 Crore | Debt: Nil",
                ],
            },
            {
                "heading": "Future Projections FY 2025",
                "level": 1,
                "body": (
                    "Based on current pipeline and market conditions, TechCorp projects FY 2025 revenue "
                    "of ₹62–65 Crore (38-44% growth), driven by:\n\n"
                    "1. US market expansion with 2 new enterprise clients already signed in Q1 FY25\n"
                    "2. Launch of DocuMind AI Enterprise Edition (₹12 Lakh/year per enterprise)\n"
                    "3. Strategic partnership with Infosys BPM for document processing at scale\n"
                    "4. Headcount expansion to 350 employees by Q3 FY25"
                ),
            },
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Document 4 — HR Handbook
# ─────────────────────────────────────────────────────────────────────────────

def create_hr_handbook() -> None:
    create_doc(
        "hr_handbook.pdf",
        "TechCorp Solutions — HR Handbook: New Employee Onboarding Guide",
        [
            {
                "heading": "Welcome to TechCorp Solutions!",
                "body": (
                    "Congratulations and welcome to the TechCorp family! We are thrilled to have you "
                    "as part of our fast-growing team of innovators, builders, and problem-solvers. "
                    "This handbook is your go-to guide for everything you need to know during your "
                    "first 90 days and beyond.\n\n"
                    "TechCorp Solutions was founded on the belief that great software, built by great "
                    "people, can transform how businesses operate. You are now part of that mission. "
                    "We look forward to seeing the unique value you will bring to your team."
                ),
            },
            {
                "heading": "1. Your First Week (Days 1–5)",
                "bullets": [
                    "Day 1: IT setup (laptop, email, Slack, Jira, Confluence access)",
                    "Day 1: Meet your buddy (peer mentor assigned to you for first 30 days)",
                    "Day 2: Orientation session with HR — company history, values, and culture",
                    "Day 2: Security awareness training (mandatory, 2 hours online)",
                    "Day 3: Team introductions and project handover meetings",
                    "Day 4: Product demo — understand what we build and sell",
                    "Day 5: 1:1 with your manager — 30/60/90 day goals setting",
                ],
            },
            {
                "heading": "2. Compensation & Benefits",
                "level": 1,
                "body": "TechCorp offers a competitive total compensation package:",
                "bullets": [
                    "Base Salary: Paid on the last working day of every month via NEFT",
                    "Variable Pay: 10-20% of CTC based on performance (paid semi-annually)",
                    "ESOP: Eligible after 1 year — 4-year vesting with 1-year cliff",
                    "Health Insurance: ₹5 Lakh family floater (self + spouse + 2 children)",
                    "Term Life Insurance: 3x annual CTC coverage",
                    "Accident Insurance: ₹25 Lakh personal accident policy",
                    "Gratuity: As per Payment of Gratuity Act (eligible after 5 years)",
                    "PF: 12% employer contribution on basic salary",
                    "Sodexo Meal Card: ₹2,500/month (tax-exempt)",
                    "Internet Reimbursement: ₹1,000/month for WFH employees",
                ],
            },
            {
                "heading": "3. Career Growth Framework",
                "level": 1,
                "body": (
                    "TechCorp follows a structured IC (Individual Contributor) and Management track. "
                    "Promotion decisions are based on a combination of performance rating, tenure, "
                    "and role availability."
                ),
                "bullets": [
                    "IC Track: Junior Engineer → Engineer → Senior Engineer → Staff Engineer → Principal Engineer",
                    "Management Track: Team Lead → Engineering Manager → Senior EM → Director → VP",
                    "Average time to first promotion: 18-24 months for top performers",
                    "Lateral moves are encouraged — cross-functional transfers allowed after 12 months",
                    "Learning budget: ₹50,000/year per employee for courses, conferences, certifications",
                    "Internal mobility portal: jobs.techcorp.internal (open positions posted every Friday)",
                ],
            },
            {
                "heading": "4. Team Structure",
                "level": 1,
                "body": (
                    "TechCorp is organised into 6 business units, each led by a VP reporting to the CEO."
                ),
                "bullets": [
                    "Engineering: 120 engineers across Frontend, Backend, Platform, ML/AI, and QA",
                    "Product: 25 PMs and Designers driving product roadmap",
                    "Sales & BD: 40 account executives and business development managers",
                    "Customer Success: 35 CSMs ensuring client retention and expansion",
                    "Operations & Finance: 20 employees managing compliance, legal, and finance",
                    "People & Culture (HR): 10 HRBPs and recruiters",
                ],
            },
            {
                "heading": "5. Tools & Access",
                "level": 1,
                "body": "You will be provisioned access to the following tools within Day 1:",
                "bullets": [
                    "Communication: Slack (primary), Email (Google Workspace), Zoom",
                    "Project Management: Jira (Engineering), Asana (Non-Engineering)",
                    "Documentation: Confluence (internal wiki), Google Drive",
                    "Code: GitHub Enterprise (Engineering), Bitbucket (legacy projects)",
                    "Design: Figma (Product & Design team)",
                    "Data & Analytics: Looker, BigQuery (Data Science team)",
                    "HR & Payroll: Darwinbox (leave, payslips, appraisals)",
                    "IT Help: ServiceNow — raise tickets at it.techcorp.internal",
                ],
            },
            {
                "heading": "6. Frequently Asked Questions (New Joiners)",
                "level": 1,
                "bullets": [
                    "When do I get my first salary? Salary is processed by the last working day of the month.",
                    "How do I apply for leave? Use the Darwinbox HR portal.",
                    "Who is my HR point of contact? Your assigned HRBP is listed in your offer letter.",
                    "Can I work from home? Yes, as per the WFH policy (see Employee Policy Manual).",
                    "How long is the probation period? 6 months for all new hires.",
                    "When can I apply for ESOP? After completing 12 months of service.",
                    "How do I raise an IT issue? Use ServiceNow at it.techcorp.internal.",
                    "Is there a dress code? Smart-casual. Formals only for client-facing meetings.",
                ],
            },
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Document 5 — Technical Documentation
# ─────────────────────────────────────────────────────────────────────────────

def create_technical_docs() -> None:
    create_doc(
        "technical_docs.pdf",
        "TechCorp Solutions — System Architecture & Technical Specifications",
        [
            {
                "heading": "1. Architecture Overview",
                "body": (
                    "TechCorp's platform is built on a microservices architecture deployed on AWS. "
                    "The system processes over 2 million API requests per day across 12 microservices, "
                    "with 99.97% uptime SLA. The architecture follows domain-driven design principles "
                    "with event-driven communication via Apache Kafka.\n\n"
                    "Core architectural decisions:\n"
                    "• Polyglot persistence: PostgreSQL (transactional), MongoDB (documents), "
                    "Redis (cache), Elasticsearch (search)\n"
                    "• API Gateway: Kong for rate limiting, auth, and routing\n"
                    "• Service mesh: Istio for inter-service communication and observability\n"
                    "• CI/CD: GitHub Actions → ArgoCD → Kubernetes (EKS)"
                ),
            },
            {
                "heading": "2. Database Schema",
                "level": 1,
                "body": "Primary PostgreSQL schema (techcorp_prod database):",
                "bullets": [
                    "users: id, email, name, role, org_id, created_at, last_login, is_active",
                    "organisations: id, name, plan, seats, created_at, billing_email, stripe_customer_id",
                    "documents: id, org_id, filename, file_type, size_bytes, chunk_count, indexed_at, status",
                    "conversations: id, session_id, user_id, created_at, message_count, last_message_at",
                    "messages: id, conversation_id, role, content, tokens_used, response_time_ms, created_at",
                    "api_keys: id, org_id, key_hash, name, permissions, created_at, expires_at, last_used_at",
                    "usage_logs: id, org_id, endpoint, tokens, cost_usd, latency_ms, status_code, created_at",
                ],
            },
            {
                "heading": "3. API Endpoints",
                "level": 1,
                "body": "REST API v2 (base: api.techcorp.com/v2). Authentication: Bearer JWT token.",
                "bullets": [
                    "POST /auth/login — Returns JWT access token (expires 24h)",
                    "POST /auth/refresh — Refresh expired token using refresh token",
                    "GET /documents — List documents with pagination (?page=1&limit=20)",
                    "POST /documents/upload — Upload document (multipart/form-data, max 50MB)",
                    "DELETE /documents/{id} — Delete document and remove from index",
                    "POST /chat — Send question and receive streamed answer (SSE)",
                    "GET /chat/history/{session_id} — Get conversation history",
                    "GET /usage — Get token usage statistics for billing period",
                    "GET /health — System health check (public endpoint, no auth required)",
                ],
            },
            {
                "heading": "4. Security Architecture",
                "level": 1,
                "body": (
                    "TechCorp implements a defence-in-depth security model aligned with ISO 27001 and "
                    "SOC 2 Type II standards."
                ),
                "bullets": [
                    "Authentication: OAuth 2.0 + PKCE for user auth, API keys for service-to-service",
                    "Authorisation: Role-Based Access Control (RBAC) with 5 roles: Owner, Admin, Developer, Viewer, Billing",
                    "Encryption: TLS 1.3 in transit; AES-256 at rest for all stored data",
                    "Secrets Management: AWS Secrets Manager for all credentials and API keys",
                    "Network: VPC with private subnets; EC2 instances not publicly accessible",
                    "WAF: AWS WAF with OWASP Core Rule Set blocking common attacks",
                    "Penetration Testing: Quarterly by certified external security firm",
                    "VAPT: Automated daily scans via Snyk (dependencies) and SonarQube (code)",
                    "Audit Logs: All API calls logged to immutable S3 with 7-year retention",
                ],
            },
            {
                "heading": "5. Deployment Guide",
                "level": 1,
                "body": (
                    "Production deployment uses Kubernetes on AWS EKS (us-east-1 primary, ap-south-1 "
                    "secondary for disaster recovery).\n\n"
                    "Prerequisites: kubectl 1.28+, helm 3.12+, AWS CLI 2.x, access to techcorp-prod cluster.\n\n"
                    "Deploy a service:\n"
                    "  helm upgrade --install documind-api ./helm/documind-api \\\n"
                    "    --namespace production \\\n"
                    "    --set image.tag=$GIT_SHA \\\n"
                    "    --set replicaCount=3 \\\n"
                    "    --values helm/values.prod.yaml\n\n"
                    "Rolling update strategy: maxSurge=1, maxUnavailable=0 (zero-downtime deploys).\n"
                    "Canary deployments: 10% traffic → 50% → 100% with automated rollback on error rate >1%."
                ),
            },
            {
                "heading": "6. Monitoring & Observability",
                "level": 1,
                "bullets": [
                    "Metrics: Prometheus + Grafana dashboards (grafana.techcorp.internal)",
                    "Logs: ELK Stack (Elasticsearch, Logstash, Kibana) — 30-day retention",
                    "Tracing: Jaeger distributed tracing (sampled at 10% in production)",
                    "Alerts: PagerDuty for P0/P1 incidents; Slack #alerts for P2/P3",
                    "SLOs: 99.97% availability, p99 latency <500ms, error rate <0.1%",
                    "On-call rotation: Engineering teams on 1-week rotation, 15-min response SLA",
                    "Incident runbooks: Stored in Confluence at docs.techcorp.internal/runbooks",
                ],
            },
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge base text file
# ─────────────────────────────────────────────────────────────────────────────

def create_knowledge_base() -> None:
    kb_path = Path("data/raw/sample_texts/knowledge_base.txt")
    kb_path.parent.mkdir(parents=True, exist_ok=True)
    kb_path.write_text(
        """\
DocuMind AI Knowledge Base
===========================

What is RAG (Retrieval-Augmented Generation)?
-----------------------------------------------
RAG is an AI architecture that combines information retrieval with language model generation.
Instead of relying solely on a model's training data, RAG first retrieves relevant documents
from a knowledge base and then uses them as context for the language model to generate
accurate, grounded answers.

RAG solves the "hallucination" problem in LLMs by anchoring responses in retrieved facts.
It also enables real-time updates to the knowledge base without retraining the model.

Key RAG Components:
- Embedding Model: Converts text into numerical vectors (e.g., OpenAI ada-002, MiniLM)
- Vector Database: Stores and searches embeddings (FAISS, Pinecone, Chroma, Weaviate)
- Retriever: Fetches the most relevant chunks for a given query
- Language Model: Generates a coherent answer from retrieved context + user question
- Prompt Template: Structures the context and question for optimal LLM performance

DocuMind AI Supported File Formats:
- PDF (.pdf) — Extracted with PyMuPDF (fitz)
- Word Documents (.docx) — Extracted with python-docx
- PowerPoint (.pptx) — Extracted with python-pptx
- Plain Text (.txt) — Direct UTF-8 reading
- CSV (.csv) — Processed with pandas
- HTML (.html) / Web URLs — Extracted with BeautifulSoup

Chunking Strategies:
- Fixed-size chunking: Split at every N characters (fast but may break context)
- Recursive chunking: Split by paragraph, then sentence, then word (preserves context)
- Semantic chunking: Split at semantic boundaries using sentence embeddings (best quality)
DocuMind uses recursive chunking with 1000-character chunks and 200-character overlap.

Vector Search Methods:
- Cosine Similarity: Measures angle between vectors (most common for text)
- Euclidean Distance: Measures absolute distance (used for dense retrieval)
- MMR (Maximal Marginal Relevance): Balances relevance AND diversity in results
DocuMind default: MMR search with fetch_k=20, lambda=0.5, returning top 5 chunks.

Performance Benchmarks (internal testing on 1000 documents):
- Average ingestion speed: 150 pages/minute
- Average query latency: 1.2 seconds (OpenAI) / 3.5 seconds (HuggingFace)
- Retrieval accuracy (Recall@5): 94.3%
- Answer faithfulness score: 0.91
- Answer relevancy score: 0.88

Cost Estimates:
- OpenAI text-embedding-ada-002: $0.0001 per 1K tokens (~$0.10 per 1000 pages)
- GPT-3.5-turbo: ~$0.002/1K tokens for a typical Q&A pair
- GPT-4: ~$0.03/1K tokens (10x better quality for complex questions)
- HuggingFace MiniLM (FREE): Zero cost, runs locally, slightly lower quality
- FAISS vector store: FREE, runs locally, handles millions of vectors

Glossary:
- LLM: Large Language Model (e.g., GPT-4, Claude, Llama)
- Embedding: Dense vector representation of text in high-dimensional space
- FAISS: Facebook AI Similarity Search — fast approximate nearest-neighbour library
- Hallucination: When an LLM generates plausible-sounding but incorrect information
- Context Window: Maximum text an LLM can process at once (e.g., GPT-4: 128K tokens)
- Token: A unit of text; roughly 4 characters or 0.75 words in English
- Grounding: Connecting LLM responses to verifiable, retrieved source documents
""",
        encoding="utf-8",
    )
    print(f"  OK  {kb_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nDocuMind AI -- Generating sample documents...\n")
    create_company_policy()
    create_product_manual()
    create_financial_report()
    create_hr_handbook()
    create_technical_docs()
    create_knowledge_base()
    print("\nAll sample documents generated successfully!")
    print(f"   Location: {OUTPUT_DIR.resolve()}\n")
