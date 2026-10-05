import os
import time
from dotenv import load_dotenv
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

chroma_client = chromadb.PersistentClient(
    path="chroma_db"
)

collection = chroma_client.get_or_create_collection(
    name="pdf_documents"
)


def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def split_text(text, chunk_size=1000, overlap=200):
    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        start += chunk_size - overlap

    return chunks


def create_embeddings(chunks):
    embeddings = embedding_model.encode(
        chunks,
        show_progress_bar=True
    )

    return embeddings.tolist()


def add_pdf_to_database(pdf_path):
    text = extract_text_from_pdf(pdf_path)

    if not text.strip():
        raise ValueError(
            "No readable text found in the PDF."
        )

    chunks = split_text(text)

    embeddings = create_embeddings(chunks)

    ids = [
        f"chunk_{i}"
        for i in range(len(chunks))
    ]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings
    )

    return len(chunks)


def search_documents(question, top_k=5):
    question_embedding = embedding_model.encode(
        [question]
    )[0].tolist()

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k
    )

    documents = results["documents"][0]

    return documents


def generate_answer(question):

    relevant_documents = search_documents(question)

    context = "\n\n".join(
        relevant_documents
    )

    prompt = f"""
You are a helpful PDF question-answering assistant.

Answer the user's question using ONLY the information
provided in the context below.

If the answer cannot be found in the context, say:

"I couldn't find the answer in the uploaded PDF."

Do not make up information.

Context:

{context}

Question:

{question}

Answer:
"""

    for attempt in range(3):

        try:

            response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt

            )

            if response.text:
                return response.text

            return "I couldn't generate an answer."

        except Exception as error:

            error_message = str(error)

            if "503" in error_message or "UNAVAILABLE" in error_message:

                if attempt < 2:
                    time.sleep(3)
                    continue

            raise error