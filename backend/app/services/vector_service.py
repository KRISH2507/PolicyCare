import os
import logging
from typing import List, Dict, Optional

import chromadb
import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)

os.makedirs(settings.CHROMA_PATH, exist_ok=True)
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
collection = chroma_client.get_or_create_collection(
    name="policies",
    metadata={"hnsw:space": "cosine"},
)


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=texts,
        task_type="retrieval_document",
    )
    embeddings = result["embedding"]
    return [embeddings] if isinstance(embeddings[0], float) else embeddings


def embed_query(text: str) -> List[float]:
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_query",
    )
    return result["embedding"]


def store_policy_chunks(policy_id: int, policy_name: str, insurer: str, chunks: List[Dict]):
    if not chunks:
        return
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)
    collection.add(
        ids=[f"policy_{policy_id}_page_{c['page_number']}_chunk_{c['chunk_index']}" for c in chunks],
        embeddings=embeddings,
        metadatas=[{
            "policy_id": str(policy_id),
            "policy_name": policy_name,
            "insurer": insurer,
            "page_number": c["page_number"],
            "chunk_index": c["chunk_index"],
        } for c in chunks],
        documents=texts,
    )


def delete_policy_vectors(policy_id: int):
    try:
        collection.delete(where={"policy_id": str(policy_id)})
    except Exception:
        pass


def search_policy_chunks(query: str, top_k: int = 5, policy_ids: Optional[List[int]] = None) -> List[Dict]:
    try:
        query_embedding = embed_query(query)
    except Exception as e:
        logger.error("Embedding query failed: %s", e)
        return []

    where_clause = None
    if policy_ids:
        where_clause = (
            {"policy_id": str(policy_ids[0])} if len(policy_ids) == 1
            else {"policy_id": {"$in": [str(p) for p in policy_ids]}}
        )

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        logger.error("ChromaDB query failed: %s", e)
        return []

    if not results.get("documents") or not results["documents"][0]:
        return []

    return [
        {"document": doc, "metadata": meta, "distance": dist}
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]
