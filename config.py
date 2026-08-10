import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi! .env faylini tekshiring (config.py).")

_admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in _admin_ids_raw.split(",") if x.strip()]
if not ADMIN_IDS:
    raise RuntimeError("ADMIN_IDS topilmadi! .env faylida kamida bitta admin ID kiriting.")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "storage", "database.db")
ARTICLES_DIR = os.path.join(BASE_DIR, "storage", "articles")
MEDIA_DIR = os.path.join(BASE_DIR, "media")
INTRO_VIDEO_PATH = os.path.join(MEDIA_DIR, "intro.mp4")

# Xavfsizlik / cheklovlar
MAX_FILE_SIZE_MB = 20
ALLOWED_EXTENSIONS = (".doc", ".docx", ".pdf")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(ARTICLES_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)
