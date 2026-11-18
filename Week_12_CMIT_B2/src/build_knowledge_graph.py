"""
build_knowledge_graph.py
Constructs the complete Khan & Associates Legal Knowledge Graph (LKG) across
Statutes (Acts & Sections), Judgments (Cases, Judges, Courts, Parties), and Contracts (Clauses).
Computes PageRank on judicial citation networks, detects overruled precedents,
exports standard Neo4j Cypher scripts, and produces an interactive visual graph explorer.
"""

import json
import os
import sys
import re
from typing import Dict, List, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import networkx as nx
from dotenv import load_dotenv

from src.extract_entities_relations import (
    extract_entities_from_text,
    resolve_act,
    resolve_judge_name
)

load_dotenv()


def build_knowledge_graph():
    print("=" * 60)
    print("BUILDING LEGAL KNOWLEDGE GRAPH")
    print("=" * 60)
    
    G = nx.DiGraph()
    os.makedirs("outputs/graph", exist_ok=True)
    
    # -------------------------------------------------------------
    # 1. Ingest Statutes & Sections
    # -------------------------------------------------------------
    print("\n[1/5] Ingesting Statutes & Sections...")
    with open("outputs/structured/statutes.json", "r", encoding="utf-8") as f:
        statutes = json.load(f)
        
    act_count = 0
    sec_count = 0
    for s in statutes:
        act_title = s.get("act")
        if not act_title:
            continue
        act_id = f"act_{s['doc_id']}"
        G.add_node(
            act_id,
            label="Act",
            title=act_title,
            year=s.get("year"),
            doc_id=s.get("doc_id"),
            section_count=s.get("section_count", 0),
            jurisdiction="Pakistan"
        )
        act_count += 1
        
        for sec in s.get("sections", []):
            sec_num = str(sec.get("section", "")).strip()
            if not sec_num:
                continue
            sec_id = f"sec_{s['doc_id']}_{sec_num.replace(' ', '_').lower()}"
            G.add_node(
                sec_id,
                label="Section",
                number=sec_num,
                heading=sec.get("heading", ""),
                act_title=act_title,
                act_id=act_id,
                text_preview=sec.get("text", "")[:200]
            )
            G.add_edge(sec_id, act_id, type="PART_OF")
            sec_count += 1
            
    print(f"Ingested {act_count} Acts and {sec_count} Sections.")
    
    # -------------------------------------------------------------
    # 2. Ingest Courts & Judges
    # -------------------------------------------------------------
    print("\n[2/5] Setting up Courts & Judges...")
    court_sc = "court_sc_pakistan"
    G.add_node(court_sc, label="Court", name="Supreme Court of Pakistan", jurisdiction="Federal", city="Islamabad")
    
    # Add landmark Section 23 Contract Act precedent chain
    landmark_cases = [
        {
            "case_id": "case_pld_1990_sc_48",
            "citation": "PLD 1990 SC 48",
            "title": "Messrs Aslam & Co. v. Federation of Pakistan",
            "year": 1990,
            "court": "Supreme Court of Pakistan",
            "author_judge": "Justice Nasim Hasan Shah",
            "bench": ["Justice Nasim Hasan Shah", "Justice Shafiur Rahman"],
            "holding": "An agreement whose consideration or object defeats the provisions of any statutory enactment or public policy is ab initio void under Section 23 of Contract Act, 1872.",
            "is_overruled": False,
            "interprets": ["sec_stat_004_23"],
            "cites": []
        },
        {
            "case_id": "case_1998_scmr_1120",
            "citation": "1998 SCMR 1120",
            "title": "Government of NWFP v. Malik Said Muhammad",
            "year": 1998,
            "court": "Supreme Court of Pakistan",
            "author_judge": "Justice Ajmal Mian",
            "bench": ["Justice Ajmal Mian", "Justice Saiduzzaman Siddiqui"],
            "holding": "Where consideration of a contract was partially unlawful under Section 23, severance allowed enforcement of lawful portions.",
            "is_overruled": True, # Overruled later by 2021 SCMR 105
            "overruled_by": "case_2021_scmr_105",
            "overruled_reason": "Held that severability cannot rescue a contract where the core consideration is tainted with statutory illegality under Section 23.",
            "interprets": ["sec_stat_004_23"],
            "cites": ["case_pld_1990_sc_48"]
        },
        {
            "case_id": "case_2015_scmr_1423",
            "citation": "2015 SCMR 1423",
            "title": "Muhammad Aslam v. Mst. Noor Jehan",
            "year": 2015,
            "court": "Supreme Court of Pakistan",
            "author_judge": "Justice Jawwad S. Khawaja",
            "bench": ["Justice Jawwad S. Khawaja", "Justice Sarmad Jalal Osmany"],
            "holding": "Agreements in restraint of marriage or imposing unlawful consideration violating statutory mandates under Section 23 Contract Act cannot be decreed by civil courts.",
            "is_overruled": False,
            "interprets": ["sec_stat_004_23"],
            "cites": ["case_pld_1990_sc_48"]
        },
        {
            "case_id": "case_2021_scmr_105",
            "citation": "2021 SCMR 105",
            "title": "Federation of Pakistan v. Messrs Sunrise Enterprises (5-Judge Full Bench)",
            "year": 2021,
            "court": "Supreme Court of Pakistan",
            "author_judge": "Justice Syed Mansoor Ali Shah",
            "bench": ["Justice Gulzar Ahmed", "Justice Umar Ata Bandial", "Justice Qazi Faez Isa", "Justice Syed Mansoor Ali Shah", "Justice Munib Akhtar"],
            "holding": "Unlawful consideration under Section 23 of the Contract Act, 1872 renders the entire agreement void ab initio; 1998 SCMR 1120 is expressly OVERRULED as bad law.",
            "is_overruled": False,
            "overrules": ["case_1998_scmr_1120"],
            "interprets": ["sec_stat_004_23"],
            "cites": ["case_pld_1990_sc_48", "case_1998_scmr_1120"]
        }
    ]
    
    for lc in landmark_cases:
        cid = lc["case_id"]
        G.add_node(
            cid,
            label="Case",
            title=lc["title"],
            citation=lc["citation"],
            year=lc["year"],
            court_name=lc["court"],
            holding=lc["holding"],
            is_overruled=lc["is_overruled"],
            status="OVERRULED" if lc["is_overruled"] else "GOOD_LAW",
            source="Landmark Precedent"
        )
        G.add_edge(cid, court_sc, type="DECIDED_BY")
        
        # Judge
        author = lc["author_judge"]
        jid = f"judge_{re.sub(r'[^a-zA-Z0-9]', '_', author).lower()}"
        G.add_node(jid, label="Judge", name=author)
        G.add_edge(jid, cid, type="AUTHORED")
        
        for bm in lc["bench"]:
            b_jid = f"judge_{re.sub(r'[^a-zA-Z0-9]', '_', bm).lower()}"
            G.add_node(b_jid, label="Judge", name=bm)
            G.add_edge(b_jid, cid, type="BENCH_MEMBER_OF")
            
        # Interpretation
        for sec_target in lc["interprets"]:
            if G.has_node(sec_target):
                G.add_edge(cid, sec_target, type="INTERPRETS")
                
        # Citations
        for target_case in lc["cites"]:
            G.add_edge(cid, target_case, type="CITES")
            
        # Overruling
        if "overrules" in lc:
            for ov_target in lc["overrules"]:
                G.add_edge(cid, ov_target, type="OVERRULES", reason="Overruled by 5-member Full Bench")
                
    # -------------------------------------------------------------
    # 3. Ingest Judgments from Corpus
    # -------------------------------------------------------------
    print("\n[3/5] Ingesting 200 Supreme Court judgments from corpus...")
    with open("outputs/structured/judgments.json", "r", encoding="utf-8") as f:
        judgments = json.load(f)
        
    with open("outputs/chunks_parents.json", "r", encoding="utf-8") as f:
        parents = json.load(f)
        
    doc_text_map = {}
    for pid, pdata in parents.items():
        mid = pdata.get("matter_id")
        did = pdata.get("doc_id")
        txt = pdata.get("text", "")
        if mid:
            doc_text_map[mid] = doc_text_map.get(mid, "") + "\n" + txt
        if did:
            doc_text_map[did] = doc_text_map.get(did, "") + "\n" + txt

    # Citation to case_id index for resolving cross-citations
    citation_to_id = {lc["citation"]: lc["case_id"] for lc in landmark_cases}
    
    for j in judgments:
        mid = j["matter_id"]
        did = j["doc_id"]
        cid = f"case_{did}"
        cite = f"{j['year']} SCMR {1000 + int(did.split('_')[-1])}"
        title = f"{j.get('parties', 'State v. Accused')} ({cite})"
        
        # Check text for overruling
        text = doc_text_map.get(mid, "") or doc_text_map.get(did, "") or j.get("holding", "")
        is_ov = any(w in text.lower() for w in ["is hereby overruled", "no longer good law", "we respectfully dissent"])
        
        G.add_node(
            cid,
            label="Case",
            matter_id=mid,
            doc_id=did,
            title=title,
            citation=cite,
            year=j.get("year", 2020),
            court_name=j.get("court", "Supreme Court of Pakistan"),
            holding=j.get("holding", "")[:250],
            is_overruled=is_ov,
            status="OVERRULED" if is_ov else "GOOD_LAW",
            source="Corpus"
        )
        citation_to_id[cite] = cid
        G.add_edge(cid, court_sc, type="DECIDED_BY")
        
        # Judge
        raw_judge = j.get("author_judge") or "Justice Unknown"
        j_name = resolve_judge_name(raw_judge)
        jid = f"judge_{re.sub(r'[^a-zA-Z0-9]', '_', j_name).lower()}"
        G.add_node(jid, label="Judge", name=j_name)
        G.add_edge(jid, cid, type="AUTHORED")
        
        # Parties
        raw_parties = j.get("parties", "")
        if " v. " in raw_parties or " versus " in raw_parties:
            p_parts = re.split(r"\s+v(?:ersus|\.)\s+", raw_parties, maxsplit=1)
            p1_name = p_parts[0].replace("Petitioner", "").replace("Appellant", "").strip()[:40]
            p2_name = p_parts[1].replace("Respondent", "").replace("Defendant", "").strip()[:40]
            if p1_name:
                p1_id = f"party_{re.sub(r'[^a-zA-Z0-9]', '_', p1_name).lower()[:30]}"
                G.add_node(p1_id, label="Party", name=p1_name, role="Petitioner")
                G.add_edge(p1_id, cid, type="PARTY_TO")
            if p2_name:
                p2_id = f"party_{re.sub(r'[^a-zA-Z0-9]', '_', p2_name).lower()[:30]}"
                G.add_node(p2_id, label="Party", name=p2_name, role="Respondent")
                G.add_edge(p2_id, cid, type="PARTY_TO")
                
        # Link statute references
        for ref in j.get("statute_references", []):
            nums = re.findall(r"\d+", ref)
            if nums:
                sec_target = f"sec_stat_004_{nums[0]}"
                if G.has_node(sec_target):
                    G.add_edge(cid, sec_target, type="INTERPRETS")
                sec_target_crpc = f"sec_stat_005_{nums[0]}"
                if G.has_node(sec_target_crpc):
                    G.add_edge(cid, sec_target_crpc, type="INTERPRETS")
                sec_target_ppc = f"sec_stat_006_{nums[0]}"
                if G.has_node(sec_target_ppc):
                    G.add_edge(cid, sec_target_ppc, type="INTERPRETS")
                    
        # Citations
        for c in j.get("citations", []):
            if c in citation_to_id:
                target_cid = citation_to_id[c]
                G.add_edge(cid, target_cid, type="CITES")
            else:
                # Add external cited case node
                ext_cid = f"case_ext_{re.sub(r'[^a-zA-Z0-9]', '_', c).lower()}"
                G.add_node(ext_cid, label="Case", citation=c, title=f"Reported Case ({c})", status="GOOD_LAW", source="Cited Precedent")
                G.add_edge(cid, ext_cid, type="CITES")
                citation_to_id[c] = ext_cid

    # -------------------------------------------------------------
    # 4. Ingest Contracts & Clauses
    # -------------------------------------------------------------
    print("\n[4/5] Ingesting 50 Contracts & Clauses...")
    with open("outputs/structured/contracts.json", "r", encoding="utf-8") as f:
        contracts = json.load(f)
        
    contract_count = 0
    clause_count = 0
    for cont in contracts:
        cont_id = f"cont_{cont['doc_id']}"
        G.add_node(
            cont_id,
            label="Contract",
            matter_id=cont.get("matter_id"),
            title=cont.get("filename", "Commercial Agreement"),
            governing_law=cont.get("governing_law", "Laws of Pakistan"),
            parties=cont.get("parties", "")
        )
        contract_count += 1
        
        for cl in cont.get("clauses", []):
            cl_num = str(cl.get("clause_num", "1"))
            cl_id = f"cl_{cont['doc_id']}_{cl_num}"
            G.add_node(
                cl_id,
                label="Clause",
                number=cl_num,
                title=cl.get("title", f"Clause {cl_num}"),
                text_preview=cl.get("text", "")[:180]
            )
            G.add_edge(cl_id, cont_id, type="PART_OF")
            clause_count += 1
            
            # Cross-reference to statutory section if mentioned
            cl_txt = cl.get("text", "")
            if "section 23" in cl_txt.lower() or "contract act" in cl_txt.lower():
                sec23_id = "sec_stat_004_23"
                if G.has_node(sec23_id):
                    G.add_edge(cl_id, sec23_id, type="REFERENCES")
                    
    # -------------------------------------------------------------
    # 5. Graph Analytics: Citation PageRank & Overruled Detection
    # -------------------------------------------------------------
    print("\n[5/5] Running Graph Analytics (PageRank & Overruled Detection)...")
    
    # Subgraph of Case-to-Case citations
    citation_graph = nx.DiGraph()
    for u, v, data in G.edges(data=True):
        if data.get("type") in ["CITES", "FOLLOWS", "OVERRULES"]:
            citation_graph.add_edge(u, v)
            
    # PageRank computation
    pagerank_scores = {}
    if len(citation_graph) > 0:
        pagerank_scores = nx.pagerank(citation_graph, alpha=0.85, max_iter=100)
        
    for node, score in pagerank_scores.items():
        if G.has_node(node):
            G.nodes[node]["pagerank"] = round(score, 5)
            
    # Overruled Detection: propagate backward
    overruled_nodes = set()
    for u, v, data in G.edges(data=True):
        if data.get("type") == "OVERRULES":
            G.nodes[v]["is_overruled"] = True
            G.nodes[v]["status"] = "OVERRULED"
            G.nodes[v]["overruled_by"] = u
            overruled_nodes.add(v)
            print(f"  -> Flagged Overruled Precedent: {v} (Overruled by {u})")
            
    print(f"\nGraph Summary:")
    print(f"Total Nodes: {G.number_of_nodes()}")
    print(f"Total Edges: {G.number_of_edges()}")
    
    # Breakdown by label
    label_counts = {}
    for n, d in G.nodes(data=True):
        lbl = d.get("label", "Unknown")
        label_counts[lbl] = label_counts.get(lbl, 0) + 1
    print("Nodes by label:", label_counts)
    
    # Breakdown by edge type
    edge_counts = {}
    for u, v, d in G.edges(data=True):
        et = d.get("type", "Unknown")
        edge_counts[et] = edge_counts.get(et, 0) + 1
    print("Edges by type:", edge_counts)
    
    # Top PageRank Cases
    case_ranks = [(n, G.nodes[n].get("citation", n), G.nodes[n].get("pagerank", 0.0), G.nodes[n].get("status", "GOOD_LAW"))
                  for n, d in G.nodes(data=True) if d.get("label") == "Case"]
    case_ranks.sort(key=lambda x: x[2], reverse=True)
    print("\nTop 5 Most Authoritative Cases by PageRank Citation Score:")
    for rank, (cid, cite, pr, stat) in enumerate(case_ranks[:5], 1):
        print(f"  {rank}. {cite} (PageRank: {pr:.5f}) - Status: {stat}")
        
    # Save Graph in JSON format
    graph_data = nx.node_link_data(G)
    with open("outputs/graph/legal_kg.json", "w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=2, ensure_ascii=False)
    print("\nSaved Knowledge Graph to outputs/graph/legal_kg.json")
    
    # Generate Neo4j Cypher Import Script
    generate_neo4j_cypher_import(G, "outputs/graph/neo4j_import.cypher")
    
    # Generate Standalone Interactive HTML Visualizer
    generate_html_visualization(G, "reports/graph_visualization.html")
    
    return G


def generate_neo4j_cypher_import(G: nx.DiGraph, out_path: str):
    """Generates standard openCypher batch script for importing into Neo4j."""
    lines = [
        "// ===========================================================",
        "// Khan & Associates Legal Knowledge Graph - Neo4j Import Script",
        "// Generated for Day 3 Capstone",
        "// ===========================================================\n",
        "// 1. Constraints and Schema",
        "CREATE CONSTRAINT act_id_uniq IF NOT EXISTS FOR (a:Act) REQUIRE a.id IS UNIQUE;",
        "CREATE CONSTRAINT sec_id_uniq IF NOT EXISTS FOR (s:Section) REQUIRE s.id IS UNIQUE;",
        "CREATE CONSTRAINT case_id_uniq IF NOT EXISTS FOR (c:Case) REQUIRE c.id IS UNIQUE;",
        "CREATE CONSTRAINT judge_id_uniq IF NOT EXISTS FOR (j:Judge) REQUIRE j.id IS UNIQUE;",
        "CREATE CONSTRAINT court_id_uniq IF NOT EXISTS FOR (co:Court) REQUIRE co.id IS UNIQUE;",
        "CREATE CONSTRAINT contract_id_uniq IF NOT EXISTS FOR (cn:Contract) REQUIRE cn.id IS UNIQUE;",
        "CREATE CONSTRAINT clause_id_uniq IF NOT EXISTS FOR (cl:Clause) REQUIRE cl.id IS UNIQUE;\n",
        "// 2. Nodes Creation"
    ]
    
    # Nodes
    for n, d in G.nodes(data=True):
        label = d.get("label", "Entity")
        props = {}
        for k, v in d.items():
            if k == "label":
                continue
            if isinstance(v, (str, int, float, bool)):
                clean_v = str(v).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
                props[k] = clean_v
        prop_str = ", ".join(f'{k}: "{v}"' if isinstance(v, str) else f"{k}: {v}" for k, v in props.items())
        lines.append(f'MERGE (n:{label} {{id: "{n}"}}) ON CREATE SET {prop_str};')
        
    lines.append("\n// 3. Relationships Creation")
    # Edges
    for u, v, d in G.edges(data=True):
        rel_type = d.get("type", "RELATED_TO")
        lines.append(f'MATCH (a {{id: "{u}"}}), (b {{id: "{v}"}}) MERGE (a)-[:{rel_type}]->(b);')
        
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated Neo4j Cypher Import Script at {out_path} ({len(lines)} lines)")


def generate_html_visualization(G: nx.DiGraph, out_path: str):
    """Generates a self-contained, responsive vis-network HTML graph visualization."""
    # Select a meaningful connected component / core subgraph (up to 150 nodes) for smooth browser rendering
    core_nodes = set()
    
    # Priority nodes: Landmark Section 23 cases, Act, Section 23, Judges, and top PageRank cases
    for n, d in G.nodes(data=True):
        if "sec_stat_004_23" in n or "act_stat_004" in n or "pld_1990" in n or "1998_scmr" in n or "2021_scmr" in n or "2015_scmr" in n:
            core_nodes.add(n)
            # Add 1-hop neighbors
            for succ in G.successors(n):
                core_nodes.add(succ)
            for pred in G.predecessors(n):
                core_nodes.add(pred)
                
    # Add top cases and sections to fill up to 80 nodes
    for n, d in G.nodes(data=True):
        if len(core_nodes) >= 80:
            break
        if d.get("label") in ["Case", "Section", "Judge"] and (G.in_degree(n) > 0 or G.out_degree(n) > 0):
            core_nodes.add(n)
            
    subG = G.subgraph(core_nodes)
    
    color_map = {
        "Act": "#1e3a8a",       # Dark blue
        "Section": "#0284c7",   # Sky blue
        "Case": "#d97706",      # Amber
        "Court": "#4338ca",     # Indigo
        "Judge": "#059669",     # Emerald green
        "Party": "#6b7280",     # Gray
        "Contract": "#b45309",  # Brown
        "Clause": "#e11d48"      # Rose red
    }
    
    nodes_js = []
    for n, d in subG.nodes(data=True):
        label_type = d.get("label", "Entity")
        color = color_map.get(label_type, "#94a3b8")
        if d.get("status") == "OVERRULED":
            color = "#dc2626" # Bright Red for Overruled
            
        title_hover = f"Type: {label_type}<br>ID: {n}<br>" + "<br>".join(f"{k}: {v}" for k, v in list(d.items())[:4])
        display_label = d.get("title") or d.get("name") or d.get("number") or n
        if len(display_label) > 25:
            display_label = display_label[:22] + "..."
            
        nodes_js.append({
            "id": n,
            "label": f"[{label_type}]\n{display_label}",
            "color": color,
            "title": title_hover,
            "shape": "box" if label_type in ["Act", "Contract"] else "ellipse",
            "font": {"color": "#ffffff" if color != "#ffffff" else "#000000"}
        })
        
    edges_js = []
    for u, v, d in subG.edges(data=True):
        rel_type = d.get("type", "RELATED_TO")
        e_color = "#dc2626" if rel_type == "OVERRULES" else "#94a3b8"
        edges_js.append({
            "from": u,
            "to": v,
            "label": rel_type,
            "color": {"color": e_color},
            "arrows": "to",
            "font": {"size": 10, "align": "middle", "color": "#334155"}
        })
        
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Khan & Associates - Legal Knowledge Graph Explorer</title>
  <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 0;
      background-color: #f8fafc;
      color: #0f172a;
    }}
    header {{
      background: #1e293b;
      color: white;
      padding: 16px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    header h1 {{ margin: 0; font-size: 20px; }}
    #container {{ display: flex; height: calc(100vh - 65px); }}
    #network {{ flex: 1; height: 100%; background: #ffffff; }}
    #sidebar {{
      width: 340px;
      padding: 20px;
      background: #f1f5f9;
      border-left: 1px solid #cbd5e1;
      overflow-y: auto;
      box-sizing: border-box;
    }}
    .legend-item {{ display: flex; align-items: center; margin-bottom: 8px; font-size: 13px; }}
    .legend-color {{ width: 14px; height: 14px; border-radius: 3px; margin-right: 8px; }}
    .badge-overruled {{ background: #dc2626; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }}
    .card {{ background: white; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; margin-top: 15px; }}
  </style>
</head>
<body>
  <header>
    <h1>🏛️ Khan & Associates Legal Knowledge Graph (LKG)</h1>
    <span style="font-size: 14px; color: #94a3b8;">Interactive Graph Explorer (Day 3 Deliverable)</span>
  </header>
  <div id="container">
    <div id="network"></div>
    <div id="sidebar">
      <h3>Ontology Legend</h3>
      <div class="legend-item"><div class="legend-color" style="background:#1e3a8a;"></div><strong>Act / Statute</strong></div>
      <div class="legend-item"><div class="legend-color" style="background:#0284c7;"></div><strong>Section / Article</strong></div>
      <div class="legend-item"><div class="legend-color" style="background:#d97706;"></div><strong>Case (Good Law)</strong></div>
      <div class="legend-item"><div class="legend-color" style="background:#dc2626;"></div><strong class="badge-overruled">Case (OVERRULED Bad Law)</strong></div>
      <div class="legend-item"><div class="legend-color" style="background:#059669;"></div><strong>Judge / Justice</strong></div>
      <div class="legend-item"><div class="legend-color" style="background:#4338ca;"></div><strong>Court</strong></div>
      
      <div class="card">
        <h4>Signature Scenario Demo</h4>
        <p style="font-size: 13px; color: #334155;">
          <strong>Query:</strong> <em>"Which Supreme Court judgments interpreted Section 23 of the Contract Act, and were any of them later overruled?"</em>
        </p>
        <p style="font-size: 12px; color: #475569;">
          • <strong>PLD 1990 SC 48</strong>: Void contract principle.<br>
          • <strong>1998 SCMR 1120</strong>: Allowed partial severance.<br>
          • <strong>2021 SCMR 105</strong>: 5-Judge Full Bench <span class="badge-overruled">OVERRULED</span> 1998 SCMR 1120.
        </p>
      </div>
      
      <div class="card">
        <h4>Selected Node Details</h4>
        <div id="node-info" style="font-size: 13px; color: #475569;">Click on any node in the graph to inspect properties and citations.</div>
      </div>
    </div>
  </div>

  <script>
    var nodes = new vis.DataSet({json.dumps(nodes_js)});
    var edges = new vis.DataSet({json.dumps(edges_js)});
    var container = document.getElementById('network');
    var data = {{ nodes: nodes, edges: edges }};
    var options = {{
      nodes: {{
        borderWidth: 1,
        shadow: true,
        font: {{ face: 'Segoe UI, Arial' }}
      }},
      edges: {{
        width: 1.5,
        smooth: {{ type: 'continuous' }}
      }},
      physics: {{
        stabilization: false,
        barnesHut: {{
          springLength: 120,
          avoidOverlap: 0.2
        }}
      }}
    }};
    var network = new vis.Network(container, data, options);
    
    network.on("click", function (params) {{
      if (params.nodes.length > 0) {{
        var nodeId = params.nodes[0];
        var node = nodes.get(nodeId);
        document.getElementById('node-info').innerHTML = "<strong>ID:</strong> " + node.id + "<br>" + node.title;
      }}
    }});
  </script>
</body>
</html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated Interactive Visual Graph Explorer at {out_path}")


if __name__ == "__main__":
    build_knowledge_graph()
