import os

from dotenv import load_dotenv

from langchain_community.document_loaders import (
    PyPDFDirectoryLoader,
    TextLoader
)

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from langchain_chroma import Chroma


load_dotenv()


def load_documents():

    documents = []

    # PDFs
    pdf_loader = PyPDFDirectoryLoader(
        "data/brochures"
    )

    documents.extend(
        pdf_loader.load()
    )

    # FAQ
    faq_loader = TextLoader(
        "data/faq.txt",
        encoding="utf-8"
    )

    documents.extend(
        faq_loader.load()
    )

    print(
        f"Loaded {len(documents)} documents"
    )

    return documents


def split_documents(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )

    chunks = splitter.split_documents(
        documents
    )

    print(
        f"Created {len(chunks)} chunks"
    )

    return chunks


def create_vector_store(chunks):

    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001"
    )

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./chroma_db",
        collection_name="properties"
    )

    print("ChromaDB created successfully.")

    return vectorstore


if __name__ == "__main__":

    documents = load_documents()

    chunks = split_documents(
        documents
    )

    create_vector_store(
        chunks
    )