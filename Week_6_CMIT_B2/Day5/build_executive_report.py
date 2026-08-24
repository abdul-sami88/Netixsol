"""
build_executive_report.py
--------------------------
Task 5: generates EXECUTIVE_REPORT.pdf (2 pages).
Run once: python3 build_executive_report.py
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
)
from reportlab.lib import colors

doc = SimpleDocTemplate(
    "EXECUTIVE_REPORT.pdf",
    pagesize=letter,
    topMargin=0.6 * inch,
    bottomMargin=0.6 * inch,
    leftMargin=0.7 * inch,
    rightMargin=0.7 * inch,
)

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleX", parent=styles["Title"], fontSize=18, spaceAfter=4)
subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=10, textColor=colors.grey, spaceAfter=14)
h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12.5, spaceBefore=10, spaceAfter=4, textColor=colors.HexColor("#1a1a1a"))
body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.8, leading=14, alignment=TA_LEFT, spaceAfter=6)
small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8.6, leading=12, textColor=colors.HexColor("#333333"), spaceAfter=6)
bullet_style = ParagraphStyle("Bullet", parent=body, leftIndent=14, spaceAfter=4)

story = []

story.append(Paragraph("AFL Assistant — Executive Report", title_style))
story.append(Paragraph("Domain-locked chat, retrieval &amp; prediction assistant — capstone summary", subtitle_style))

# --- Product goal ---
story.append(Paragraph("Product Goal", h2))
story.append(Paragraph(
    "Ship a single AFL assistant that can answer factual questions, retrieve real statistics, and make "
    "match/player predictions — without ever confusing the three. The core product requirement is trust: a "
    "prediction must always be framed as a probability with a disclaimer, never presented as a guaranteed "
    "outcome, and the assistant must stay strictly within AFL scope even under adversarial prompting.",
    body,
))

# --- Architecture ---
story.append(Paragraph("Architecture", h2))
story.append(Paragraph(
    "Built as a LangGraph state machine rather than one free-form agent, specifically because the general "
    "chat/retrieval agent (Gemini-backed, with five retrieval tools over historical match/player data) has "
    "<b>no prediction capability at all</b>. A single agent handed a prediction-shaped query would have to "
    "either refuse incorrectly or hallucinate a winner from language-model \u201cknowledge\u201d — unacceptable for a "
    "stats-grounded product. The router intercepts prediction-shaped queries before they can reach that agent:",
    body,
))
story.append(ListFlowable([
    ListItem(Paragraph("<b>Router</b> — classifies each query as factual / retrieval / prediction (match or player) / "
                        "off-topic / unsupported, using a deterministic rule-based classifier by default (a "
                        "swappable Gemini-based classifier is available for better generalisation).", bullet_style)),
    ListItem(Paragraph("<b>Prediction path</b> — resolves team names against the real dataset, calls fitted "
                        "scikit-learn pipelines (Logistic Regression for match winner, Gradient Boosting for top "
                        "disposal-getter), and validates the result before it can reach the user.", bullet_style)),
    ListItem(Paragraph("<b>Chat/retrieval path</b> — delegates factual, retrieval, and off-topic queries entirely "
                        "to the existing Day 3 agent rather than reimplementing that logic.", bullet_style)),
    ListItem(Paragraph("<b>Validation &amp; clarification</b> — an unresolved team name asks the user to clarify "
                        "instead of guessing; a genuinely out-of-scope prediction (e.g. an exact score, or \u201cwho "
                        "wins the Grand Final\u201d) gets an honest \u201ccan't do that\u201d response, not a hallucination.", bullet_style)),
    ListItem(Paragraph("<b>API/UI</b> — a FastAPI wrapper (structured JSON logging, real async timeouts, basic "
                        "abuse-signal tracking) and a Streamlit chat UI sit on top for demoing and integration.", bullet_style)),
], bulletType="bullet", start="circle", leftIndent=12))

# --- Evaluation results ---
story.append(Paragraph("Evaluation Results", h2))
story.append(Paragraph(
    "A 34-case suite spanning four categories currently passes 100% offline (router + real prediction models + "
    "a scripted stand-in for the live chat agent). This validates the graph's structure — routing correctness, "
    "fail-closed behavior on unresolved entities, and multi-turn state handling — which is fully testable "
    "without external dependencies:",
    body,
))

table_data = [
    ["Category", "Cases", "Pass", "What it covers"],
    ["Factual Q&A routing", "7", "100%", "Correct routing of AFL rules/history questions"],
    ["Prediction sanity", "9", "100%", "Probabilities move sensibly with matchup strength; reversed home/away; degenerate cases"],
    ["Scope guardrails", "11", "100%", "Off-topic refusal, unsupported-scope handling, 5 prompt-injection attempts"],
    ["Multi-turn coherence", "7", "100%", "Context across turns; recovery after a clarification round"],
]
t = Table(table_data, colWidths=[1.25*inch, 0.4*inch, 0.45*inch, 4.0*inch])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b2b2b")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
]))
story.append(t)
story.append(Spacer(1, 6))
story.append(Paragraph(
    "<b>Important caveat:</b> the offline suite uses a scripted stand-in for the live Gemini chat agent (no "
    "API key in this evaluation environment). It validates plumbing, not live answer quality or live "
    "prompt-injection resistance — both must be re-verified against the real agent before launch.",
    small,
))
story.append(Paragraph(
    "<b>Benchmark context:</b> the match-winner model reaches 63.4% test accuracy vs. a 56.3% naive baseline "
    "(always predict the home team) — a real but modest ~7-point lift; AFL outcomes are genuinely hard to "
    "predict from pre-match features alone. The top-player model's 63.0% top-5 hit rate is currently "
    "<b>below</b> an even simpler baseline (71.9%, \u201clast week's leader repeats\u201d) — it is retained for its "
    "explainable, grounded reasoning rather than raw accuracy, and this should be stated plainly to "
    "stakeholders rather than glossed over.",
    body,
))

story.append(Spacer(1, 4))
story.append(Paragraph("Known Limitations", h2))
story.append(ListFlowable([
    ListItem(Paragraph("<b>Data recency / no real fixture calendar.</b> Predictions use each team's latest known "
                        "rolling state rather than a specific upcoming fixture with a real date/venue — \u201cthis "
                        "week\u201d is not tied to an actual schedule in the current data.", bullet_style)),
    ListItem(Paragraph("<b>Model accuracy ceiling.</b> 63.4% match-winner accuracy is a real, useful signal, not "
                        "a confident oracle; the top-player model does not currently beat its naive baseline.", bullet_style)),
    ListItem(Paragraph("<b>Rule-based router has no coreference resolution</b> — a follow-up like \u201cwhat about "
                        "their stats\u201d needs a named team, not a pronoun, unless the Gemini-based router variant "
                        "is enabled.", bullet_style)),
    ListItem(Paragraph("<b>Guardrail edge cases</b> are evaluated here against a stand-in agent; live "
                        "verification against the real Gemini-backed agent is a required pre-launch step.", bullet_style)),
], bulletType="bullet", start="circle", leftIndent=12))

story.append(Paragraph("Recommended Next Steps", h2))
story.append(ListFlowable([
    ListItem(Paragraph("Source a real fixture calendar so predictions can be tied to actual upcoming matches, "
                        "venues, and dates rather than \u201clatest known state.\u201d", bullet_style)),
    ListItem(Paragraph("Stand up the weekly data-refresh / monthly retraining loop described in the monitoring "
                        "plan, with accuracy-drift alerting against the documented baselines.", bullet_style)),
    ListItem(Paragraph("Either improve the top-player model past its naive baseline or reframe its role in the "
                        "product as explanatory context rather than a headline prediction.", bullet_style)),
    ListItem(Paragraph("Move the in-memory abuse-signal tracker to a shared store (e.g. Redis) before any "
                        "multi-instance production deployment.", bullet_style)),
], bulletType="bullet", start="circle", leftIndent=12))

story.append(Spacer(1, 16))
story.append(Paragraph("Bottom line", h2))
story.append(Paragraph(
    "The system is structurally sound and honest about its own limits — predictions are always hedged, "
    "off-topic requests (including adversarial ones) are refused rather than answered, and the two areas "
    "where the model genuinely underperforms (top-scorer prediction vs. a naive baseline; no real fixture "
    "calendar) are surfaced here rather than hidden. It is ready for a live-agent verification pass and a "
    "staged rollout, not yet for an unmonitored production launch.",
    body,
))
story.append(Spacer(1, 10))
story.append(Paragraph(
    "Full codebase, evaluation logs, monitoring checklist, and demo script accompany this report.",
    small,
))

doc.build(story)
print("Wrote EXECUTIVE_REPORT.pdf")
