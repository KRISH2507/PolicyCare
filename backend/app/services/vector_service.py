import chromadb
from chromadb.config import Settings as ChromaSettings
from openai import OpenAI
from typing import List, Dict, Optional
import os

from app.core.config import settings

# Initialize persistent OpenAI Text Embedding client 
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Verify Chroma directory path exists
os.makedirs(settings.CHROMA_PATH, exist_ok=True)

# Initialize production persistent VectorDB via native python local runtime
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PATH)

# Instantiate the single collection with explicit standard Cosine Space parameters
collection = chroma_client.get_or_create_collection(
    name="policies",
    metadata={"hnsw:space": "cosine"}
)

def init_vector_db() -> int:
    """Warmup check and diagnostic wrapper returning total indexed count."""
    return collection.count()

def embed_texts(text_list: List[str]) -> List[List[float]]:
    """Native pass via OpenAI SDK 'text-embedding-3-small' models"""
    if not text_list:
        return []
        
    try:
        response = openai_client.embeddings.create(
            input=text_list,
            model="text-embedding-3-small",
            encoding_format="float"
        )
        return [data.embedding for data in response.data]
    except Exception as e:
        raise ConnectionError(f"Embedding API failed: {str(e)}")

def store_policy_chunks(policy_id: int, policy_name: str, insurer: str, chunks: List[Dict]):
    """
    Parses and serializes chunk dictionaries into parallel lists (Chroma struct style)
    and pushes to database implicitly generating vector embeddings.
    """
    if not chunks:
        return

    # Extract target strings to be vectorized
    texts = [c["text"] for c in chunks]
    
    # Fire 1 batch call up to OpenAI endpoints
    embeddings = embed_texts(texts)
    
    # Forge highly guaranteed unique IDs per chunk
    ids = [f"policy_{policy_id}_page_{c['page_number']}_chunk_{c['chunk_index']}" for c in chunks]
    
    # Pass SQL mapping metadata allowing fast categorical pre-filtering locally
    metadatas = [
        {
            "policy_id": str(policy_id), # Chroma requires strings/ints
            "policy_name": policy_name,
            "insurer": insurer,
            "page_number": c["page_number"],
            "chunk_index": c["chunk_index"]
        }
        for c in chunks
    ]
    
    collection.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=texts
    )

def delete_policy_vectors(policy_id: int):
    """Purges any and all nested chunks matching a strict subset string explicitly."""
    try:
        collection.delete(where={"policy_id": str(policy_id)})
    except Exception as e:
        pass # Optional to pass depending on strict enforcement level of empty docs

def search_policy_chunks(query: str, top_k: int = 5, policy_ids: Optional[List[int]] = None) -> List[Dict]:
    """
    Given a raw string logic prompt, search embeddings comparing distance logic.
    Optionally filter by standard policy_id bounds using 'where'.
    """
    try:
        query_embedding = embed_texts([query])[0]
    except Exception:
        return []
        
    # Chroma accepts complex JSON conditions
    where_clause = None
    if policy_ids:
        if len(policy_ids) == 1:
            where_clause = {"policy_id": str(policy_ids[0])}
        else:
            where_clause = {"policy_id": {"$in": [str(pid) for pid in policy_ids]}}
            
    try: 
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
    except Exception:
        return []
        
    # Parsing into an easily handled frontend/dict wrapper
    parsed_results = []
    if results.get("documents") and len(results["documents"]) > 0 and len(results["documents"][0]) > 0:
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]
        
        for i in range(len(docs)):
            parsed_results.append({
                "document": docs[i],
                "metadata": metas[i],
                "distance": dists[i]
            })
            
    return parsed_results