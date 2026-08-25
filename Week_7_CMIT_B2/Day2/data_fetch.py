from dotenv import load_dotenv

from langchain_chroma import Chroma

from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI
)

from langchain_core.prompts import ChatPromptTemplate


load_dotenv()


embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001"
)


vectorstore = Chroma(
    persist_directory="./chroma_db",
    collection_name="properties",
    embedding_function=embeddings
)


retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 4
    }
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)


prompt = ChatPromptTemplate.from_template(
    """
You are a property assistant.

Answer the user's question using ONLY
the provided context.

If the answer cannot be found in the
context, say that you don't have enough
information.

Context:
{context}

Question:
{question}

Answer:
"""
)

def ask_question(question):

    documents = retriever.invoke(question)

    context = "\n\n".join(
        doc.page_content
        for doc in documents
    )

    messages = prompt.format_messages(
        context=context,
        question=question
    )

    response = llm.invoke(messages)

    return response.content

if __name__ == "__main__":

    question = input(
        "Ask a property question: "
    )

    answer = ask_question(
        question
    )

    print("\nAnswer:")
    print(answer)