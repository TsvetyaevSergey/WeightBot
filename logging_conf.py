# -*- coding: utf-8 -*-
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FILE = Path("bot.log")

def setup_logging(level=logging.INFO):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logger = logging.getLogger()
    logger.setLevel(level)

    # Консоль
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
    logger.addHandler(ch)

    # Ротация файла (до 5 файлов по 2 МБ)
    fh = RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
    logger.addHandler(fh)
