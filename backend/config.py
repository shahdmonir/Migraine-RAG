import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
PDF_FILENAME = os.getenv("PDF_FILENAME", "source.pdf")
SOURCE_LABEL = os.getenv("SOURCE_LABEL", "Source Document")
TOP_K = int(os.getenv("TOP_K", "5"))

PDF_PATH = DATA_DIR / PDF_FILENAME
COLLECTION_NAME = "medical_guideline"