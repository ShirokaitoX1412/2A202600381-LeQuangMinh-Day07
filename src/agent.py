from typing import Callable

from .store import EmbeddingStore

class KnowledgeBaseAgent:
    def __init__(self, store: EmbeddingStore, llm_fn: Callable = None):
        """
        Khởi tạo Agent với Store và hàm LLM.
        Lưu ý: Đổi tên tham số thành 'llm_fn' để khớp với main.py
        """
        self._store = store
        # Gán llm_fn vào một biến nội bộ để dùng trong hàm answer
        self._llm_fn = llm_fn

    def answer(self, query: str, top_k: int = 3) -> str:
        # Bước 1: Tìm kiếm context
        results = self._store.search(query, top_k=top_k)
        
        # Bước 2: Tạo context string
        context = "\n".join([r["content"] for r in results])
        
        # Bước 3: Gọi LLM thông qua self._llm_fn
        prompt = f"Context: {context}\n\nQuestion: {query}"
        
        if self._llm_fn:
            return self._llm_fn(prompt)
        return "No LLM function provided."