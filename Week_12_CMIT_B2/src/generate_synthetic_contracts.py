"""Generate 20 synthetic Pakistani-law contracts as structured PDFs (with clauses and tables)."""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


OUT_DIR = Path("data_sources/contracts/synthetic")

CONTRACTS = [
    ("01_employment_agreement_lahore.pdf", "EXECUTIVE EMPLOYMENT AGREEMENT", "Khan & Associates (Law Firm)", "Bilal Ahmed, Advocate High Court", "Lahore, Punjab", "PKR 250,000 / month", "Section 4 of the Contract Act, 1872 and Punjab Shops and Establishments Ordinance, 1969"),
    ("02_commercial_lease_deed_karachi.pdf", "COMMERCIAL OFFICE LEASE DEED", "Clifton Realty Holdings (Pvt.) Ltd.", "Crescent Tech Solutions (Pvt.) Ltd.", "Karachi, Sindh", "PKR 450,000 / month", "Transfer of Property Act, 1882 and Sindh Rented Premises Ordinance, 1979"),
    ("03_software_development_msa_islamabad.pdf", "MASTER SOFTWARE DEVELOPMENT AGREEMENT", "Indus FinTech Systems (Pvt.) Ltd.", "PakCloud Engineering Services", "Islamabad Capital Territory", "PKR 6,500,000 total", "Contract Act, 1872 and Electronic Transactions Ordinance, 2002"),
    ("04_mutual_nda_rawalpindi.pdf", "MUTUAL NON-DISCLOSURE AGREEMENT", "Margalla Defence Systems Ltd.", "Potohar Analytics (Pvt.) Ltd.", "Rawalpindi, Punjab", "Liquidated damages PKR 2,000,000", "Contract Act, 1872 (Section 74)"),
    ("05_supply_procurement_faisalabad.pdf", "TEXTILE YARN SUPPLY AND PROCUREMENT AGREEMENT", "Chenab Spinning Mills Ltd.", "Ravi Apparel Exports (Pvt.) Ltd.", "Faisalabad, Punjab", "PKR 12,800,000 per quarter", "Sale of Goods Act, 1930 and Contract Act, 1872"),
    ("06_legal_retainer_agreement_lahore.pdf", "ANNUAL CORPORATE LEGAL RETAINER AGREEMENT", "Al-Noor Pharmaceutical Industries Ltd.", "Khan & Associates (Advocates & Legal Consultants)", "Lahore, Punjab", "PKR 180,000 / month", "Legal Practitioners and Bar Councils Act, 1973 and Contract Act, 1872"),
    ("07_it_consultancy_agreement_karachi.pdf", "CYBERSECURITY AUDIT & CONSULTANCY CONTRACT", "Karachi Microfinance Bank Ltd.", "ShieldSec Advisory (Pvt.) Ltd.", "Karachi, Sindh", "PKR 3,200,000 fixed fee", "Prevention of Electronic Crimes Act, 2016 and Contract Act, 1872"),
    ("08_shareholders_agreement_islamabad.pdf", "SHAREHOLDERS AND GOVERNANCE AGREEMENT", "Zainab Tariq & Hamza Malik (Founders)", "Capital Venture Partners Pakistan", "Islamabad Capital Territory", "PKR 40,000,000 equity subscription", "Companies Act, 2017 and Contract Act, 1872"),
    ("09_franchise_agreement_multan.pdf", "RETAIL FRANCHISE & TRADEMARK LICENSE AGREEMENT", "Lahore Heritage Foods (Pvt.) Ltd.", "Multan Hospitality Group", "Multan, Punjab", "PKR 1,500,000 upfront + 6% royalty", "Trade Marks Ordinance, 2001 and Contract Act, 1872"),
    ("10_logistics_services_sialkot.pdf", "FREIGHT FORWARDING AND LOGISTICS SERVICES AGREEMENT", "Sialkot Surgical Instruments Co.", "SwiftPort Logistics (Pvt.) Ltd.", "Sialkot, Punjab", "PKR 950,000 monthly minimum", "Carriage of Goods by Sea / Road Laws and Contract Act, 1872"),
    ("11_equipment_lease_peshawar.pdf", "INDUSTRIAL GENERATOR EQUIPMENT LEASE AGREEMENT", "Khyber Power Rentals (Pvt.) Ltd.", "Frontier Medical Complex", "Peshawar, Khyber Pakhtunkhwa", "PKR 320,000 / month", "Contract Act, 1872 and Specific Relief Act, 1877"),
    ("12_joint_venture_construction_quetta.pdf", "CONSORTIUM AND JOINT VENTURE AGREEMENT", "Bolan Civil Contractors Ltd.", "Makran Infrastructure Associates", "Quetta, Balochistan", "PKR 85,000,000 project share (60/40)", "Partnership Act, 1932 and Contract Act, 1872"),
    ("13_exclusive_distribution_lahore.pdf", "EXCLUSIVE PHARMACEUTICAL DISTRIBUTION AGREEMENT", "MedCare Laboratories Pakistan Ltd.", "Punjab Health Distributors", "Lahore, Punjab", "PKR 15,000,000 annual target", "Competition Act, 2010 and Contract Act, 1872"),
    ("14_saas_subscription_karachi.pdf", "ENTERPRISE CLOUD SAAS SUBSCRIPTION AGREEMENT", "BazaarCloud Technologies (Pvt.) Ltd.", "Sindh Retail Mart Ltd.", "Karachi, Sindh", "PKR 1,200,000 / year", "Contract Act, 1872 and Electronic Transactions Ordinance, 2002"),
    ("15_residential_tenancy_islamabad.pdf", "RESIDENTIAL TENANCY AND LEASE AGREEMENT", "Brig. (R) Tariq Mehmood (Landlord)", "Dr. Ayesha Siddiqui (Tenant)", "Sector F-7/2, Islamabad", "PKR 220,000 / month", "Islamabad Rent Restriction Ordinance, 2001"),
    ("16_working_capital_facility_karachi.pdf", "CORPORATE WORKING CAPITAL LOAN FACILITY AGREEMENT", "Meezan Commercial Credit Co.", "Harbour Cold Storage (Pvt.) Ltd.", "Karachi, Sindh", "PKR 25,000,000 principal facility", "Financial Institutions (Recovery of Finances) Ordinance, 2001"),
    ("17_ip_assignment_lahore.pdf", "INTELLECTUAL PROPERTY ASSIGNMENT & WORK-FOR-HIRE DEED", "Saad Farooq (Independent Architect)", "UrbanEdge Developers (Pvt.) Ltd.", "Lahore, Punjab", "PKR 1,850,000 lump sum", "Copyright Ordinance, 1962 and Contract Act, 1872"),
    ("18_solar_epc_subcontract_gujranwala.pdf", "SOLAR EPC INSTALLATION SUBCONTRACT AGREEMENT", "GreenGrid Energy Pakistan", "Gujranwala Steel Works Ltd.", "Gujranwala, Punjab", "PKR 18,400,000 turnkey", "Contract Act, 1872 and Alternative Dispute Resolution Act, 2017"),
    ("19_vendor_sla_islamabad.pdf", "MANAGED DATA CENTER & SLA AGREEMENT", "PakNet Hosting Infrastructure Ltd.", "National Agri-Data Portal", "Islamabad Capital Territory", "PKR 540,000 / month", "Contract Act, 1872 and Arbitration Act, 1940"),
    ("20_non_compete_settlement_lahore.pdf", "SEPARATION, CONFIDENTIALITY & NON-SOLICITATION DEED", "Apex Consulting Partners Pakistan", "Usman Raza (Former Senior Partner)", "Lahore, Punjab", "PKR 3,500,000 severance consideration", "Contract Act, 1872 (Sections 27 and 73)"),
]


def build_contract_pdf(spec: tuple[str, ...]) -> None:
    fname, title, party_a, party_b, city, value, governing_law = spec
    dest = OUT_DIR / fname
    styles = getSampleStyleSheet()
    heading = ParagraphStyle("ClauseHead", parent=styles["Heading3"], spaceBefore=8, spaceAfter=4)
    body = styles["Normal"]

    doc = SimpleDocTemplate(str(dest), pagesize=A4, leftMargin=48, rightMargin=48, topMargin=44, bottomMargin=44)
    story = [
        Paragraph(f"<b>{title}</b>", styles["Title"]),
        Spacer(1, 8),
        Paragraph(
            f"This {title.title()} ('Agreement') is executed at <b>{city}</b> on 15th January 2025 "
            f"by and between <b>{party_a}</b> ('First Party') and <b>{party_b}</b> ('Second Party'), "
            f"collectively referred to as the 'Parties'.",
            body,
        ),
        Spacer(1, 10),
        Paragraph("1. DEFINITIONS AND INTERPRETATION", heading),
        Paragraph(
            "1.1 'Confidential Information' means all proprietary technical, financial, client, and legal data "
            "disclosed by either Party during the term of this Agreement.<br/>"
            "1.2 'Effective Date' means 15th January 2025 unless otherwise extended in writing by the Parties.",
            body,
        ),
        Paragraph("2. SCOPE OF OBLIGATIONS AND CONSIDERATION", heading),
        Paragraph(
            f"2.1 The Second Party shall perform the deliverables and obligations described in Schedule A in "
            f"strict compliance with industry standards applicable in {city}.<br/>"
            f"2.2 In consideration thereof, the agreed commercial value is <b>{value}</b>, payable net 15 days "
            f"from receipt of an undisputed tax invoice under Pakistan tax regulations.",
            body,
        ),
        Spacer(1, 8),
        Paragraph("SCHEDULE A: COMMERCIAL MILESTONES AND PAYMENT TABLE", heading),
    ]

    table_data = [
        ["Milestone / Item", "Deliverable Description", "Timeline", "Fee / Allocation", "Tax Withholding"],
        ["Milestone 1", "Execution & Mobilization / Onboarding", "Day 1 - Day 15", "30% of Value", "As per Income Tax Ord. 2001"],
        ["Milestone 2", "Core Performance / Interim Delivery", "Day 16 - Day 60", "40% of Value", "As per Income Tax Ord. 2001"],
        ["Milestone 3", "Final Acceptance & Handover Sign-off", "Day 61 - Day 90", "30% of Value", "Final Reconciliation"],
    ]
    tbl = Table(table_data, colWidths=[78, 155, 82, 85, 95])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f7f9fc")),
            ]
        )
    )
    story.extend(
        [
            tbl,
            Spacer(1, 10),
            Paragraph("3. REPRESENTATIONS, WARRANTIES AND INDEMNITY", heading),
            Paragraph(
                "3.1 Each Party represents that it holds full corporate authority and legal capacity under the "
                "laws of Pakistan to enter into this Agreement.<br/>"
                "3.2 Each Party shall indemnify and hold harmless the other against third-party claims arising from "
                "gross negligence, willful misconduct, or breach of statutory obligations.",
                body,
            ),
            Paragraph("4. LIMITATION OF LIABILITY", heading),
            Paragraph(
                "4.1 Except for breaches of confidentiality or indemnity obligations, neither Party shall be liable "
                "for indirect, incidental, or consequential damages. Aggregate liability shall not exceed total "
                "fees paid or payable during the preceding twelve (12) months.",
                body,
            ),
            Paragraph("5. TERM, TERMINATION AND FORCE MAJEURE", heading),
            Paragraph(
                "5.1 This Agreement remains valid for twelve (12) months from the Effective Date and may be "
                "terminated for convenience upon thirty (30) days' prior written notice.<br/>"
                "5.2 Either Party may terminate immediately upon material breach not cured within fourteen (14) "
                "days of written notice. Force Majeure events suspend performance for up to forty-five (45) days.",
                body,
            ),
            Paragraph("6. GOVERNING LAW AND DISPUTE RESOLUTION", heading),
            Paragraph(
                f"6.1 This Agreement shall be governed by and construed in accordance with the <b>{governing_law}</b>.<br/>"
                f"6.2 Any dispute not resolved amicably within fifteen (15) days shall be referred to arbitration "
                f"under the Arbitration Act, 1940 seated at <b>{city}</b>, and the courts at {city} shall have "
                f"exclusive jurisdiction.",
                body,
            ),
            Spacer(1, 14),
            Paragraph(f"IN WITNESS WHEREOF, the Parties sign below at {city}.", body),
            Spacer(1, 10),
            Paragraph(f"For {party_a}: ______________________     For {party_b}: ______________________", body),
        ]
    )
    doc.build(story)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for spec in CONTRACTS:
        build_contract_pdf(spec)
    print(f"Generated {len(CONTRACTS)} synthetic Pakistani contracts in {OUT_DIR}")


if __name__ == "__main__":
    main()

