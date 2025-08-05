import faiss
import numpy as np
import os
import pickle
from langchain.embeddings import HuggingFaceEmbeddings


async def get_relevant_chunks(user_id: str, question: str):
    
    
    index_path = f"{user_id}.faiss"
    chunks_path = f"{user_id}.pkl"
    try:
        chunks = await retrieve_chunks(
            query=question,
            index_path=index_path,
            chunks_path=chunks_path,
            top_k=9
        )
        return chunks
    except Exception as e:
        return f"Error loading index or chunks: {str(e)}"
async def retrieve_chunks(
    query,
    origin="faiss_indecies",
    index_path="index.faiss",
    chunks_path="chunk_lookup.pkl",
    model="text-embedding-3-small",
    top_k=9
):
    
    retrieved = []
    try:
        index_file = os.path.join(origin, index_path)
        chunks_file = os.path.join(origin, chunks_path)
        print(index_file, chunks_file)

        # Load or create index and chunks
        if os.path.exists(index_file) and os.path.exists(chunks_file):
            print("✅ Loading FAISS index and chunks from disk...")
            index = faiss.read_index(index_file)
            with open(chunks_file, "rb") as f:
                chunks_metadata = pickle.load(f)
                chunks = [chunk.page_content for chunk in chunks_metadata]
        else:
            print("⚠️ Index not found. Please Make Sure You have Index...")
            return []
        # Embed the query
        embeddings_model = HuggingFaceEmbeddings()
        query_vec = embeddings_model.embed_documents([query])
        query_vec = np.array([query_vec]).reshape(1, -1)
        # Search
        D, I = index.search(query_vec, top_k)
        retrieved = [chunks[i] for i in I[0] if i < len(chunks)]
        return retrieved

    except FileNotFoundError as fnf_err:
        print(f"❌ File error: {fnf_err}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    return []  # Return empty list on failure