import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
DB_PATH: str = os.getenv("DB_PATH", "data.db")
CHECK_INTERVAL_SEC: int = int(os.getenv("CHECK_INTERVAL_SEC", "120"))
MAX_NOTIFICATIONS_PER_CYCLE: int = int(os.getenv("MAX_NOTIFICATIONS_PER_CYCLE", "10"))
SS_LANG: str = os.getenv("SS_LANG", "ru").lower()

if SS_LANG not in ("ru", "lv"):
    SS_LANG = "ru"

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN не задан. Скопируй .env.example → .env")

MAX_FILTERS_PER_USER: int = int(os.getenv("MAX_FILTERS_PER_USER", "25"))
