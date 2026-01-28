import numpy as np
import faiss
import threading
import pickle
from typing import List, Dict, Optional
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer

class HFEmbedding():
    def __init__(self, model_name: Optional[str]="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def get_dim(self):
        return self.dim

    def embed(self, texts: List[str]) -> np.ndarray:
        return np.array(self.model.encode(texts, normalize_embeddings=True))

@dataclass
class VectorRecord:
    text: str
    metadata: Optional[Dict] = None

class VectorStore:
    def __init__(self, embedding_fn, dim: int, index_factory: str = "Flat", persist_path: str = "vector_store"):
        self.embedding_fn = embedding_fn
        self.dim = dim
        self.index = faiss.index_factory(dim, index_factory)
        self.records: List[VectorRecord] = []
        self.lock = threading.Lock()
        self.persist_path = persist_path
        self.load()

    def add(self, text: str, metadata: Optional[Dict] = None) -> None:
        if not text:
            return

        embedding = self.embedding_fn.embed([text])
        if embedding.shape[1] != self.dim:
            raise ValueError("Embedding dimension mismatch")

        with self.lock:
            self.index.add(embedding.astype("float32"))
            self.records.append(VectorRecord(text=text, metadata=metadata))
        
        self.save()

    def search(self, query: str, k: int = 5, score_threshold: Optional[float] = None) -> List[str]:
        if not query or self.index.ntotal == 0:
            return []

        query_emb = self.embedding_fn.embed([query]).astype("float32")

        with self.lock:
            distances, indices = self.index.search(query_emb, k)

        results = []
        for idx, score in zip(indices[0], distances[0]):
            if idx == -1:
                continue
            if score_threshold is not None and score > score_threshold:
                continue
            results.append(self.records[idx].text)

        return results
    
    def save(self) -> None:
        """Save index and records to disk"""
        with self.lock:
            faiss.write_index(self.index, f"{self.persist_path}.index")
            with open(f"{self.persist_path}.pkl", "wb") as f:
                pickle.dump(self.records, f)

    def load(self) -> None:
        """Load index and records from disk if they exist"""
        import os
        if os.path.exists(f"{self.persist_path}.index"):
            with self.lock:
                self.index = faiss.read_index(f"{self.persist_path}.index")
                with open(f"{self.persist_path}.pkl", "rb") as f:
                    self.records = pickle.load(f)
                print(f"Loaded vector store from disk: {len(self.records)} records")
    
    def clear(self) -> None:
        with self.lock:
            self.index.reset()
            self.records.clear()
        self.save()

    def size(self) -> int:
        return self.index.ntotal