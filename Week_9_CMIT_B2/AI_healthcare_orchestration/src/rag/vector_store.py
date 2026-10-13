"""
ChromaDB Vector Store Manager for City Care Clinics Medical Knowledge RAG
Chunks and indexes:
- Clinic FAQs, fees, branches, and operational timings
- Lab test preparation and sampling instructions
- Patient education and home care leaflets
- Symptom to specialty mapping rules
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
CHROMA_PERSIST_DIR = PROJECT_ROOT / "data" / "chroma_db"
CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

COLLECTION_NAME = "city_care_medical_knowledge"


def chunk_markdown_document(file_path: Path) -> List[Dict[str, Any]]:
    """
    Semantically chunks markdown files by section headers (## or ###),
    preserving section titles and source metadata.
    """
    text = file_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    
    chunks = []
    current_section = "Overview"
    current_content = []
    file_name = file_path.name
    category = file_name.replace(".md", "")

    for line in lines:
        if line.startswith("## ") or line.startswith("### "):
            if current_content:
                chunk_text = "\n".join(current_content).strip()
                if len(chunk_text) > 40:
                    chunks.append({
                        "text": chunk_text,
                        "source": file_name,
                        "category": category,
                        "section": current_section
                    })
                current_content = []
            current_section = line.lstrip("#").strip()
            current_content.append(line)
        else:
            current_content.append(line)

    if current_content:
        chunk_text = "\n".join(current_content).strip()
        if len(chunk_text) > 40:
            chunks.append({
                "text": chunk_text,
                "source": file_name,
                "category": category,
                "section": current_section
            })

    return chunks


class MedicalKnowledgeVectorStore:
    def __init__(self, persist_dir: Optional[Path] = None):
        self.persist_dir = str(persist_dir or CHROMA_PERSIST_DIR)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "City Care Clinics clinical and operational guidelines"}
        )

    def build_or_refresh_index(self, force: bool = False):
        """Indexes all markdown knowledge documents into ChromaDB."""
        count = self.collection.count()
        if count > 0 and not force:
            print(f"[VectorStore] Existing index loaded with {count} chunks.")
            return count

        print("[VectorStore] Indexing knowledge documents into ChromaDB...")
        md_files = list(KNOWLEDGE_BASE_DIR.glob("*.md"))
        if not md_files:
            raise FileNotFoundError(f"No markdown documents found in {KNOWLEDGE_BASE_DIR}")

        all_chunks = []
        for f in md_files:
            chunks = chunk_markdown_document(f)
            all_chunks.extend(chunks)

        if not all_chunks:
            raise ValueError("No valid chunks extracted from knowledge base.")

        # If re-indexing, clear old entries
        if count > 0:
            self.client.delete_collection(COLLECTION_NAME)
            self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)

        ids = [f"chunk_{i:04d}" for i in range(len(all_chunks))]
        documents = [c["text"] for c in all_chunks]
        metadatas = [
            {
                "source": c["source"],
                "category": c["category"],
                "section": c["section"]
            }
            for c in all_chunks
        ]

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        new_count = self.collection.count()
        print(f"[VectorStore] Successfully indexed {new_count} chunks into ChromaDB.")
        return new_count

    def search(self, query: str, top_k: int = 3, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Queries ChromaDB and returns top matching snippets with similarity distances and metadata.
        """
        where_clause = {"category": category_filter} if category_filter else None
        
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_clause
        )

        formatted = []
        if results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(docs)
            
            for doc, meta, dist in zip(docs, metas, dists):
                formatted.append({
                    "content": doc,
                    "source": meta.get("source", "unknown"),
                    "category": meta.get("category", "unknown"),
                    "section": meta.get("section", "unknown"),
                    "distance": dist
                })
                
        return formatted


# Singleton instance
_vector_store_instance = None

def get_vector_store() -> MedicalKnowledgeVectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = MedicalKnowledgeVectorStore()
    return _vector_store_instance
