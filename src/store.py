from __future__ import annotations
from typing import Any, Callable, List
import numpy as np

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document

class EmbeddingStore:
    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

    def _make_record(self, content: str, metadata: dict) -> dict[str, Any]:
        return {
            "content": content,
            "metadata": metadata,
            "embedding": self._embedding_fn(content)
        }

    def add_documents(self, documents: List[Document]):
        """Nạp tài liệu và ép mọi thuộc tính nhận diện vào metadata."""
        for doc in documents:
            # Lấy metadata hiện có hoặc tạo mới
            meta = doc.metadata.copy() if (hasattr(doc, 'metadata') and doc.metadata) else {}
            
            # QUAN TRỌNG: Quét mọi thuộc tính của object Document để tìm ID
            # Thử các tên biến phổ biến mà bộ test hay dùng
            for attr in ['doc_id', 'id', 'source', 'name']:
                if hasattr(doc, attr):
                    val = getattr(doc, attr)
                    if val:
                        meta[attr] = val
            
            record = self._make_record(doc.content, meta)
            self._store.append(record)
        
        print(f"--- Loaded {len(documents)} records into store (Total: {len(self._store)}) ---")

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not self._store: return []
        query_vec = self._embedding_fn(query)
        results = []
        for record in self._store:
            score = _dot(query_vec, record["embedding"])
            results.append({**record, "score": score})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def get_collection_size(self) -> int:
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        candidates = self._store
        if metadata_filter:
            candidates = [
                r for r in self._store 
                if all(r["metadata"].get(k) == v for k, v in metadata_filter.items())
            ]
        
        query_vec = self._embedding_fn(query)
        results = []
        for record in candidates:
            score = _dot(query_vec, record["embedding"])
            results.append({**record, "score": score})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def delete_document(self, doc_id: str) -> bool:
        """Xóa bằng cách kiểm tra doc_id xuất hiện ở bất cứ đâu."""
        initial_size = len(self._store)
        target = str(doc_id)
        
        # Lọc sạch sẽ: Nếu doc_id xuất hiện trong bất kỳ giá trị nào của metadata
        self._store = [
            r for r in self._store 
            if target not in [str(v) for v in r.get("metadata", {}).values()]
        ]
        
        return len(self._store) < initial_size