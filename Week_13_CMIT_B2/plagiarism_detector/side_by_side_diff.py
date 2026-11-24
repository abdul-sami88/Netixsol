"""
Side-by-Side Teacher Code Comparison & Academic Integrity Report Generator
Generates clean, readable side-by-side code inspection views for instructor review.
Strictly adheres to Ilm Academy Policy: 'FLAG ONLY — NEVER AUTO-PUNISH'.
"""

from typing import Dict, Any

class SideBySideDiffViewer:
    """
    Renders side-by-side comparison cards for teachers to inspect suspected plagiarism.
    """

    POLICY_DISCLAIMER = (
        "> [!IMPORTANT]\n"
        "> **ACADEMIC INTEGRITY DIRECTIVE: FLAG ONLY — NEVER AUTO-PUNISH.**\n"
        "> This automated similarity score indicates structural and semantic overlap for human inspection.\n"
        "> No disciplinary penalty or grade deduction may be applied without formal review and confirmation by the course instructor."
    )

    def render_markdown_diff(
        self,
        sub_a_id: str,
        student_a: str,
        code_a: str,
        sub_b_id: str,
        student_b: str,
        code_b: str,
        comparison_res: Dict[str, Any]
    ) -> str:
        sim = comparison_res["composite_similarity"] * 100.0
        containment = comparison_res["containment_similarity"] * 100.0
        cosine = comparison_res["ast_vector_cosine"] * 100.0
        shared_fp = comparison_res["shared_fingerprints_count"]

        flag_status = "[FLAGGED FOR INSTRUCTOR REVIEW]" if sim >= 70.0 else "[BELOW FLAG THRESHOLD]"
        status_color = "CRITICAL SIMILARITY" if sim >= 85.0 else "SUSPICIOUS OVERLAP" if sim >= 70.0 else "UNLIKELY PLAGIARISM"

        lines_a = code_a.strip().split("\n")
        lines_b = code_b.strip().split("\n")
        max_lines = max(len(lines_a), len(lines_b))

        # Build side by side lines
        diff_table = "| Line | Submission A (`" + sub_a_id + "`: " + student_a + ") | Line | Submission B (`" + sub_b_id + "`: " + student_b + ") |\n"
        diff_table += "|:---:|:---|:---:|:---|\n"

        for idx in range(max_lines):
            l_a = lines_a[idx].replace("|", "\\|") if idx < len(lines_a) else ""
            l_b = lines_b[idx].replace("|", "\\|") if idx < len(lines_b) else ""
            line_no_a = str(idx + 1) if idx < len(lines_a) else ""
            line_no_b = str(idx + 1) if idx < len(lines_b) else ""
            diff_table += f"| `{line_no_a}` | `{l_a}` | `{line_no_b}` | `{l_b}` |\n"

        md = f"""### {flag_status}: {status_color} ({sim:.1f}%)

{self.POLICY_DISCLAIMER}

#### Plagiarism Telemetry
- **Composite Similarity:** `{sim:.1f}%`
- **Winnowing Containment:** `{containment:.1f}%` ({shared_fp} shared k-gram fingerprints)
- **AST Vector Cosine:** `{cosine:.1f}%`
- **Recommended Action:** {"Flag for teacher review meeting" if sim >= 70.0 else "No action required"}

#### Side-by-Side Source Inspection
{diff_table}
"""
        return md
