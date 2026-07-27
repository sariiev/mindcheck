import chromadb
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = chromadb.HttpClient(
    host=os.getenv("CHROMA_HOST"),
    port=int(os.getenv("CHROMA_PORT"))
)

embedding_client = OpenAI(api_key=os.getenv("LLM_API_KEY"))

def embed(text: str) -> list[float]:
    response = embedding_client.embeddings.create(
        model=os.getenv("OPENAI_EMBEDDING_MODEL"),
        input=text
    )
    return response.data[0].embedding

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

def get_collection(project_id: str) -> None:
    return client.get_or_create_collection(
        name=f"project_{project_id}",
        metadata={"hnsw:space": "cosine"}
    )

def delete_collection(project_id: str) -> None:
    try:
        client.delete_collection(f"project_{project_id}")
    except Exception:
        pass

def add_document(project_id: str, material_id: str, text: str) -> None:
    collection = get_collection(project_id)
    chunks = chunk_text(text)

    for i, chunk in enumerate(chunks):
        embedding = embed(chunk)
        collection.add(
            ids=[f"{material_id}_{i}"],
            embeddings=[embedding],
            documents=[chunk],
            metadatas=[{"project_id": project_id, "material_id": material_id}]
        )

def delete_document(project_id: str, material_id: str) -> None:
    collection = get_collection(project_id)
    collection.delete(where={"material_id": material_id})

def search_chunks(project_id: str, query: str, n_results: int = 3) -> list[str]:
    collection = get_collection(project_id)
    query_embedding = embed(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    return results["documents"][0]