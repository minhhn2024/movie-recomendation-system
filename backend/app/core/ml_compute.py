from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Optional, List, Dict
import faiss
from surprise.prediction_algorithms.matrix_factorization import SVD

from app import constants


def get_embedding(text: Optional[str], model: SentenceTransformer, dim: int = 384) -> np.ndarray:
    if text is None or not isinstance(text, str) or not text.strip():
        return np.zeros(dim)

    embedding = model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0]

    if len(embedding) != dim:
        raise ValueError(f"Embedding dimension ({len(embedding)}) does not match expected ({dim})")

    return embedding


def multi_search_faiss_index(
    query_emb: np.ndarray,
    index_dict: Dict[str, faiss.Index],
    faiss_to_movie: Dict[int, int],
    k: int = 10,

) -> List[Dict[str, float | int | str]]:

    results = []
    query_emb = query_emb.reshape(1, -1)
    for index_name, index in index_dict.items():
        distances, indices = index.search(query_emb, k)
        for dist, idx in zip(distances[0], indices[0]):
            results.append({
                "type": index_name,
                "distance": float(dist),
                "index": idx,
                "movieId": faiss_to_movie[idx]
            })

    return results


def search_by_faiss_index(
    vectors: Dict[str, np.ndarray],
    index_dict: Dict[str, faiss.Index],
    faiss_to_movie: Dict[int, int],
    k: int = 10,
) -> List[Dict[str, float | int | str]]:

    results = []
    for index_name, index in index_dict.items():

        embedding_vector = np.zeros(constants.EmbeddingModelConstants.VECTOR_EMBEDDING_DIM)
        if (index_name == "content"):
            embedding_vector = vectors["content_vector"].reshape(1, -1)
        elif (index_name == "title"):
            embedding_vector = vectors["title_vector"].reshape(1, -1)
        elif (index_name == "type"):
            embedding_vector = vectors["type_vector"].reshape(1, -1)
        elif (index_name == "people"):
            embedding_vector = vectors["people_vector"].reshape(1, -1)
        else:
            raise ValueError(f"Invalid index name: {index_name}")

        distances, indices = index.search(embedding_vector, k)
        for dist, idx in zip(distances[0], indices[0]):
            results.append({
                "type": index_name,
                "distance": float(dist),
                "index": idx,
                "movieId": faiss_to_movie[idx]
            })

    return results