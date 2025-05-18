from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

# Initialize the embedding model
embedding_model = SentenceTransformer("FinLang/finance-embeddings-investopedia")

def get_embedding(text_list: List[str], model: SentenceTransformer = embedding_model) -> np.ndarray:
    """Generates embeddings for a list of texts."""
    embeddings = model.encode(text_list, convert_to_numpy=True)
    return embeddings

def similarity_score(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """Calculates cosine similarity between two single embeddings."""
    return (embedding1*embedding2).sum()
