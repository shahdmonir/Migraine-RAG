import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"

# بنجمع كل مفاتيح الـ Gemini المتاحة في قايمة واحدة، ونتجاهل أي واحد فاضي
GEMINI_API_KEYS = [
    key for key in [
        os.getenv("GEMINI_API_KEY_1", ""),
        os.getenv("GEMINI_API_KEY_2", ""),
        os.getenv("GEMINI_API_KEY_3", ""),
    ] if key.strip()
]

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
PDF_FILENAME = os.getenv("PDF_FILENAME", "source.pdf")
SOURCE_LABEL = os.getenv("SOURCE_LABEL", "Source Document")
TOP_K = int(os.getenv("TOP_K", "5"))

PDF_PATH = DATA_DIR / PDF_FILENAME
COLLECTION_NAME = "medical_guideline"

# بنسمح بأي origin وقت التطوير، وبس الـ frontend المنشور وقت الإنتاج (production)
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")