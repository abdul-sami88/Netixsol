# Khan & Associates — User Guide for Associates & Paralegals

Welcome to the **Khan & Associates AI Legal Assistant**. This platform is designed to assist attorneys, associates, and paralegals in legal research, contract review, redline comparison, and legal drafting.

---

## 1. Accessing the Web Application
1. Start the assistant server by running:
   ```powershell
   python src/app.py
   ```
2. Open your web browser and navigate to:
   ```
   http://localhost:8000
   ```

---

## 2. Using the 6 Core Modules

### 🔍 Tab 1: Legal Research & RAG
- **When to use:** Researching statutory sections, constitutional fundamental rights, or Supreme Court case law.
- **Languages supported:** English and Roman Urdu (e.g. *"Agar consideration unlawful ho to kya contract void hai?"*).
- **Key Features:**
  - Guaranteed zero fabricated citations.
  - Returns exact Act, Section, and verbatim quoted text.
  - Automatically alerts if any relevant Supreme Court decision has been overruled.
  - Refuses out-of-corpus foreign questions with *"No sufficient source found"*.

### 📋 Tab 2: Contract Playbook Review
- **When to use:** Vetting incoming vendor contracts, NDAs, or commercial agreements.
- **Workflow:**
  1. Click **Run Automated Playbook Audit**.
  2. The agent classifies each clause according to the CUAD taxonomy.
  3. Evaluates each clause against `data/firm_playbook.json` and marks with badges:
     - ✅ **Approved:** Complies with firm standards.
     - ⚠️ **Medium Risk:** Missing safeguards or non-standard terms.
     - ❌ **High Risk:** Prohibited terms (unilateral indemnity, unlimited liability, foreign governing law).
  4. Automatically lists **Missing Mandatory Clauses** (Force Majeure, Severability, etc.).
  5. Formatted Word report with redlines is exported to `outputs/contract_review_report.docx`.

### ⚖️ Tab 3: Redline & Comparison
- **When to use:** Comparing opposing counsel's redline against the firm's standard agreement.
- **Workflow:**
  1. Click **Compare V1 Standard vs V2 Vendor Markup**.
  2. The system calculates token-level additions and deletions.
  3. For every modified clause, the system generates a **Plain-Language Legal Impact Analysis** explaining the commercial and litigation risk.

### ✍️ Tab 4: Autonomous Drafting
- **When to use:** Preparing initial drafts of Case Briefs, Legal Notices, or Bespoke Clauses.
- **Available Instruments:**
  1. **Case Brief:** In-depth analysis of *2021 SCMR 105* (5-Judge Full Bench on Contract Act Section 23).
  2. **Legal Notice:** Advocate's notice demanding cure of default and liquidated damages under Contract Act Sections 73–74.
  3. **Contract Clauses:** Tailored Pakistani clauses (Arbitration Act 1940, Mutual Indemnity, Liquidated Damages under Section 74).
- **Important Rule:** Every draft is stamped with the watermark: `"DRAFT — for lawyer review"`. An Advocate must review and approve prior to external distribution.

### 🕸️ Tab 5: Knowledge Graph Explorer
- **When to use:** Visualizing precedent citations, bench compositions, and overruled cases.
- Click **Open Interactive Graph Explorer in Full Window** to open `reports/graph_visualization.html`.

### 🛡️ Tab 6: Ingestion & Security
- **When to use:** Scanning new documents before saving to matter folders.
- Sanitizes Pakistani CNICs, phone numbers, and bank IBANs in real-time.
- Scans for hidden prompt injections (Contract Trojans).

