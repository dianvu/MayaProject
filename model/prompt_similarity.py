from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

# Initialize the embedding model
# embedding_model = SentenceTransformer("FinLang/finance-embeddings-investopedia")
embedding_model = SentenceTransformer("sentence-transformers/multi-qa-mpnet-base-dot-v1")

def get_embedding(text_list: List[str], model: SentenceTransformer = embedding_model) -> np.ndarray:
    """Generates embeddings for a list of texts."""
    embeddings = model.encode(text_list, convert_to_numpy=True)
    return embeddings

def similarity_score(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """Calculates cosine similarity between two single embeddings."""
    dot_product = (embedding1 * embedding2).sum()
    norm1 = np.sqrt((embedding1 * embedding1).sum())
    norm2 = np.sqrt((embedding2 * embedding2).sum())
    return dot_product / (norm1 * norm2)
