# -*- coding: utf-8 -*-
import os
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
# токен только из окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден. Укажите его в .env или переменных окружения.")

# часовой пояс: берём из TZ или по умолчанию МСК
TIMEZONE = ZoneInfo(os.getenv("TZ", "Europe/Moscow"))

USERS = {
    "semen": "Семён",
    "sergeant": "Сержант",
}

DATA_PATH = BASE_DIR / "data" / "data.json"
CHARTS_DIR = BASE_DIR / "charts"
BREAKFAST_FILE = DATA_DIR / "breakfast.json"
LUNCH_FILE     = DATA_DIR / "lunch.json"
DINNER_FILE    = DATA_DIR / "dinner.json"
SNACK1_FILE    = DATA_DIR / "snack1.json"   # NEW
SNACK2_FILE    = DATA_DIR / "snack2.json"   # NEW