from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        # Đảm bảo bước nhảy luôn dương để tránh lặp vô tận
        if step <= 0:
            step = 1
            
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
            
        # Regex tách câu: kết thúc bằng . ! ? theo sau là khoảng trắng hoặc xuống dòng
        sentences = re.split(r'(?<=[.!?])(?:\s+|\n)', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk = " ".join(sentences[i : i + self.max_sentences_per_chunk])
            if chunk:
                chunks.append(chunk)
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Nếu đoạn text đã đủ nhỏ, trả về luôn
        if len(current_text) <= self.chunk_size:
            return [current_text]
        
        # Nếu hết separator, cắt cứng theo chunk_size
        if not remaining_separators:
            return [current_text[i:i+self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        sep = remaining_separators[0]
        new_remaining = remaining_separators[1:]

        if sep == "" or sep not in current_text:
            return self._split(current_text, new_remaining)

        # Tách theo separator hiện tại
        final_chunks = []
        parts = current_text.split(sep)
        
        # Xử lý từng phần sau khi tách
        for i, part in enumerate(parts):
            if not part and i < len(parts) - 1: # Giữ lại các cấu trúc xuống dòng trống nếu cần
                continue
            
            if len(part) <= self.chunk_size:
                if part.strip():
                    final_chunks.append(part.strip())
            else:
                # Đệ quy sâu hơn với các separator còn lại
                final_chunks.extend(self._split(part, new_remaining))
                
        return final_chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.
    """
    if not vec_a or not vec_b:
        return 0.0
        
    dot_product = _dot(vec_a, vec_b)
    
    # Tính Magnitude (L2 norm)
    norm_a = math.sqrt(sum(x**2 for x in vec_a))
    norm_b = math.sqrt(sum(x**2 for x in vec_b))
    
    # Tránh chia cho 0 nếu một trong hai vector là vector không
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    return dot_product / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
            strategies = {
                "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0),
                "by_sentences": SentenceChunker(max_sentences_per_chunk=2), # Đổi 'sentence' thành 'by_sentences'
                "recursive": RecursiveChunker(chunk_size=chunk_size)
            }
            
            results = {}
            for name, chunker in strategies.items():
                chunks = chunker.chunk(text)
                results[name] = {
                    "count": len(chunks),
                    "avg_length": float(sum(len(c) for c in chunks) / len(chunks)) if chunks else 0.0,
                    "chunks": chunks
                }
            return results