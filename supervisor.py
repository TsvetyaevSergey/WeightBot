# -*- coding: utf-8 -*-
import subprocess
import time
import json
import logging
from pathlib import Path
import requests
from dotenv import load_dotenv
import os

from logging_conf import setup_logging

setup_logging()
log = logging.getLogger("supervisor")

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "data.json"

def get_sergeant_chat_id() -> int | None:
    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        s = data["users"].get("sergeant")
        tid = s.get("telegram_id") if s else None
        return int(tid) if tid else None
    except Exception as e:
        log.warning("Cannot read sergeant id: %s", e)
        return None

def notify_sergeant(text: str):
    chat_id = get_sergeant_chat_id()
    if not chat_id:
        log.warning("Sergeant chat_id unknown, skip notify")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": text})
        if resp.status_code != 200:
            log.warning("Notify failed: %s %s", resp.status_code, resp.text)
        else:
            log.info("Notify sent to sergeant")
    except Exception:
        log.exception("Notify request failed")

def run_bot_once() -> int:
    log.info("Launching bot.py")
    proc = subprocess.Popen(
        [str(BASE_DIR / ".venv" / "bin" / "python"), "bot.py"],
        stdout=open(BASE_DIR / "bot.out.log", "ab"),
        stderr=open(BASE_DIR / "bot.err.log", "ab"),
        cwd=str(BASE_DIR),
    )
    proc.wait()
    return proc.returncode

def main():
    backoff = 2
    max_backoff = 60

    while True:
        rc = run_bot_once()
        if rc == 0:
            log.info("bot.py exited normally (rc=0)")
            break

        # Падение
        log.error("bot.py crashed with rc=%s", rc)
        if not first_start:
            notify_sergeant("⚠️ Бот упал и перезапускается автоматически.")
        else:
            notify_sergeant("⚠️ Бот запускается.")
            # Если это первый старт после ребута — просто отметим
            log.info("First start cycle finished with crash (no notify)")
        first_start = False

        time.sleep(backoff)
        backoff = min(max_backoff, backoff * 2)  # экспоненциальная задержка

if __name__ == "__main__":
    main()
