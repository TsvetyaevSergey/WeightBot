# -*- coding: utf-8 -*-
import os
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).parent

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
