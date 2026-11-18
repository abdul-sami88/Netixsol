# Day 3: Legal Knowledge Graph Schema & Ontology

## 1. Graph Overview
The **Khan & Associates Legal Knowledge Graph (LKG)** is designed to capture complex relational, precedential, and hierarchical structures in Pakistani law that flat vector embeddings cannot resolve.

### Core Objectives:
1. **Multi-Hop Precedent Tracing:** Trace how Supreme Court judgments cite, follow, distinguish, or overrule earlier decisions.
2. **Statutory Interpretation Grounding:** Connect specific judicial holdings to the exact legislative Sections and Acts they interpret.
3. **Overruling & Bad Law Detection:** Instantly identify whether a cited precedent has been overruled or modified by a larger bench.
4. **Contract Compliance Verification:** Link contractual clauses to governing statutory sections and judicial interpretations.

---

## 2. Graph Schema Diagram

```mermaid
graph TD
    classDef act fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef section fill:#0284c7,stroke:#38bdf8,stroke-width:2px,color:#fff;
    classDef case fill:#b45309,stroke:#f59e0b,stroke-width:2px,color:#fff;
    classDef court fill:#4338ca,stroke:#6366f1,stroke-width:2px,color:#fff;
    classDef judge fill:#047857,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef party fill:#6b7280,stroke:#9ca3af,stroke-width:2px,color:#fff;
    classDef contract fill:#7c2d12,stroke:#ea580c,stroke-width:2px,color:#fff;
    classDef clause fill:#c2410c,stroke:#fb923c,stroke-width:2px,color:#fff;

    Act[Act / Statute]::act
    Section[Section / Article]::section
    Case[Case / Judgment]::case
    Court[Court]::court
    Judge[Judge / Justice]::judge
    Party[Party]::party
    Contract[Contract]::contract
    Clause[Clause]::clause

    Section -->|PART_OF| Act
    Case -->|INTERPRETS| Section
    Case -->|CITES| Case
    Case -->|OVERRULES| Case
    Case -->|FOLLOWS| Case
    Case -->|DISTINGUISHES| Case
    Case -->|DECIDED_BY| Court
    Judge -->|AUTHORED| Case
    Judge -->|BENCH_MEMBER_OF| Case
    Party -->|PARTY_TO| Case
    Clause -->|PART_OF| Contract
    Clause -->|REFERENCES| Section
```

---

## 3. Node Specifications

| Node Label | Key Identifier (`id`) | Primary Attributes | Description |
| :--- | :--- | :--- | :--- |
| **`Act`** | `act_id` (e.g. `act_contract_1872`) | `title`, `short_name`, `year`, `jurisdiction`, `section_count` | Primary statute or ordinance enacted by Parliament |
| **`Section`** | `sec_id` (e.g. `sec_contract_1872_23`) | `number`, `heading`, `text_preview`, `act_title` | Statutory section, clause, or constitutional article |
| **`Case`** | `case_id` (e.g. `judg_ka_175`) | `title`, `citation`, `court_name`, `year`, `date`, `holding`, `status`, `pagerank_score` | High Court or Supreme Court reported judgment |
| **`Court`** | `court_id` (e.g. `court_sc_pakistan`) | `name`, `city`, `level` (`Supreme Court`, `High Court`) | Judicial forum deciding the matter |
| **`Judge`** | `judge_id` (e.g. `judge_qazi_faez_isa`) | `name`, `designation`, `appointment_year`, `retirement_year` | Justice authoring or sitting on the bench |
| **`Party`** | `party_id` (e.g. `party_state_pakistan`) | `name`, `type` (`Individual`, `Corporate`, `State`) | Litigant in the case (petitioner, respondent, appellant) |
| **`Contract`** | `contract_id` (e.g. `cont_cuad_012`) | `title`, `matter_id`, `governing_law`, `parties`, `clause_count` | Commercial agreement or contract |
| **`Clause`** | `clause_id` (e.g. `cl_cont_012_sec4`) | `number`, `title`, `text_preview` | Distinct section or clause in a contract |

---

## 4. Relationship Specifications

| Relationship | Source Node | Target Node | Cardinality | Properties | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`INTERPRETS`** | `Case` | `Section` | N : M | `substantive_holding`, `interpretation_type` | Case delivers an authoritative judicial construction of a statute section |
| **`CITES`** | `Case` | `Case` | N : M | `page_ref`, `context` | Case refers to an earlier judicial precedent |
| **`OVERRULES`** | `Case` | `Case` | N : M | `overruled_date`, `reason`, `bench_size` | Larger bench explicitly overrules earlier case law (bad law flag) |
| **`FOLLOWS`** | `Case` | `Case` | N : M | `aspect` | Case adheres to and adopts principle from earlier precedent |
| **`DISTINGUISHES`** | `Case` | `Case` | N : M | `distinguishing_ground` | Case distinguishes facts from an earlier precedent |
| **`DECIDED_BY`** | `Case` | `Court` | N : 1 | `registry` | Court where judgment was pronounced |
| **`AUTHORED`** | `Judge` | `Case` | 1 : N | `opinion_type` (`Majority`, `Dissent`, `Concurrence`) | Authoring Justice of the judgment |
| **`BENCH_MEMBER_OF`** | `Judge` | `Case` | N : M | `bench_size` | Member of the hearing division/larger bench |
| **`PARTY_TO`** | `Party` | `Case` | N : M | `role` (`Appellant`, `Respondent`, `Petitioner`) | Party to the litigation |
| **`PART_OF`** | `Section` | `Act` | N : 1 | `chapter`, `part` | Section belonging to a specific Act |
| **`PART_OF`** | `Clause` | `Contract`| N : 1 | `clause_number` | Clause belonging to a specific Contract |
| **`REFERENCES`** | `Clause` | `Section` | N : M | `relevance` | Contractual clause explicitly referencing statutory section |

---

## 5. Cypher Constraints & Schema DDL

```cypher
// Uniqueness Constraints
CREATE CONSTRAINT act_id_unique IF NOT EXISTS FOR (a:Act) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT sec_id_unique IF NOT EXISTS FOR (s:Section) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT case_id_unique IF NOT EXISTS FOR (c:Case) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT court_id_unique IF NOT EXISTS FOR (co:Court) REQUIRE co.id IS UNIQUE;
CREATE CONSTRAINT judge_id_unique IF NOT EXISTS FOR (j:Judge) REQUIRE j.id IS UNIQUE;
CREATE CONSTRAINT party_id_unique IF NOT EXISTS FOR (p:Party) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT contract_id_unique IF NOT EXISTS FOR (cn:Contract) REQUIRE cn.id IS UNIQUE;
CREATE CONSTRAINT clause_id_unique IF NOT EXISTS FOR (cl:Clause) REQUIRE cl.id IS UNIQUE;

// Search Indexes
CREATE INDEX case_citation_idx IF NOT EXISTS FOR (c:Case) ON (c.citation);
CREATE INDEX case_year_idx IF NOT EXISTS FOR (c:Case) ON (c.year);
CREATE INDEX sec_number_idx IF NOT EXISTS FOR (s:Section) ON (s.number);
CREATE INDEX judge_name_idx IF NOT EXISTS FOR (j:Judge) ON (j.name);
```

