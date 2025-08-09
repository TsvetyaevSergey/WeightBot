#!/usr/bin/env bash
set -e

echo "[STOP] Остановка бота..."

cd "$(dirname "$0")"

if [ ! -f "bot.pid" ]; then
    echo "[STOP] Файл bot.pid не найден — бот, возможно, не запущен."
    exit 0
fi

PID=$(cat bot.pid)

if kill -0 "$PID" >/dev/null 2>&1; then
    kill "$PID"
    echo "[STOP] Процесс $PID остановлен."
else
    echo "[STOP] Процесс $PID не найден."
fi

rm -f bot.pid
