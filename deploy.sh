#!/usr/bin/env bash
set -e

echo "[DEPLOY] Запуск деплоя WeightBot..."

# 1. Переходим в директорию скрипта
cd "$(dirname "$0")"

# 2. Проверка Python
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] Python3 не найден!"
    exit 1
fi

# 3. Создание виртуального окружения (если нет)
if [ ! -d ".venv" ]; then
    echo "[DEPLOY] Создаю виртуальное окружение..."
    python3 -m venv .venv
fi

# 4. Активация окружения
source .venv/bin/activate

# 5. Обновление pip и установка зависимостей
echo "[DEPLOY] Устанавливаю зависимости..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. Копирование .env.example в .env, если .env отсутствует
if [ ! -f ".env" ]; then
    echo "[DEPLOY] .env не найден, создаю из .env.example"
    cp .env.example .env
    echo "[DEPLOY] ⚠️ Не забудьте прописать реальный BOT_TOKEN в .env"
fi

# 7. Запуск бота в фоне
echo "[DEPLOY] Запускаю бота..."
nohup .venv/bin/python bot.py > bot.log 2>&1 &

# 8. Сохраняем PID
echo $! > bot.pid

echo "[DEPLOY] ✅ Бот запущен. PID=$(cat bot.pid)"
echo "[DEPLOY] Лог: tail -f bot.log"
