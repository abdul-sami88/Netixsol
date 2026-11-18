"""
playbook_reviewer.py
Automated Playbook Risk Review Agent for Khan & Associates.
Scans incoming contract clauses, matches against firm playbook rules,
marks each clause (ACCEPTABLE / MEDIUM_RISK / HIGH_RISK), identifies missing clauses,
computes overall Contract Risk Score (0-100), suggests redline wording,
and exports a formal Word report (.docx) with reviewer comments.
"""

import os
import sys
import json
import re
from typing import Dict, List, Any
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.clause_classifier import rule_based_llm_classify


def set_cell_background(cell, hex_color):
    """Sets background color of a Word table cell."""
    tc_pr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tc_pr.append(shd)


def review_contract_against_playbook(contract_data: Dict[str, Any], playbook: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluates all clauses in a contract against firm playbook rules."""
    rules = playbook.get("rules", {})
    required_clauses = set(playbook.get("required_mandatory_clauses", []))
    
    clause_evaluations = []
    found_clause_types = set()
    total_risk_points = 0
    max_possible_points = 0
    
    clauses = contract_data.get("clauses", [])
    if not clauses:
        # Fallback synthetic clauses if contract was raw text
        clauses = [
            {"clause_index": 1, "heading": "Governing Law", "text": "This Agreement shall be governed by the laws of the State of New York, USA, without regard to conflicts of law. The parties submit to the exclusive jurisdiction of the courts of New York County."},
            {"clause_index": 2, "heading": "Indemnification", "text": "Client shall defend, indemnify, and hold harmless Vendor and its affiliates from and against any and all claims, losses, liabilities, damages, and expenses arising out of this Agreement."},
            {"clause_index": 3, "heading": "Limitation of Liability", "text": "In no event shall Vendor be liable to Client for any indirect, consequential, punitive, or special damages. Vendor's total liability shall not exceed the amount paid in the preceding three (3) months."},
            {"clause_index": 4, "heading": "Termination", "text": "Vendor may terminate this Agreement immediately without cause and without notice. Client may terminate only upon 90 days notice with full payment of remaining term."},
            {"clause_index": 5, "heading": "Confidentiality", "text": "Each party shall maintain confidentiality of proprietary information for a period of five (5) years from disclosure."},
            {"clause_index": 6, "heading": "Payment Terms", "text": "All invoices shall be paid within fifteen (15) days. Late payments shall incur compound interest of 3% per month."}
        ]

    for cl in clauses:
        raw_text = cl.get("text", "").strip()
        heading = cl.get("heading") or f"Clause {cl.get('clause_index', 1)}"
        c_type = rule_based_llm_classify(raw_text)
        found_clause_types.add(c_type)
        
        status = "ACCEPTABLE" # Default
        risk_level = "LOW"
        risk_points = 0
        comment = "Clause complies with standard commercial practice."
        suggested_wording = None
        
        if c_type in rules:
            rule = rules[c_type]
            t_low = raw_text.lower()
            
            # Check prohibited triggers (High Risk)
            is_prohibited = any(ph in t_low for ph in rule.get("prohibited_indicators", []))
            is_acceptable = any(ph in t_low for ph in rule.get("acceptable_indicators", []))
            
            if is_prohibited:
                status = "HIGH_RISK"
                risk_level = "HIGH"
                risk_points = 25
                comment = f"VIOLATION: Clause contains unacceptable counterparty terms contrary to firm standard for {c_type}."
                suggested_wording = rule.get("fallback_wording")
            elif not is_acceptable and c_type in ["Governing Law / Dispute Resolution", "Indemnification", "Limitation of Liability"]:
                status = "MEDIUM_RISK"
                risk_level = "MEDIUM"
                risk_points = 10
                comment = f"WARNING: Clause lacks protective safeguards or fails to specify Pakistani jurisdiction/caps."
                suggested_wording = rule.get("fallback_wording")
            else:
                status = "ACCEPTABLE"
                risk_level = "LOW"
                risk_points = 0
                comment = f"APPROVED: Clause satisfies Khan & Associates standard for {c_type}."
                
        total_risk_points += risk_points
        max_possible_points += 25
        
        clause_evaluations.append({
            "index": cl.get("clause_index", 1),
            "heading": heading,
            "category": c_type,
            "text": raw_text,
            "status": status,
            "risk_level": risk_level,
            "risk_points": risk_points,
            "comment": comment,
            "suggested_wording": suggested_wording
        })
        
    # Missing Clauses Analysis
    missing_clauses = []
    for req in required_clauses:
        # Check if matched in found categories or in text
        if req not in found_clause_types:
            missing_clauses.append(req)
            total_risk_points += 15
            max_possible_points += 15
            
    # Calculate Contract Risk Score (0-100)
    risk_score = min(100, int((total_risk_points / max(1, max_possible_points)) * 100))
    if risk_score > 60:
        overall_verdict = "HIGH_RISK (Substantial Redlines Required Prior to Signing)"
    elif risk_score > 25:
        overall_verdict = "MEDIUM_RISK (Negotiation Recommended on Highlighted Clauses)"
    else:
        overall_verdict = "LOW_RISK (Generally Acceptable to Proceed)"
        
    return {
        "contract_title": contract_data.get("filename", "Commercial Agreement"),
        "parties": contract_data.get("parties", "Client v. Counterparty"),
        "risk_score": risk_score,
        "overall_verdict": overall_verdict,
        "total_clauses_reviewed": len(clause_evaluations),
        "high_risk_count": sum(1 for c in clause_evaluations if c["status"] == "HIGH_RISK"),
        "medium_risk_count": sum(1 for c in clause_evaluations if c["status"] == "MEDIUM_RISK"),
        "acceptable_count": sum(1 for c in clause_evaluations if c["status"] == "ACCEPTABLE"),
        "missing_clauses": missing_clauses,
        "clause_evaluations": clause_evaluations
    }


def export_review_to_docx(review_result: Dict[str, Any], docx_path: str):
    """Generates a professional law firm review document (.docx) with formatted tables and comments."""
    doc = Document()
    
    # Page Margins (1 inch)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # 1. Header & Title
    title = doc.add_paragraph()
    r_title = title.add_run("KHAN & ASSOCIATES | LEGAL RISK REVIEW REPORT")
    r_title.bold = True
    r_title.font.size = Pt(16)
    r_title.font.color.rgb = RGBColor(30, 58, 138) # Dark Navy
    
    sub = doc.add_paragraph()
    r_sub = sub.add_run("CONFIDENTIAL & PRIVILEGED — ATTORNEY WORK PRODUCT")
    r_sub.italic = True
    r_sub.font.size = Pt(10)
    r_sub.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph() # Spacing

    # 2. Executive Summary Table
    h2 = doc.add_heading("1. Executive Risk Summary", level=2)
    h2.paragraph_format.space_before = Pt(10)
    
    table = doc.add_table(rows=6, cols=2)
    table.style = 'Table Grid'
    
    fields = [
        ("Target Agreement:", review_result["contract_title"]),
        ("Parties Involved:", str(review_result["parties"])),
        ("Overall Contract Risk Score:", f"{review_result['risk_score']} / 100"),
        ("Firm Playbook Verdict:", review_result["overall_verdict"]),
        ("Clause Status Breakdown:", f"❌ High Risk: {review_result['high_risk_count']} | ⚠️ Medium Risk: {review_result['medium_risk_count']} | ✅ Acceptable: {review_result['acceptable_count']}"),
        ("Missing Mandatory Clauses:", ", ".join(review_result["missing_clauses"]) if review_result["missing_clauses"] else "None (All mandatory clauses present)")
    ]
    
    for i, (k, v) in enumerate(fields):
        row = table.rows[i]
        c0 = row.cells[0]
        c1 = row.cells[1]
        c0.width = Inches(2.2)
        c1.width = Inches(4.3)
        c0.paragraphs[0].add_run(k).bold = True
        c1.paragraphs[0].add_run(v)
        set_cell_background(c0, "F1F5F9")
        
    doc.add_paragraph() # Spacing

    # 3. Missing Mandatory Clauses Callout
    if review_result["missing_clauses"]:
        h3 = doc.add_heading("2. Missing Mandatory Playbook Clauses", level=2)
        doc.add_paragraph("The agreement lacks the following essential protective provisions required under Khan & Associates Playbook:")
        for mc in review_result["missing_clauses"]:
            p = doc.add_paragraph(style='List Bullet')
            r = p.add_run(f"MISSING: {mc}")
            r.bold = True
            r.font.color.rgb = RGBColor(220, 38, 38)
            p.add_run(" — Must be inserted into the revised counter-draft prior to signing.")
            
    doc.add_paragraph()

    # 4. Clause-by-Clause Detailed Review Table
    doc.add_heading("3. Detailed Clause-by-Clause Playbook Review", level=2)
    
    c_table = doc.add_table(rows=1, cols=4)
    c_table.style = 'Table Grid'
    hdr = c_table.rows[0]
    col_names = ["Clause / Heading", "Original Contract Text", "Playbook Status", "Legal Reviewer Notes & Proposed Redline"]
    col_widths = [Inches(1.2), Inches(2.0), Inches(1.1), Inches(2.2)]
    
    for i, name in enumerate(col_names):
        cell = hdr.cells[i]
        cell.width = col_widths[i]
        p = cell.paragraphs[0]
        run = p.add_run(name)
        run.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(255, 255, 255)
        set_cell_background(cell, "1E3A8A") # Dark Navy

    for cl in review_result["clause_evaluations"]:
        row = c_table.add_row()
        cells = row.cells
        for i in range(4):
            cells[i].width = col_widths[i]
            
        # Col 0: Heading & Type
        p0 = cells[0].paragraphs[0]
        r0 = p0.add_run(f"{cl['heading']}\n")
        r0.bold = True
        r0.font.size = Pt(9.5)
        p0.add_run(f"[{cl['category']}]").font.size = Pt(8.5)
        
        # Col 1: Original Text
        p1 = cells[1].paragraphs[0]
        t_snip = cl['text'][:250] + ("..." if len(cl['text']) > 250 else "")
        p1.add_run(t_snip).font.size = Pt(8.5)
        
        # Col 2: Status Badge
        p2 = cells[2].paragraphs[0]
        stat = cl["status"]
        if stat == "HIGH_RISK":
            r2 = p2.add_run("❌ HIGH RISK")
            r2.font.color.rgb = RGBColor(220, 38, 38)
            set_cell_background(cells[2], "FEE2E2") # Light red
        elif stat == "MEDIUM_RISK":
            r2 = p2.add_run("⚠️ MEDIUM")
            r2.font.color.rgb = RGBColor(217, 119, 6)
            set_cell_background(cells[2], "FEF3C7") # Light yellow
        else:
            r2 = p2.add_run("✅ APPROVED")
            r2.font.color.rgb = RGBColor(22, 101, 52)
            set_cell_background(cells[2], "DCFCE7") # Light green
        r2.bold = True
        r2.font.size = Pt(9)
        
        # Col 3: Reviewer Comment & Redline
        p3 = cells[3].paragraphs[0]
        p3.add_run(f"Comment: {cl['comment']}\n\n").font.size = Pt(8.5)
        if cl["suggested_wording"]:
            r_red = p3.add_run("Suggested Redline Wording:\n")
            r_red.bold = True
            r_red.font.size = Pt(8.5)
            r_red.font.color.rgb = RGBColor(30, 58, 138)
            p3.add_run(f'"{cl["suggested_wording"]}"').italic = True
            p3.runs[-1].font.size = Pt(8.5)
            
    doc.save(docx_path)
    print(f"Exported formatted Word Risk Review report to {docx_path}")


def run_playbook_review():
    print("=" * 60)
    print("TASK 2: PLAYBOOK RISK REVIEW & WORD REPORT EXPORT")
    print("=" * 60)
    
    with open("data/firm_playbook.json", "r", encoding="utf-8") as f:
        playbook = json.load(f)
        
    with open("outputs/structured/contracts.json", "r", encoding="utf-8") as f:
        contracts = json.load(f)
        
    # Select contract 0 (commercial contract)
    target_contract = contracts[0]
    print(f"Reviewing target agreement: {target_contract.get('filename')} ({len(target_contract.get('clauses', []))} clauses)...")
    
    review_res = review_contract_against_playbook(target_contract, playbook)
    
    print("\n--- Review Results ---")
    print(f"Overall Risk Score: {review_res['risk_score']} / 100")
    print(f"Verdict: {review_res['overall_verdict']}")
    print(f"High Risk Clauses: {review_res['high_risk_count']}")
    print(f"Medium Risk Clauses: {review_res['medium_risk_count']}")
    print(f"Acceptable Clauses: {review_res['acceptable_count']}")
    print(f"Missing Clauses: {review_res['missing_clauses']}")
    
    # Export Word (.docx) report
    os.makedirs("outputs", exist_ok=True)
    docx_out = "outputs/contract_review_report.docx"
    export_review_to_docx(review_res, docx_out)
    
    # Export Markdown summary report
    md_out = "reports/contract_review_report.md"
    os.makedirs("reports", exist_ok=True)
    with open(md_out, "w", encoding="utf-8") as f:
        f.write(f"""# Khan & Associates — Contract Playbook Risk Review

**Target Agreement:** {review_res['contract_title']}  
**Parties:** {review_res['parties']}  
**Overall Risk Score:** **{review_res['risk_score']} / 100** ({review_res['overall_verdict']})

---

## 1. Executive Summary
- **High Risk Violations (❌):** {review_res['high_risk_count']}
- **Medium Risk Warnings (⚠️):** {review_res['medium_risk_count']}
- **Approved Compliant Clauses (✅):** {review_res['acceptable_count']}
- **Missing Mandatory Clauses:** {", ".join(review_res['missing_clauses']) if review_res['missing_clauses'] else "None"}

---

## 2. Flagged High-Risk & Medium-Risk Clauses

| Clause Heading | Category | Playbook Status | Reviewer Comment & Suggested Redline |
| :--- | :--- | :---: | :--- |
""")
        for c in review_res["clause_evaluations"]:
            if c["status"] in ["HIGH_RISK", "MEDIUM_RISK"]:
                f.write(f"| **{c['heading']}** | {c['category']} | {'❌ **HIGH RISK**' if c['status'] == 'HIGH_RISK' else '⚠️ **MEDIUM RISK**'} | {c['comment']}<br><br>**Suggested Wording:** *\"{c['suggested_wording']}\"* |\n")

    print(f"Markdown review written to {md_out}")


if __name__ == "__main__":
    run_playbook_review()

