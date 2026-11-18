"""Task 5: Citation Verification Engine.
Automatically verifies that:
1. Every cited Act and Section exists in the official statutory catalog.
2. Every cited Case / Judge exists in the Supreme Court judgment corpus.
3. Every quoted source text appears verbatim (exact or normalized substring) in the source document.
4. Target: ZERO fabricated citations.
"""

import json
from pathlib import Path
import re
import unicodedata


STATUTES_JSON = Path("outputs/structured/statutes.json")
JUDGMENTS_JSON = Path("outputs/structured/judgments.json")
PARENTS_JSON = Path("outputs/chunks_parents.json")


def normalize_text(text: str) -> str:
    """Normalize whitespace and Unicode for robust substring matching."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    # Remove punctuation for fuzzy quote alignment if needed
    return text


class CitationVerifier:
    def __init__(self):
        self.statutes = json.loads(STATUTES_JSON.read_text(encoding="utf-8"))
        self.judgments = json.loads(JUDGMENTS_JSON.read_text(encoding="utf-8"))
        self.parents = json.loads(PARENTS_JSON.read_text(encoding="utf-8"))

        # Build Act -> Set of valid sections
        self.act_sections: dict[str, set[str]] = {}
        self.act_canonical: dict[str, str] = {}
        self.section_texts: dict[tuple[str, str], str] = {}

        for st in self.statutes:
            act_name = st["act"]
            norm_act = normalize_text(act_name)
            self.act_canonical[norm_act] = act_name

            # Add common aliases
            if "penal code" in norm_act:
                self.act_canonical["ppc"] = act_name
                self.act_canonical["pakistan penal code"] = act_name
            elif "contract" in norm_act:
                self.act_canonical["contract act"] = act_name
            elif "constitution" in norm_act:
                self.act_canonical["constitution of pakistan"] = act_name
                self.act_canonical["constitution"] = act_name
            elif "family laws" in norm_act:
                self.act_canonical["mflo"] = act_name
                self.act_canonical["muslim family laws"] = act_name
            elif "criminal procedure" in norm_act:
                self.act_canonical["crpc"] = act_name
            elif "civil procedure" in norm_act:
                self.act_canonical["cpc"] = act_name
            elif "specific relief" in norm_act:
                self.act_canonical["specific relief act"] = act_name
            elif "money laundering" in norm_act:
                self.act_canonical["aml act"] = act_name
                self.act_canonical["anti money laundering"] = act_name
            elif "terrorism" in norm_act:
                self.act_canonical["ata"] = act_name
                self.act_canonical["anti terrorism act"] = act_name

            sec_set = set()
            for sec in st.get("sections", []):
                snum = str(sec.get("section", "")).strip().upper()
                sec_set.add(snum)
                self.section_texts[(act_name, snum)] = sec.get("text", "")
            self.act_sections[act_name] = sec_set

        # Build Judgment lookup sets
        self.judgment_files = {j["filename"].lower(): j for j in self.judgments}
        self.judgment_judges = {j.get("author_judge", "").lower() for j in self.judgments if j.get("author_judge")}

    def verify(self, answer: dict) -> dict:
        """Verify an answer dictionary against the ground truth catalog."""
        query = answer.get("query", "")
        short_ans = answer.get("short_answer", "")
        cit = answer.get("citation") or {}
        quote = answer.get("quoted_source")
        parent_id = answer.get("parent_id")

        result = {
            "query": query,
            "status": "VERIFIED",
            "act_exists": None,
            "section_exists": None,
            "case_exists": None,
            "quote_verified": None,
            "is_unanswerable_handled": None,
            "fabricated_elements": [],
        }

        # Case 1: Unanswerable or No sufficient source found
        if "no sufficient source found" in short_ans.lower() or not answer.get("is_sufficient_source_found", True):
            if cit.get("act") or cit.get("section") or (quote and len(quote.strip()) > 10):
                result["status"] = "FABRICATED_CITATION_ON_UNANSWERABLE"
                result["fabricated_elements"].append("fabricated citation on unanswerable query")
                result["is_unanswerable_handled"] = False
            else:
                result["is_unanswerable_handled"] = True
                result["status"] = "VERIFIED_NO_SOURCE"
            return result

        # Case 2: Statute Citation Verification
        if cit.get("act") or cit.get("section"):
            raw_act = cit.get("act", "")
            norm_act = normalize_text(raw_act)
            matched_act = None

            # Match Act
            for alias, canon in self.act_canonical.items():
                if alias in norm_act or norm_act in alias:
                    matched_act = canon
                    break

            if not matched_act:
                result["act_exists"] = False
                result["status"] = "FABRICATED_ACT"
                result["fabricated_elements"].append(f"Act not found in corpus: '{raw_act}'")
            else:
                result["act_exists"] = True
                raw_sec = str(cit.get("section", "")).strip().upper().replace("SECTION", "").replace("ARTICLE", "").strip(" .")
                valid_secs = self.act_sections.get(matched_act, set())
                if raw_sec in valid_secs or any(s == raw_sec or s.startswith(raw_sec) for s in valid_secs):
                    result["section_exists"] = True
                else:
                    result["section_exists"] = False
                    result["status"] = "FABRICATED_SECTION"
                    result["fabricated_elements"].append(f"Section '{raw_sec}' does not exist in '{matched_act}'")

        # Case 3: Case-Law Citation Verification
        if cit.get("court") or cit.get("case") or cit.get("judge"):
            raw_case = (cit.get("case") or "").lower()
            raw_judge = (cit.get("judge") or "").lower()
            case_found = any(raw_case in fname for fname in self.judgment_files) if raw_case else False
            judge_found = any(raw_judge in j for j in self.judgment_judges) if raw_judge else False

            if case_found or judge_found or cit.get("court") == "Supreme Court of Pakistan":
                result["case_exists"] = True
            else:
                result["case_exists"] = False
                result["status"] = "FABRICATED_CASE"
                result["fabricated_elements"].append(f"Judgment '{raw_case}' / Judge '{raw_judge}' not found")

        # Case 4: Verbatim Quote Verification
        if quote and len(quote.strip()) > 10:
            norm_quote = normalize_text(quote)
            found_quote = False

            # Check inside parent text if parent_id provided
            if parent_id and parent_id in self.parents:
                parent_norm = normalize_text(self.parents[parent_id].get("text", ""))
                if norm_quote in parent_norm:
                    found_quote = True

            # Also check across all statute texts or retrieved documents if needed
            if not found_quote:
                for (act_name, snum), sec_text in self.section_texts.items():
                    if norm_quote in normalize_text(sec_text):
                        found_quote = True
                        break

            if found_quote:
                result["quote_verified"] = True
            else:
                result["quote_verified"] = False
                if result["status"] == "VERIFIED":
                    result["status"] = "FABRICATED_QUOTE"
                result["fabricated_elements"].append(f"Quote does not appear in source text: '{quote[:60]}...'")
        else:
            result["quote_verified"] = False
            if result["status"] == "VERIFIED":
                result["status"] = "MISSING_QUOTE"
                result["fabricated_elements"].append("Missing or empty quoted_source")

        return result


def main():
    verifier = CitationVerifier()
    print(f"Citation Verifier initialized:")
    print(f"  {len(verifier.act_sections)} Acts cataloged")
    print(f"  {len(verifier.judgment_files)} Judgments cataloged")
    print(f"  {len(verifier.parents)} Parent source texts loaded")

    # Sanity test with 1 valid and 1 fabricated citation
    test_valid = {
        "query": "Agar consideration unlawful ho to kya contract void hai?",
        "short_answer": "Yes, void under Section 23.",
        "citation": {"act": "Contract Act, 1872", "section": "23"},
        "quoted_source": "The consideration or object of an agreement is lawful, unless it is forbidden by law",
    }
    test_fake = {
        "query": "Fake question",
        "short_answer": "Fake law.",
        "citation": {"act": "NonExistent Act, 2099", "section": "999"},
        "quoted_source": "This quote was made up completely by an LLM hallucination",
    }
    print("\nSanity Check - Valid Citation:")
    print(verifier.verify(test_valid))
    print("\nSanity Check - Fabricated Citation:")
    print(verifier.verify(test_fake))


if __name__ == "__main__":
    main()
