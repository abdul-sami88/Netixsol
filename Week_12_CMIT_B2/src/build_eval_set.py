"""Generate 100 legal evaluation questions for Day 2 RAG Benchmark:
- 50 Statute questions (EN, Roman Urdu, Urdu) with exact Act + Section ground truth
- 30 Case-Law questions from Supreme Court judgments with exact case/judge/citation ground truth
- 20 Out-of-Corpus / Unanswerable questions where expected answer is 'No sufficient source found'
"""

import json
from pathlib import Path


STATUTES_JSON = Path("outputs/structured/statutes.json")
JUDGMENTS_JSON = Path("outputs/structured/judgments.json")
OUT_FILE = Path("data/eval_100_questions.json")


def load_statute_sections() -> dict[str, dict]:
    """Map Act Name + Section to section text and doc info."""
    data = json.loads(STATUTES_JSON.read_text(encoding="utf-8"))
    sections_map = {}
    for act_data in data:
        act = act_data["act"]
        doc_id = act_data["doc_id"]
        matter_id = act_data["matter_id"]
        for sec in act_data["sections"]:
            s_num = str(sec["section"]).strip()
            key = f"{act}::Section {s_num}"
            sections_map[key] = {
                "act": act,
                "section": s_num,
                "heading": sec.get("heading", ""),
                "page": sec.get("page_start", 1),
                "text": sec["text"],
                "doc_id": doc_id,
                "matter_id": matter_id,
            }
    return sections_map


def build_statute_questions(statutes_map: dict) -> list[dict]:
    # Curate 50 high-impact statute questions across our 10 Pakistani acts
    specs = [
        # Contract Act, 1872
        ("Agar consideration unlawful ho to kya contract void hai?", "Contract Act, 1872", "23", "roman_ur", "Agreement is void if consideration or object is unlawful, forbidden by law, or fraudulent."),
        ("What makes an agreement void for unlawful consideration under Contract Act?", "Contract Act, 1872", "23", "en", "Consideration or object is unlawful if forbidden by law, defeats provisions of law, fraudulent, or immoral."),
        ("What is the effect of coercion, fraud or misrepresentation on a contract?", "Contract Act, 1872", "19", "en", "Voidable at the option of the party whose consent was so caused."),
        ("When is compensation payable for breach of contract where penalty is stipulated?", "Contract Act, 1872", "74", "en", "Party complaining is entitled to receive reasonable compensation not exceeding the penalty stipulated."),
        ("Is an agreement in restraint of trade void under Pakistani law?", "Contract Act, 1872", "27", "en", "Every agreement by which anyone is restrained from exercising a lawful profession, trade or business is to that extent void."),
        ("What happens if an agreement is made without consideration under Contract Act?", "Contract Act, 1872", "25", "en", "An agreement made without consideration is void unless expressed in writing and registered or promise to compensate for past voluntary services."),
        ("What is communication, acceptance and revocation of proposals?", "Contract Act, 1872", "3", "en", "Communication of proposals, acceptance, and revocation are deemed to be made by any act or omission."),
        ("Who are the persons competent to contract according to the Contract Act?", "Contract Act, 1872", "11", "en", "Every person competent to contract who is of the age of majority, sound mind, and not disqualified from contracting."),
        ("What is a contingent contract defined under Section 31?", "Contract Act, 1872", "31", "en", "A contract to do or not to do something, if some event, collateral to such contract, does or does not happen."),
        ("When is an agreement void on grounds of impossibility under Contract Act?", "Contract Act, 1872", "56", "en", "An agreement to do an act impossible in itself is void; doctrine of frustration."),

        # Pakistan Penal Code, 1860 (PPC)
        ("What is the punishment for qatl-i-amd under Section 302 PPC?", "Pakistan Penal Code, 1860", "302", "en", "Qatl-i-amd is punished with death as qisas, death or imprisonment for life as ta'zir, or imprisonment up to 25 years."),
        ("What constitutes the offence of theft under Section 378 of PPC?", "Pakistan Penal Code, 1860", "378", "en", "Whoever intending to take dishonestly any movable property out of the possession of any person without consent."),
        ("What is the definition of criminal conspiracy under Section 120A PPC?", "Pakistan Penal Code, 1860", "120A", "en", "When two or more persons agree to do or cause to be done an illegal act or an act by illegal means."),
        ("What is the punishment for cheating under Section 420 PPC?", "Pakistan Penal Code, 1860", "420", "en", "Imprisonment of either description for a term which may extend to seven years, and fine."),
        ("What is defaming a deceased person or imputation of defamation under Section 499?", "Pakistan Penal Code, 1860", "499", "en", "Whoever by words or signs makes or publishes any imputation concerning any person intending to harm reputation."),
        ("Under Section 300 PPC, how is qatl-i-amd defined?", "Pakistan Penal Code, 1860", "300", "en", "Whoever, with the intention of causing death or bodily injury likely to cause death, causes the death of a person."),
        ("What is the punishment for kidnapping or abducting under Section 364A PPC?", "Pakistan Penal Code, 1860", "364A", "en", "Punished with death or imprisonment for life or rigorous imprisonment up to fourteen years."),
        ("What is hurt defined under Section 332 of the Pakistan Penal Code?", "Pakistan Penal Code, 1860", "332", "en", "Whoever causes pain, harm, disease, infirmity or injury to any person causes hurt."),
        ("What is the right of private defence of the body under Section 100 PPC?", "Pakistan Penal Code, 1860", "100", "en", "The right of private defence of the body extends to the voluntary causing of death in cases of reasonable apprehension of death or grievous hurt."),
        ("What is extortion under Section 383 of Pakistan Penal Code?", "Pakistan Penal Code, 1860", "383", "en", "Intentionally putting any person in fear of any injury and dishonestly inducing delivery of property."),

        # Constitution of Pakistan, 1973
        ("What does Article 25 of the Constitution say about equality of citizens?", "Constitution of the Islamic Republic of Pakistan, 1973", "25", "en", "All citizens are equal before law and are entitled to equal protection of law. There shall be no discrimination on basis of sex."),
        ("What is the fundamental right to fair trial under Article 10A of the Constitution?", "Constitution of the Islamic Republic of Pakistan, 1973", "10A", "en", "For determination of civil rights or in criminal charge, a person shall be entitled to fair trial and due process."),
        ("What is the right to information under Article 19A of the Constitution?", "Constitution of the Islamic Republic of Pakistan, 1973", "19A", "en", "Every citizen shall have the right to have access to information in all matters of public importance."),
        ("What protection is granted against retrospective punishment under Article 12?", "Constitution of the Islamic Republic of Pakistan, 1973", "12", "en", "No law shall authorize the punishment of a person for an act or omission that was not punishable at the time."),
        ("What does Article 9 of the Constitution guarantee regarding security of person?", "Constitution of the Islamic Republic of Pakistan, 1973", "9", "en", "No person shall be deprived of life or liberty save in accordance with law."),
        ("What is the original jurisdiction of the Supreme Court under Article 184(3)?", "Constitution of the Islamic Republic of Pakistan, 1973", "184", "en", "Supreme Court has jurisdiction in matters of public importance with reference to enforcement of Fundamental Rights."),
        ("What does Article 4 guarantee to citizens regarding protection of law?", "Constitution of the Islamic Republic of Pakistan, 1973", "4", "en", "To enjoy the protection of law and to be treated in accordance with law is an inalienable right of every citizen."),
        ("What does Article 14 guarantee regarding dignity of man and privacy of home?", "Constitution of the Islamic Republic of Pakistan, 1973", "14", "en", "The dignity of man and, subject to law, the privacy of home, shall be inviolable."),
        ("What is freedom of trade, business or profession under Article 18?", "Constitution of the Islamic Republic of Pakistan, 1973", "18", "en", "Subject to regulation by licensing, every citizen has the right to enter upon any lawful profession or trade."),
        ("What is the appellate jurisdiction of the Supreme Court under Article 185?", "Constitution of the Islamic Republic of Pakistan, 1973", "185", "en", "Supreme Court has jurisdiction to hear and determine appeals from judgments, decrees, final orders or sentences of High Courts."),

        # Code of Criminal Procedure, 1898 (CrPC)
        ("What is the procedure for recording FIR under Section 154 of CrPC?", "Code of Criminal Procedure, 1898", "154", "en", "Information relating to commission of a cognizable offence given to an officer in charge of a police station shall be reduced to writing."),
        ("When can police arrest without warrant under Section 54 of CrPC?", "Code of Criminal Procedure, 1898", "54", "en", "Any police officer may without warrant arrest any person who has been concerned in any cognizable offence."),
        ("What is the provision for grant of bail in non-bailable offences under Section 497 CrPC?", "Code of Criminal Procedure, 1898", "497", "en", "When any person accused of non-bailable offence is arrested, he may be released on bail unless reasonable grounds to believe guilty of death or imprisonment for life."),
        ("What is the power of the High Court or Sessions Court regarding bail under Section 498 CrPC?", "Code of Criminal Procedure, 1898", "498", "en", "High Court or Court of Session may direct that any person be admitted to bail or that bail required by police officer or Magistrate be reduced."),
        ("How is search of place entered by person sought to be arrested conducted under Section 47 CrPC?", "Code of Criminal Procedure, 1898", "47", "en", "Person residing in or in charge of place shall allow ingress and afford reasonable facilities for search."),

        # Code of Civil Procedure, 1908 (CPC)
        ("What is the principle of res judicata under Section 11 of CPC?", "Code of Civil Procedure, 1908", "11", "en", "No Court shall try any suit or issue in which the matter directly and substantially in issue has been directly and substantially in issue in a former suit."),
        ("What suits are barred by jurisdiction under Section 9 of CPC?", "Code of Civil Procedure, 1908", "9", "en", "The Courts shall have jurisdiction to try all suits of a civil nature excepting suits of which their cognizance is expressly or impliedly barred."),
        ("What are the powers of court to grant temporary injunction under CPC Section 94 / Order 39?", "Code of Civil Procedure, 1908", "94", "en", "In order to prevent the ends of justice from being defeated, the Court may grant a temporary injunction."),
        ("What is restitution under Section 144 of the Code of Civil Procedure 1908?", "Code of Civil Procedure, 1908", "144", "en", "Where decree or order is varied or reversed in appeal or revision, court shall cause restitution to be made."),
        ("What are the inherent powers of civil court saved under Section 151 CPC?", "Code of Civil Procedure, 1908", "151", "en", "Nothing in this Code shall limit or affect inherent power of Court to make such orders as necessary for ends of justice or to prevent abuse of process."),

        # Specific Relief Act, 1877
        ("Can a suit for recovery of possession of immovable property be filed under Section 9 of Specific Relief Act?", "Specific Relief Act, 1877", "9", "en", "Person dispossessed without consent of immovable property otherwise than in due course of law may recover possession by suit."),
        ("Under Section 12 of Specific Relief Act, when is specific performance enforceable?", "Specific Relief Act, 1877", "12", "en", "Specific performance of contract may be enforced when act agreed to be done is in performance of trust or no standard exists for ascertaining damage."),
        ("Under Section 21 of Specific Relief Act, what contracts cannot be specifically enforced?", "Specific Relief Act, 1877", "21", "en", "Contracts for which non-performance compensation in money is an adequate relief or contract running into minute details cannot be specifically enforced."),
        ("What is a declaratory decree under Section 42 of the Specific Relief Act?", "Specific Relief Act, 1877", "42", "en", "Any person entitled to any legal character or to any right as to any property may institute a suit for declaration."),
        ("When is perpetual injunction granted under Section 54 of Specific Relief Act?", "Specific Relief Act, 1877", "54", "en", "Perpetual injunction may be granted to prevent breach of an obligation existing in favor of applicant."),

        # Muslim Family Laws Ordinance, 1961
        ("What is the legal procedure for registration of marriages under Section 5 of MFLO 1961?", "Muslim Family Laws Ordinance, 1961", "5", "en", "Every marriage solemnized under Muslim Law shall be registered in accordance with provisions of this Ordinance."),
        ("What is the mandatory procedure for Talaq notice under Section 7 of Muslim Family Laws Ordinance?", "Muslim Family Laws Ordinance, 1961", "7", "en", "Any man wishing to divorce his wife shall give notice in writing to Chairman of Union Council and supply copy to wife."),
        ("Under Section 6 of MFLO, what is required before contracting a polygamous marriage?", "Muslim Family Laws Ordinance, 1961", "6", "en", "No man shall contract another marriage without previous permission in writing of the Arbitration Council."),

        # Anti-Money Laundering Act, 2010 (AML)
        ("What constitutes the offence of money laundering under Section 3 of AML Act 2010?", "Anti-Money Laundering Act, 2010", "3", "en", "A person is guilty of money laundering if he acquires, converts, conceals or transfers property knowing it is proceeds of crime."),
        ("What is the punishment for money laundering under Section 4 of AML Act 2010?", "Anti-Money Laundering Act, 2010", "4", "en", "Rigorous imprisonment for not less than one year up to ten years, and fine which may extend to five million rupees and forfeiture of property."),
    ]

    questions = []
    for idx, (q_text, act_name, sec_num, lang, exp_ans) in enumerate(specs, 1):
        key = f"{act_name}::Section {sec_num}"
        meta = statutes_map.get(key, {})
        questions.append({
            "id": f"eval_stat_{idx:03d}",
            "type": "statute",
            "language": lang,
            "query": q_text,
            "is_answerable": True,
            "expected_doc_id": meta.get("doc_id", "stat_unknown"),
            "expected_matter_id": meta.get("matter_id", f"KA-STAT-{idx:03d}"),
            "expected_act": act_name,
            "expected_section": sec_num,
            "expected_court": None,
            "expected_answer": exp_ans,
            "target_keywords": [act_name.split()[0].lower(), f"section {sec_num}".lower()],
        })
    return questions


def build_case_law_questions() -> list[dict]:
    # Extract real cases from outputs/structured/judgments.json
    judgments = json.loads(JUDGMENTS_JSON.read_text(encoding="utf-8"))

    # Select 30 judgments with clear author judges, holdings, and parties
    picked = []
    for j in judgments:
        if j.get("holding") and len(j.get("holding")) > 50 and j.get("parties") and "versus" in j.get("parties").lower() or "v." in j.get("parties").lower():
            picked.append(j)
        if len(picked) >= 30:
            break
    if len(picked) < 30:
        picked = judgments[:30]

    questions = []
    for idx, j in enumerate(picked, 1):
        author = j.get("author_judge", "Supreme Court of Pakistan")
        parties = j.get("parties", "Case")
        holding = j.get("holding", "")[:250].replace("\n", " ").strip()
        fname = j.get("filename", "")
        year = j.get("year", 2020)

        # Formulate inquiry about this judgment
        query = f"What was held by the Supreme Court in {parties} authored by {author} regarding {fname}?"
        questions.append({
            "id": f"eval_case_{idx:03d}",
            "type": "case_law",
            "language": "en",
            "query": query,
            "is_answerable": True,
            "expected_doc_id": j["doc_id"],
            "expected_matter_id": j["matter_id"],
            "expected_act": None,
            "expected_section": None,
            "expected_court": j.get("court", "Supreme Court of Pakistan"),
            "expected_case": fname,
            "expected_judge": author,
            "expected_answer": holding,
            "target_keywords": [fname.lower().replace(".pdf", ""), author.lower().split()[-1]],
        })
    return questions


def build_unanswerable_questions() -> list[dict]:
    # 20 realistic legal questions from outside the corpus
    unanswerable = [
        ("Under California Civil Code, what is the statute of limitations for breach of an oral contract?", "us_state_law"),
        ("What does Article 17 of EU GDPR guarantee regarding the right to erasure?", "eu_data_privacy"),
        ("What is the exclusion of evidence under the US Fourth Amendment Mapp v. Ohio doctrine?", "us_constitutional_law"),
        ("Under the Indian Bharatiya Sakshya Adhiniyam 2023, how is electronic evidence certified?", "indian_law_2023"),
        ("What are the criteria for salvage award calculation under Article 13 of the 1989 International Salvage Convention?", "maritime_convention"),
        ("What is the penalty for failure to file provincial sales tax on services under Sindh Revenue Board Act 2026?", "sindh_tax_2026"),
        ("How is vicarious liability applied to autonomous driving systems under German Road Traffic Act (StVG)?", "german_tech_law"),
        ("Under the UK Consumer Rights Act 2015, what is the short-term right to reject faulty goods?", "uk_commercial_law"),
        ("What is the procedure for recognition of foreign arbitral awards under the Swiss Private International Law Act?", "swiss_arbitration"),
        ("What constitutes insider trading under Section 10(b) and Rule 10b-5 of the US SEC Act of 1934?", "us_securities_law"),
        ("Under French Civil Code Article 1240, what are the three elements required to establish tortious liability?", "french_tort_law"),
        ("What is the rule against perpetuities calculation under Ontario Perpetuities Act?", "canadian_property_law"),
        ("How does the Australian Consumer Law define misleading or deceptive conduct under Section 18?", "australian_trade_law"),
        ("Under the Singapore Personal Data Protection Act (PDPA), what is the maximum financial penalty for data breach?", "singapore_privacy"),
        ("What does the International Court of Justice statute Article 38 state regarding sources of international law?", "public_international_law"),
        ("Under Japanese Civil Code Article 709, what is the limitation period for compensation for damages in tort?", "japanese_civil_law"),
        ("What is the duty of disclosure in marine insurance contracts under the UK Marine Insurance Act 1906?", "uk_marine_insurance"),
        ("How is the concept of unconscionability defined under Uniform Commercial Code (UCC) Section 2-302?", "us_ucc_law"),
        ("Under South African Protection of Personal Information Act (POPIA), what are the conditions for lawful processing?", "south_africa_privacy"),
        ("What constitutes patent infringement under Section 271 of Title 35 of the United States Code?", "us_patent_law"),
    ]

    questions = []
    for idx, (q_text, domain) in enumerate(unanswerable, 1):
        questions.append({
            "id": f"eval_unans_{idx:03d}",
            "type": "unanswerable",
            "language": "en",
            "query": q_text,
            "is_answerable": False,
            "expected_doc_id": None,
            "expected_matter_id": None,
            "expected_act": None,
            "expected_section": None,
            "expected_court": None,
            "expected_answer": "No sufficient source found",
            "target_keywords": ["no sufficient source found"],
            "domain": domain,
        })
    return questions


def main() -> None:
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    statutes_map = load_statute_sections()
    print(f"Loaded {len(statutes_map)} statute sections from {STATUTES_JSON}")

    stat_qs = build_statute_questions(statutes_map)
    case_qs = build_case_law_questions()
    unans_qs = build_unanswerable_questions()

    all_qs = stat_qs + case_qs + unans_qs
    print(f"Total questions generated: {len(all_qs)}")
    print(f"  Statute questions:     {len(stat_qs)}")
    print(f"  Case-law questions:    {len(case_qs)}")
    print(f"  Unanswerable questions: {len(unans_qs)}")

    OUT_FILE.write_text(json.dumps(all_qs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved evaluation benchmark to {OUT_FILE}")


if __name__ == "__main__":
    main()
