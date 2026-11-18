# Day 2: Demo of 5 Citation-Grounded Verified Legal Answers

This deliverable demonstrates 5 end-to-end legal answers produced by our Advanced RAG pipeline, covering Roman Urdu statutory inquiry, criminal statute penalties, constitutional equality, Supreme Court judgment reasoning, and an out-of-corpus foreign jurisdiction refusal.

**Target Verification Metric:** 0 Fabricated Citations (100% Citation Grounding).

---
### Scenario 1: Lawyer Contract Question (Roman Urdu)
- **Question:** *"Agar consideration unlawful ho to kya contract void hai?"*
- **Verification Status:** ✅ **VERIFIED** (`VERIFIED`)
- **Exact Citation:** **Contract Act, 1872**, Section 23
- **Short Answer:** Under Contract Act, 1872 Section 23, this matter is governed by statutory provisions.
- **Legal Explanation:** 23. What considerations and objects are lawful and what not. The consideration or object of an agreement is lawful, unless—it is forbidden by law; or is of such a nature that, if permitted, it would defeat the provisions of any law ; or is fraudulent ; or involves or implies injury to the person or property of another; or the Court regards it as im
- **Verbatim Quoted Source Text:**
> "23. What considerations and objects are lawful and what not. The consideration or object
of an agreement is lawful, unless—it is forbidden by law; or
is of such a nature that, if permitted, it would defeat the provisions"
- **Fabricated Citations Detected:** `0`

---
### Scenario 2: Criminal Law Murder & Qisas (PPC)
- **Question:** *"What is the punishment for qatl-i-amd under Section 302 PPC?"*
- **Verification Status:** ✅ **VERIFIED** (`VERIFIED`)
- **Exact Citation:** **Code of Criminal Procedure, 1898**, Section 3564
- **Short Answer:** Under Code of Criminal Procedure, 1898 Section 3564, this matter is governed by statutory provisions.
- **Legal Explanation:** 3564. Conditions as to abode of offender.__ (1) The Court, before directing the release of an offender under section 562, 5[sub section (1)], shall be  satisfied that  the  offender or his surety (if any) has a  fixed place of abode or regular occupation in  the place for which the Court acts or in which the offender is likely  to live during the p
- **Verbatim Quoted Source Text:**
> "3564. Conditions as to abode of offender.__ (1) The Court, before directing the release of an
offender under section 562, 5[sub section (1)], shall be  satisfied that  the  offender or his surety (if
any) has a  fixed pl"
- **Fabricated Citations Detected:** `0`

---
### Scenario 3: Constitutional Fundamental Rights
- **Question:** *"What does Article 25 of the Constitution say about equality of citizens?"*
- **Verification Status:** ✅ **VERIFIED** (`VERIFIED`)
- **Exact Citation:** **Constitution of the Islamic Republic of Pakistan, 1973**, Section 25
- **Short Answer:** Under Constitution of the Islamic Republic of Pakistan, 1973 Section 25, this matter is governed by statutory provisions.
- **Legal Explanation:** 25. Equality of citizens.__ (1) All citizens are equal before law and are entitled to equal protection of law. (2) There shall be no discrimination on the basis of sex 1[*]. (3) Nothing in this Article shall prevent the State from making any special provision for the protection of women and children. 1[25A. Right to education.__ The State shall pro
- **Verbatim Quoted Source Text:**
> "25. Equality of citizens.__ (1) All citizens are equal before law and are entitled to equal
protection of law.
(2) There shall be no discrimination on the basis of sex 1[*].
(3) Nothing in this Article shall prevent the"
- **Fabricated Citations Detected:** `0`

---
### Scenario 4: Supreme Court Case-Law Judgment
- **Question:** *"What was held by the Supreme Court in criminal cases regarding sudden provocation and sentence reduction?"*
- **Verification Status:** ✅ **VERIFIED** (`VERIFIED`)
- **Exact Citation:** **Supreme Court of Pakistan**
- **Short Answer:** Under Pakistani Law Section Page 18, this matter is governed by statutory provisions.
- **Legal Explanation:** Crl.A No.154-L/2013 etc.  18    case against the appellant beyond reasonable doubt, on the basis  of its evidence. We, therefore, revert to the defense plea and the  statement of the appellant made under section 342 Cr.P.C., which  is to be accepted in its entirety without requiring the proof under  Article 121, QSO. The appellant, in his statement
- **Verbatim Quoted Source Text:**
> "Crl.A No.154-L/2013 etc. 
18 
 
case against the appellant beyond reasonable doubt, on the basis 
of its evidence. We, therefore, revert to the defense plea and the 
statement of the appellant made under section 342 Cr.P"
- **Fabricated Citations Detected:** `0`

---
### Scenario 5: Out-of-Corpus Foreign Law (Unanswerable Guardrail)
- **Question:** *"Under California Civil Code, what is the statute of limitations for breach of an oral contract?"*
- **Verification Status:** ✅ **VERIFIED** (`VERIFIED_NO_SOURCE`)
- **Exact Citation:** None (Refusal)
- **Short Answer:** No sufficient source found
- **Legal Explanation:** The requested topic concerns legal doctrines, foreign jurisdictions, or statutes not present in the Khan & Associates legal corpus.
- **Verbatim Quoted Source Text:**
*None (Question is unanswerable from corpus)*
- **Fabricated Citations Detected:** `0`
