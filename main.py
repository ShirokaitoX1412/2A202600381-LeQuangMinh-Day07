from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
# Sửa đổi import để lấy tất cả các chunker cần thiết
from src.chunking import (
    FixedSizeChunker,
    RecursiveChunker,
    SentenceChunker,
)
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore

SAMPLE_FILES = [
    "data/chunking_experiment_report.md",
    "data/customer_support_playbook.txt",
    "data/python_intro.txt",
    "data/rag_system_design.md",
    "data/Tài liệu Bộ luật DS 2015.md",
    "data/vector_store_notes.md",
    "data/vi_retrieval_notes.md",
]


def load_documents_from_files(file_paths: list[str]) -> list[Document]:
    """Load documents from file paths for the manual demo."""
    allowed_extensions = {".md", ".txt"}
    documents: list[Document] = []

    for raw_path in file_paths:
        path = Path(raw_path)

        if path.suffix.lower() not in allowed_extensions:
            print(f"Skipping unsupported file type: {path} (allowed: .md, .txt)")
            continue

        if not path.exists() or not path.is_file():
            print(f"Skipping missing file: {path}")
            continue

        content = path.read_text(encoding="utf-8")
        documents.append(
            Document(
                id=path.stem,
                content=content,
                metadata={"source": str(path), "extension": path.suffix.lower()},
            )
        )

    return documents


def demo_llm(prompt: str) -> str:
    """A simple mock LLM for manual RAG testing."""
    preview = prompt[:400].replace("\n", " ")
    return f"[DEMO LLM] Generated answer from prompt preview: {preview}..."


def run_chunking_comparison(files: list[str]):
    """
    Chạy so sánh các chiến lược chunking bằng cách gọi thủ công từng chunker.
    """
    print("--- Chạy so sánh các chiến lược Chunking ---")
    target_file = "data/Tài liệu Bộ luật DS 2015.md"
    if target_file not in files:
        print(f"Tệp mục tiêu {target_file} không có trong danh sách tệp mẫu.")
        return

    print(f"Sử dụng tệp: {target_file}\n")
    try:
        text = Path(target_file).read_text(encoding="utf-8")
        print(f"Đã đọc được {len(text)} ký tự từ tệp.\n")
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy tệp {target_file}")
        return

    # --- Bỏ qua ChunkingStrategyComparator và chạy thủ công ---
    chunk_size = 1000
    strategies = {
        "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=50),
        "by_sentences": SentenceChunker(max_sentences_per_chunk=5),
        "recursive": RecursiveChunker(chunk_size=chunk_size),
    }

    results = {}
    for name, chunker in strategies.items():
        # Một số chunker có thể không có phương thức chunk, chúng ta sẽ bỏ qua nếu có lỗi
        try:
            chunks = chunker.chunk(text)
            results[name] = chunks
        except Exception as e:
            print(f"Lỗi khi chạy chiến lược '{name}': {e}")
            results[name] = []


    print("--- Kết quả so sánh Chunking ---")
    for strategy, chunks in results.items():
        if not chunks:
            print(f"\nChiến lược: {strategy}")
            print("  - Không tạo được chunk nào hoặc có lỗi.")
            continue

        num_chunks = len(chunks)
        chunk_lengths = [len(chunk) for chunk in chunks]
        avg_chunk_size = sum(chunk_lengths) / num_chunks
        min_chunk_size = min(chunk_lengths)
        max_chunk_size = max(chunk_lengths)

        print(f"\nChiến lược: {strategy}")
        print(f"  - Số lượng chunk: {num_chunks}")
        print(f"  - Kích thước chunk trung bình: {avg_chunk_size:.2f}")
        print(f"  - Kích thước chunk nhỏ nhất: {min_chunk_size}")
        print(f"  - Kích thước chunk lớn nhất: {max_chunk_size}")
    print("\n---------------------------------")


def run_manual_demo(question: str | None = None, sample_files: list[str] | None = None) -> int:
    files = sample_files or SAMPLE_FILES
    query = question or "BLDS 2015 quy định bao nhiêu biện pháp bảo đảm thực hiện nghĩa vụ và gồm những biện pháp nào?"

    print("=== Manual File Test ===")
    print("Accepted file types: .md, .txt")
    print("Input file list:")
    for file_path in files:
        print(f"  - {file_path}")

    docs = load_documents_from_files(files)
    if not docs:
        print("\nNo valid input files were loaded.")
        print("Create files matching the sample paths above, then rerun:")
        print("  python3 main.py")
        return 1

    print(f"\nLoaded {len(docs)} documents. Now chunking...")
    chunker = RecursiveChunker(chunk_size=1000)
    chunked_docs = []
    for doc in docs:
        chunks = chunker.chunk(doc.content)
        for i, chunk_content in enumerate(chunks):
            new_doc = Document(
                id=f"{doc.id}-chunk-{i}",
                content=chunk_content,
                metadata=doc.metadata.copy(),
            )
            chunked_docs.append(new_doc)

    print(f"Split into {len(chunked_docs)} total chunks.")

    load_dotenv(override=True)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            embedder = LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception as e:
            print(f"--- Failed to load LocalEmbedder, falling back to mock. Error: {e} ---")
            embedder = _mock_embed
    elif provider == "openai":
        try:
            embedder = OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception:
            embedder = _mock_embed
    else:
        embedder = _mock_embed

    print(f"\nEmbedding backend: {getattr(embedder, '_backend_name', embedder.__class__.__name__)}")

    store = EmbeddingStore(collection_name="manual_test_store", embedding_fn=embedder)
    store.add_documents(chunked_docs)

    print(f"\nStored {store.get_collection_size()} chunks in EmbeddingStore")
    print("\n=== EmbeddingStore Search Test ===")
    print(f"Query: {query}")
    search_results = store.search(query, top_k=3)
    for index, result in enumerate(search_results, start=1):
        print(f"{index}. score={result['score']:.3f} source={result['metadata'].get('source')}")
        print(f"   content preview: {result['content'][:120].replace(chr(10), ' ')}...")

    print("\n=== KnowledgeBaseAgent Test ===")
    agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)
    print(f"Question: {query}")
    print("Agent answer:")
    print(agent.answer(query, top_k=3))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Hệ thống RAG hoặc so sánh chunking.")
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Câu truy vấn để hỏi hệ thống RAG.",
    )
    parser.add_argument(
        "--compare-chunking",
        action="store_true",
        help="Chạy chế độ so sánh các chiến lược chunking thay vì RAG.",
    )
    args = parser.parse_args()

    if args.compare_chunking:
        run_chunking_comparison(SAMPLE_FILES)
        return 0

    return run_manual_demo(question=args.query, sample_files=SAMPLE_FILES)


if __name__ == "__main__":
    raise SystemExit(main())