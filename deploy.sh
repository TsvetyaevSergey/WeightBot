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

# --- SYSTEMD (опционально, но рекомендуется) ---
if command -v systemctl >/dev/null 2>&1; then
  echo "[DEPLOY] Настраиваю systemd unit..."
  UNIT_NAME="weightbot@$(whoami).service"
  # копируем юнит в ~/.config/systemd/user/
  mkdir -p ~/.config/systemd/user
  cp weightbot.service ~/.config/systemd/user/weightbot@.service

  systemctl --user daemon-reload
  systemctl --user enable "$UNIT_NAME"
  systemctl --user restart "$UNIT_NAME"

  echo "[DEPLOY] ✅ systemd unit запущен: $UNIT_NAME"
  echo "[DEPLOY] Подсказка: journalctl --user -u $UNIT_NAME -f"
else
  echo "[DEPLOY] systemd не найден — запускаю supervisor в фоне через nohup"
  nohup .venv/bin/python supervisor.py >> supervisor.log 2>&1 &
  echo $! > supervisor.pid
  echo "[DEPLOY] ✅ Supervisor запущен в фоне (PID=$(cat supervisor.pid))"
fi

