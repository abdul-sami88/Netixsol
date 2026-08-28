"""
chunking.py — Task 2 step 2.

Splits documents into chunks by word count with configurable overlap.
Since each `Document` here (a property brochure or an FAQ) is already
short (~50-90 words), chunk_size mainly matters when documents are
concatenated for evaluation purposes (chunk_experiment.py). This module
still implements a real chunker so it generalizes to longer brochures.
"""
from dataclasses import dataclass
from document_loader import Document


@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: dict


def chunk_document(doc: Document, chunk_size: int = 100, overlap: int = 20) -> list[Chunk]:
    words = doc.text.split()
    if len(words) <= chunk_size:
        return [Chunk(chunk_id=f"{doc.doc_id}_0", text=doc.text, metadata=doc.metadata)]

    chunks = []
    start = 0
    idx = 0
    step = max(1, chunk_size - overlap)
    while start < len(words):
        piece = words[start:start + chunk_size]
        chunks.append(Chunk(
            chunk_id=f"{doc.doc_id}_{idx}",
            text=" ".join(piece),
            metadata=doc.metadata,
        ))
        idx += 1
        start += step
    return chunks


def chunk_documents(docs: list[Document], chunk_size: int = 100, overlap: int = 20) -> list[Chunk]:
    out = []
    for d in docs:
        out.extend(chunk_document(d, chunk_size, overlap))
    return out
