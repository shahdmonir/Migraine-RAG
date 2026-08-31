"""
سكريبت الـ Ingestion.
بيشتغل مرة واحدة (أو كل ما تغيّري الـ PDF) عشان يجهز قاعدة البيانات الشعاعية.

طريقة التشغيل من التيرمينال جوه مجلد backend:
    python ingest.py
"""

import re
import sys
import shutil

from pypdf import PdfReader
import chromadb
from chromadb.utils import embedding_functions

import config


def extract_pages(pdf_path):
    """بترجع list من tuples (page_number, page_text) - رقم الصفحة يبدأ من 1"""
    if not pdf_path.exists():
        print(f"❌ الملف مش موجود: {pdf_path}")
        print("حطي ملف الـ PDF بتاعك في backend/data/ وسميه زي القيمة في PDF_FILENAME بملف .env")
        sys.exit(1)

    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            pages.append((i, text))
    return pages


def chunk_pages(pages, chunk_words=350, overlap_words=40):
    """
    بتقسم كل صفحة لـ chunks بحجم تقريبي chunk_words كلمة، مع overlap بسيط.
    كل chunk بيحتفظ برقم الصفحة اللي طلع منها.
    """
    chunks = []
    chunk_id = 0

    for page_num, text in pages:
        words = text.split(" ")
        start = 0
        while start < len(words):
            end = start + chunk_words
            piece_words = words[start:end]
            piece_text = " ".join(piece_words).strip()

            if piece_text:
                chunks.append(
                    {
                        "id": f"chunk_{chunk_id}",
                        "text": piece_text,
                        "page": page_num,
                    }
                )
                chunk_id += 1

            if end >= len(words):
                break
            start = end - overlap_words  # overlap

    return chunks


def build_vector_store(chunks):
    # لو فيه قاعدة بيانات قديمة، نمسحها ونبني واحدة جديدة نظيفة
    if config.CHROMA_DIR.exists():
        shutil.rmtree(config.CHROMA_DIR)
    config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))

    # embedding model مجاني وشغال محلي على الجهاز (من غير API key)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )

    collection = client.create_collection(
        name=config.COLLECTION_NAME,
        embedding_function=embed_fn,
    )

    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[{"page": c["page"]} for c in chunks],
    )

    return collection


def main():
    print("📄 بقرأ الملف وبستخرج النص...")
    pages = extract_pages(config.PDF_PATH)
    print(f"   لقيت {len(pages)} صفحة فيها نص.")

    print("✂️  بقسم النص لأجزاء (chunks)...")
    chunks = chunk_pages(pages)
    print(f"   طلع {len(chunks)} chunk.")

    print("🧠 بحوّل الأجزاء لأرقام (embeddings) وبخزنها... (ممكن تاخد دقيقة أول مرة)")
    build_vector_store(chunks)

    print("✅ خلصنا! قاعدة البيانات جاهزة في backend/chroma_db")


if __name__ == "__main__":
    main()
