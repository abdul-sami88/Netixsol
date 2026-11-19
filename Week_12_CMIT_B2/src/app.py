"""
app.py
Day 5 Capstone: Production FastAPI Application & Unified Legal Web App.
Includes:
- Health checks (/health, /health/ready, /health/live)
- REST API endpoints for Research, Review, Compare, Draft, Graph, and Upload
- Security Firewall integration (Ethical Walls, PII Masking, Prompt Injection Defense)
- Embedded HTML5 Web Application with tabs for Research, Review, Compare, Draft, Graph, and Upload
"""

import os
import sys
import json
import hashlib
from typing import Dict, List, Any, Optional
import io
import re
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Header, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.graph_rag import LegalGraphRAG
from src.query_router import LegalQueryRouter
from src.security_firewall import SecurityFirewall
from src.playbook_reviewer import review_contract_against_playbook
from src.contract_comparator import compare_contracts, CONTRACT_V1_ORIGINAL, CONTRACT_V2_COUNTERPARTY_REDLINE
from src.drafting_agent import (
    draft_case_brief,
    draft_legal_notice,
    draft_contract_clauses,
    draft_commercial_nda,
    draft_employment_noncompete
)

app = FastAPI(
    title="Khan & Associates AI Legal Assistant API",
    description="Production Legal Intelligence, Contract Review, GraphRAG, and Security Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
firewall = SecurityFirewall()
graph_rag = LegalGraphRAG()
router = LegalQueryRouter()

with open("data/firm_playbook.json", "r", encoding="utf-8") as f:
    playbook_data = json.load(f)


# --- Request Models ---
class ResearchRequest(BaseModel):
    query: str
    matter_id: Optional[str] = "KA-MATTER-101"
    user_id: Optional[str] = "attorney_ahmed"


class ContractReviewRequest(BaseModel):
    contract_title: str
    clauses: List[Dict[str, Any]]
    matter_id: Optional[str] = "KA-MATTER-101"
    user_id: Optional[str] = "attorney_ahmed"


class CustomCompareRequest(BaseModel):
    v1_title: Optional[str] = "Version 1 (Client Standard)"
    v1_text: Optional[str] = None
    v1_clauses: Optional[List[Dict[str, Any]]] = None
    v2_title: Optional[str] = "Version 2 (Counterparty Redline)"
    v2_text: Optional[str] = None
    v2_clauses: Optional[List[Dict[str, Any]]] = None
    matter_id: Optional[str] = "KA-MATTER-101"
    user_id: Optional[str] = "attorney_ahmed"


class ExportDocxRequest(BaseModel):
    title: str
    content: str
    watermark: Optional[bool] = True
    doc_type: Optional[str] = "legal_draft"


class UploadScanRequest(BaseModel):
    filename: str
    content: str
    matter_id: Optional[str] = "KA-MATTER-101"
    user_id: Optional[str] = "attorney_ahmed"


class MatterCreateRequest(BaseModel):
    matter_id: str
    title: str
    client_name: str
    jurisdiction: Optional[str] = "Islamabad High Court"
    practice_area: Optional[str] = "Commercial Litigation"
    lead_counsel: Optional[str] = "Khan & Associates"


def parse_raw_text_to_clauses(text: str, filename: str = "Uploaded_Contract.txt") -> List[Dict[str, Any]]:
    pattern = r'(?m)(^(?:Clause\s+\d+|Section\s+\d+|\d+\.\d+|\d+\.)[^\n]*)'
    splits = re.split(pattern, text)
    clauses = []
    if len(splits) > 1:
        if splits[0].strip():
            clauses.append({
                "clause_number": "Preamble",
                "clause_index": 1,
                "title": "Preamble & Recitals",
                "heading": "Preamble",
                "text": splits[0].strip()
            })
        for i in range(1, len(splits), 2):
            heading = splits[i].strip()
            body = splits[i+1].strip() if i+1 < len(splits) else ""
            m_num = re.match(r'^((?:Clause\s+)?\d+(?:\.\d+)?|\d+\.)', heading, re.IGNORECASE)
            c_num = m_num.group(1).strip() if m_num else f"{len(clauses)+1}.0"
            c_title = re.sub(r'^((?:Clause\s+)?\d+(?:\.\d+)?|\d+\.)\s*', '', heading).strip() or heading
            clauses.append({
                "clause_number": c_num,
                "clause_index": len(clauses)+1,
                "title": c_title,
                "heading": heading,
                "text": f"{heading}\n{body}".strip()
            })
    else:
        paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        for idx, p in enumerate(paras, 1):
            first_line = p.split("\n")[0][:45]
            clauses.append({
                "clause_number": f"{idx}.0",
                "clause_index": idx,
                "title": first_line or f"Clause {idx}",
                "heading": f"Clause {idx}",
                "text": p
            })
    return clauses


# --- Health Check Endpoints ---
@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "version": "1.0.0", "timestamp": "2026-11-16T12:00:00Z"}


@app.get("/health/ready")
def readiness_check():
    # Verify graph and playbook loaded
    nodes = graph_rag.engine.G.number_of_nodes()
    return {"status": "READY", "graph_nodes": nodes, "playbook_rules": len(playbook_data["rules"])}


@app.get("/health/live")
def liveness_check():
    return {"status": "LIVE"}


# --- Core Legal API Endpoints ---
@app.post("/api/research")
def research_endpoint(req: ResearchRequest):
    # 1. Security & Ethical Wall Check
    allowed, reason = firewall.enforce_matter_access_control(req.user_id, req.matter_id)
    if not allowed:
        raise HTTPException(status_code=403, detail=reason)
        
    # 2. Prompt Injection Defense
    is_safe, msg = firewall.scan_for_prompt_injection(req.query, req.user_id, req.matter_id)
    if not is_safe:
        return {
            "query": req.query,
            "status": "BLOCKED",
            "short_answer": "Request blocked by Security Firewall: Adversarial Prompt Injection detected.",
            "explanation": msg,
            "citations": []
        }
        
    # 3. Route & Answer
    route = router.route(req.query)
    ans = graph_rag.answer_query(req.query)
    
    # 4. PII Sanitization
    clean_explanation, pii_count = firewall.mask_pii(ans["explanation"])
    ans["explanation"] = clean_explanation
    ans["routed_engine"] = route["engine"]
    ans["route_confidence"] = route["confidence"]
    
    return ans


@app.post("/api/review")
def review_endpoint(req: ContractReviewRequest):
    allowed, reason = firewall.enforce_matter_access_control(req.user_id, req.matter_id)
    if not allowed:
        raise HTTPException(status_code=403, detail=reason)
        
    contract_data = {
        "filename": req.contract_title,
        "clauses": req.clauses
    }
    review_res = review_contract_against_playbook(contract_data, playbook_data)
    return review_res


@app.get("/api/compare")
def compare_endpoint():
    diff_res = compare_contracts(CONTRACT_V1_ORIGINAL, CONTRACT_V2_COUNTERPARTY_REDLINE)
    return diff_res


@app.get("/api/draft/{doc_type}")
def draft_endpoint(doc_type: str):
    doc_type_clean = doc_type.lower().strip()
    if doc_type_clean == "case_brief":
        return {"doc_type": "case_brief", "title": "Supreme Court Appellate Case Brief", "watermark": "DRAFT — for lawyer review", "content": draft_case_brief()}
    elif doc_type_clean == "legal_notice":
        return {"doc_type": "legal_notice", "title": "Advocate's Formal Legal Notice", "watermark": "DRAFT — for lawyer review", "content": draft_legal_notice()}
    elif doc_type_clean == "clauses":
        return {"doc_type": "clauses", "title": "Bespoke Contract Clauses", "watermark": "DRAFT — for lawyer review", "content": draft_contract_clauses()}
    elif doc_type_clean in ["commercial_nda", "nda"]:
        return {"doc_type": "commercial_nda", "title": "Commercial Non-Disclosure Agreement", "watermark": "DRAFT — for lawyer review", "content": draft_commercial_nda()}
    elif doc_type_clean in ["employment_noncompete", "noncompete"]:
        return {"doc_type": "employment_noncompete", "title": "Employment Non-Compete & IP Covenant", "watermark": "DRAFT — for lawyer review", "content": draft_employment_noncompete()}
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid doc_type '{doc_type}'. Choose: legal_notice, case_brief, commercial_nda, employment_noncompete, clauses"
        )


@app.post("/api/upload")
def upload_endpoint(req: UploadScanRequest):
    allowed, reason = firewall.enforce_matter_access_control(req.user_id, req.matter_id)
    if not allowed:
        raise HTTPException(status_code=403, detail=reason)
        
    # Scan for Trojan injections
    is_safe, msg = firewall.scan_for_prompt_injection(req.content, req.user_id, req.matter_id)
    if not is_safe:
        return {"filename": req.filename, "status": "REJECTED_SECURITY_VIOLATION", "message": msg}
        
    # Mask PII
    sanitized_content, pii_count = firewall.mask_pii(req.content)
    
    return {
        "filename": req.filename,
        "matter_id": req.matter_id,
        "status": "ACCEPTED_AND_SANITIZED",
        "pii_redactions_applied": pii_count,
        "content_length": len(sanitized_content)
    }


# --- Static Report & File Serving ---
@app.get("/reports/{filename:path}")
def serve_report(filename: str):
    # Handle typos / aliases
    normalized = filename.replace("contraact_", "contract_")
    if normalized == "contraact_comparison.md" or normalized == "contract_comparison.md":
        normalized = "contract_comparison_report.md"
        
    file_path = os.path.join("reports", normalized)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    # Check if exact filename exists
    exact_path = os.path.join("reports", filename)
    if os.path.exists(exact_path):
        return FileResponse(exact_path)
    raise HTTPException(status_code=404, detail=f"Report '{filename}' not found")


@app.get("/outputs/{filename:path}")
def serve_output(filename: str):
    file_path = os.path.join("outputs", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail=f"Output file '{filename}' not found")


# --- Contract Ingestion & Parsing API ---
@app.post("/api/upload_and_parse")
async def upload_and_parse(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    contract_name: Optional[str] = Form(None),
    matter_id: Optional[str] = Form("KA-MATTER-101"),
    user_id: Optional[str] = Form("attorney_ahmed")
):
    filename = contract_name or "uploaded_agreement.txt"
    full_text = ""
    
    if file and file.filename:
        filename = file.filename
        content_bytes = await file.read()
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == ".docx":
            import docx
            doc = docx.Document(io.BytesIO(content_bytes))
            full_text = "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        elif ext == ".pdf":
            import fitz
            doc = fitz.open(stream=content_bytes, filetype="pdf")
            full_text = "\n\n".join([page.get_text() for page in doc])
        else:
            full_text = content_bytes.decode("utf-8", errors="ignore")
    elif raw_text:
        full_text = raw_text
        
    if not full_text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in uploaded document or text area.")
        
    # --- Security Gate 1: Ethical Wall Enforcement ---
    allowed, auth_reason = firewall.enforce_matter_access_control(user_id, matter_id)
    if not allowed:
        raise HTTPException(status_code=403, detail=auth_reason)

    # --- Security Gate 2: Contract Trojan & Prompt Injection Scanner ---
    is_safe, trojan_msg = firewall.scan_for_prompt_injection(full_text, user_id, matter_id)
    if not is_safe:
        raise HTTPException(status_code=400, detail=f"SECURITY FIREWALL INTERCEPT: {trojan_msg}")

    # --- Security Gate 3: Pakistani PII Masking (CNIC, Mobile, IBAN) ---
    sanitized_text, pii_count = firewall.mask_pii(full_text)

    # --- Security Gate 4: Parse Sanitized Text into Structured Clauses ---
    clauses = parse_raw_text_to_clauses(sanitized_text, filename)

    # --- Security Gate 5: Tamper-Evident SHA-256 Audit Event ---
    firewall.log_audit_event(
        user_id=user_id,
        matter_id=matter_id,
        action="PLAYBOOK_DOC_UPLOAD",
        pii_count=pii_count,
        injection=False,
        allowed=True,
        details=f"Document '{filename}' scanned & approved. {len(clauses)} clauses parsed, {pii_count} PII items masked."
    )

    return {
        "filename": filename,
        "clause_count": len(clauses),
        "character_count": len(full_text),
        "clauses": clauses,
        "security_status": "VERIFIED_SAFE",
        "pii_redactions": pii_count,
        "security_details": trojan_msg
    }


@app.get("/api/matters")
def get_matters():
    matters_file = os.path.join("outputs", "matters.json")
    if os.path.exists(matters_file):
        try:
            with open(matters_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


@app.post("/api/matters")
def create_matter(req: MatterCreateRequest):
    matters_file = os.path.join("outputs", "matters.json")
    matters = get_matters()
    
    # Check if duplicate matter_id
    clean_id = req.matter_id.strip().upper()
    for m in matters:
        if m.get("matter_id", "").upper() == clean_id:
            return m
            
    new_matter = {
        "matter_id": clean_id,
        "title": req.title.strip(),
        "display": f"{req.title.strip()} ({clean_id})",
        "client_name": req.client_name.strip(),
        "jurisdiction": req.jurisdiction.strip() if req.jurisdiction else "Islamabad High Court",
        "practice_area": req.practice_area.strip() if req.practice_area else "Commercial Dispute",
        "status": "ACTIVE"
    }
    matters.insert(0, new_matter)
    
    # Register in firewall authorization matrix
    try:
        if "partner_khan" in firewall.user_matter_authorizations:
            firewall.user_matter_authorizations["partner_khan"].append(clean_id)
        if "attorney_ahmed" in firewall.user_matter_authorizations:
            firewall.user_matter_authorizations["attorney_ahmed"].append(clean_id)
    except Exception:
        pass
        
    os.makedirs("outputs", exist_ok=True)
    with open(matters_file, "w", encoding="utf-8") as f:
        json.dump(matters, f, indent=2)
        
    return new_matter


def _clean_contract_title(fn: str, i: int) -> str:
    base = os.path.splitext(fn)[0]
    parts = base.split("-")
    if len(parts) >= 2:
        raw_doc = parts[-1].strip()
        raw_doc = re.sub(r'^[0-9A-Za-z\._]+\s*_', '', raw_doc).strip().title()
        co = parts[0].split("_")[0]
        co_spaced = re.sub(r'([A-Z][a-z]+)', r' \1', co).strip().title()
        if not co_spaced:
            co_spaced = co.title()
        if len(raw_doc) > 3:
            return f"{raw_doc} ({co_spaced})"
    return base.replace("_", " ").replace("-", " ").title()[:55]


@app.get("/api/contracts_list")
def get_contracts_list():
    c_file = "outputs/structured/contracts.json"
    if os.path.exists(c_file):
        with open(c_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        contracts = []
        for i, c in enumerate(data[:50]):
            fn = c.get("filename", f"Contract_{i+1}")
            title = _clean_contract_title(fn, i)
            c_count = len(c.get("clauses", []))
            contracts.append({
                "index": i,
                "title": title,
                "filename": fn,
                "clause_count": c_count,
                "clauses_count": c_count,
                "governing_law": c.get("governing_law", "Pakistan Law"),
                "parties": c.get("parties", [])
            })
        return contracts
    return []


@app.get("/api/contracts/{index}")
def get_contract_detail(index: int):
    c_file = "outputs/structured/contracts.json"
    if os.path.exists(c_file):
        with open(c_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if 0 <= index < len(data):
            contract = dict(data[index])
            fn = contract.get("filename", f"Contract_{index+1}")
            contract["title"] = _clean_contract_title(fn, index)
            contract["clause_count"] = len(contract.get("clauses", []))
            contract["clauses_count"] = len(contract.get("clauses", []))
            
            # Ensure mapped clauses have clause_type and text for playbook review
            mapped_clauses = []
            for j, cl in enumerate(contract.get("clauses", [])):
                heading = cl.get("heading") or cl.get("category") or f"Clause {j+1}"
                mapped_clauses.append({
                    "clause_number": f"{j+1}.0",
                    "clause_index": j + 1,
                    "title": heading,
                    "heading": heading,
                    "clause_type": cl.get("category") or heading,
                    "text": cl.get("text", "")
                })
            contract["clauses"] = mapped_clauses
            return contract
    raise HTTPException(status_code=404, detail="Contract not found in firm repository")


@app.post("/api/compare_custom")
def compare_custom_endpoint(req: CustomCompareRequest):
    v1_clauses = req.v1_clauses
    if not v1_clauses and req.v1_text:
        v1_clauses = parse_raw_text_to_clauses(req.v1_text, "v1_original.txt")
    if not v1_clauses:
        v1_clauses = CONTRACT_V1_ORIGINAL

    v2_clauses = req.v2_clauses
    if not v2_clauses and req.v2_text:
        v2_clauses = parse_raw_text_to_clauses(req.v2_text, "v2_counterparty.txt")
    if not v2_clauses:
        v2_clauses = CONTRACT_V2_COUNTERPARTY_REDLINE

    diff_res = compare_contracts(v1_clauses, v2_clauses)
    return diff_res


@app.post("/api/export_draft_docx")
def export_draft_docx(req: ExportDocxRequest):
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = docx.Document()
    
    # Configure 1-inch margins
    for sec in doc.sections:
        sec.top_margin = Inches(1.0)
        sec.bottom_margin = Inches(1.0)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(1.0)

    # Formal Letterhead
    p_hdr = doc.add_paragraph()
    r1 = p_hdr.add_run("KHAN & ASSOCIATES | ADVOCATES & CORPORATE COUNSEL\n")
    r1.font.bold = True
    r1.font.size = Pt(13)
    r1.font.color.rgb = RGBColor(30, 58, 138)

    r2 = p_hdr.add_run("Supreme Court & High Court Bar Association Buildings, Islamabad, Pakistan")
    r2.font.size = Pt(9)
    r2.font.color.rgb = RGBColor(100, 116, 139)
    p_hdr.alignment = WD_ALIGN_PARAGRAPH.CENTER

    if req.watermark:
        p_wm = doc.add_paragraph()
        r_wm = p_wm.add_run("⚠️ DRAFT — FOR LAWYER REVIEW ONLY")
        r_wm.font.bold = True
        r_wm.font.size = Pt(10)
        r_wm.font.color.rgb = RGBColor(180, 83, 9)
        p_wm.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p_div = doc.add_paragraph("—" * 45)
    p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Document Title
    t_head = doc.add_heading(req.title, level=1)
    t_head.runs[0].font.color.rgb = RGBColor(15, 23, 42)

    # Structured Document Lines
    for line in req.content.split("\n"):
        line_s = line.strip()
        if not line_s:
            continue
        if line_s.startswith("### "):
            h = doc.add_heading(line_s[4:], level=3)
            h.runs[0].font.color.rgb = RGBColor(30, 58, 138)
        elif line_s.startswith("## "):
            h = doc.add_heading(line_s[3:], level=2)
            h.runs[0].font.color.rgb = RGBColor(15, 23, 42)
        elif line_s.startswith("# "):
            h = doc.add_heading(line_s[2:], level=1)
        elif line_s.startswith("- ") or line_s.startswith("* "):
            doc.add_paragraph(line_s[2:], style="List Bullet")
        else:
            doc.add_paragraph(line_s)

    out_file = os.path.join("outputs", "lawyer_custom_draft.docx")
    doc.save(out_file)
    clean_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', req.title)
    return FileResponse(
        out_file,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{clean_title}.docx"
    )


@app.get("/api/audit_logs")
def get_audit_logs():
    log_path = "outputs/security_audit_log.jsonl"
    logs = []
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        if "sha256" not in entry:
                            # Compute real cryptographic SHA-256 hash for historical entry
                            entry["sha256"] = hashlib.sha256(line.encode("utf-8")).hexdigest()
                        logs.append(entry)
                    except Exception:
                        pass
    return logs[::-1][:100]


# Mount static assets
if not os.path.exists("static"):
    os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Production Single Page Application Entrypoint ---
@app.get("/", response_class=FileResponse)
def index_web_app():
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Khan & Associates Legal Tech Suite</h1><p>Frontend static assets loading...</p>")


if __name__ == "__main__":
    import uvicorn
    print("Starting Khan & Associates AI Legal Assistant API on port 8000...")
    uvicorn.run("src.app:app", host="127.0.0.1", port=8000, reload=False)

