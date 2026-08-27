"""
document_loader.py — Task 2 step 1.

Loads the *unstructured* documents that will be embedded for semantic
retrieval: property descriptions/brochures and FAQs. (Prices, availability,
plot sizes, agent names stay in SQL — see retriever.py / Task 3.)
"""
import sqlite3
from dataclasses import dataclass, field


@dataclass
class Document:
    doc_id: str
    text: str
    metadata: dict = field(default_factory=dict)


def load_documents(db_path: str) -> list[Document]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    docs = []

    # Property descriptions/brochures, enriched with amenity + nearby-facility
    # context so semantic search can surface "brochure-style" answers.
    cur.execute("""
        SELECT d.property_id, d.text, p.city, p.locality, p.property_type,
               p.price, p.purpose, p.bedrooms, p.area
        FROM descriptions d JOIN properties p ON p.property_id = d.property_id
    """)
    for row in cur.fetchall():
        amen = conn.execute(
            "SELECT amenity_name FROM amenities WHERE property_id=?", (row["property_id"],)
        ).fetchall()
        amen_txt = ", ".join(a["amenity_name"] for a in amen)
        text = row["text"]
        if amen_txt and "Amenities include" not in text:
            text += f" Amenities include: {amen_txt}."
        docs.append(Document(
            doc_id=f"property_{row['property_id']}",
            text=text,
            metadata={"type": "property_description", "property_id": row["property_id"],
                      "city": row["city"], "locality": row["locality"]},
        ))

    # FAQs
    cur.execute("SELECT faq_id, question, answer, category, language FROM faqs")
    for row in cur.fetchall():
        docs.append(Document(
            doc_id=str(row["faq_id"]),
            text=f"Q: {row['question']} A: {row['answer']}",
            metadata={"type": "faq", "category": row["category"], "language": row["language"]},
        ))

    conn.close()
    return docs


if __name__ == "__main__":
    import os
    docs = load_documents(os.path.join(os.path.dirname(__file__), "..", "db", "real_estate.db"))
    print(f"Loaded {len(docs)} documents")
    print(docs[0])
