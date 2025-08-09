#!/usr/bin/env bash
set -euo pipefail

echo "[DEPLOY] Deploy WeightBot..."
cd "$(dirname "$0")"

PY313_BIN="python3.13"
VENV_DIR=".venv"
VENV_PY="$VENV_DIR/bin/python"

have_cmd() { command -v "$1" >/dev/null 2>&1; }

ensure_python313_apt() {
  # Установка через deadsnakes (Ubuntu/Debian)
  if ! have_cmd apt-get; then
    return 1
  fi
  echo "[DEPLOY] Trying to install Python 3.13 via apt (deadsnakes)..."
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y software-properties-common curl git build-essential
  add-apt-repository -y ppa:deadsnakes/ppa || true
  apt-get update -y
  apt-get install -y python3.13 python3.13-venv
  have_cmd "$PY313_BIN"
}

ensure_python313_pyenv() {
  # Фоллбэк через pyenv (ставим в ~/.pyenv)
  echo "[DEPLOY] Installing Python 3.13 via pyenv (fallback)..."
  # deps для сборки CPython (Ubuntu/Debian)
  if have_cmd apt-get; then
    apt-get update -y
    apt-get install -y make build-essential \
      libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
      wget curl llvm libncursesw5-dev xz-utils tk-dev libxml2-dev \
      libxmlsec1-dev libffi-dev liblzma-dev git
  fi
  if [ ! -d "${HOME}/.pyenv" ]; then
    git clone https://github.com/pyenv/pyenv.git "${HOME}/.pyenv"
  fi
  export PYENV_ROOT="${HOME}/.pyenv"
  export PATH="${PYENV_ROOT}/bin:${PATH}"
  eval "$(pyenv init -)"
  # ставим 3.13.x (можешь поменять патч-версию при желании)
  pyenv install -s 3.13.1
  pyenv local 3.13.1 || true
  # создадим симлинк-шим в локальный bin, чтобы был python3.13
  mkdir -p ./bin
  ln -sf "${PYENV_ROOT}/versions/3.13.1/bin/python3.13" ./bin/python3.13
  export PATH="$(pwd)/bin:${PATH}"
  have_cmd "$PY313_BIN"
}

ensure_python313() {
  if have_cmd "$PY313_BIN"; then
    echo "[DEPLOY] Found $( $PY313_BIN -V )"
    return 0
  fi
  # пробуем через apt
  if ensure_python313_apt; then
    echo "[DEPLOY] Installed $( $PY313_BIN -V ) via apt"
    return 0
  fi
  # fallback pyenv
  if ensure_python313_pyenv; then
    echo "[DEPLOY] Installed $( $PY313_BIN -V ) via pyenv"
    return 0
  fi
  echo "[ERROR] Cannot install Python 3.13 automatically. Install it manually and retry."
  exit 1
}

ensure_python313

# --- VENV строго на 3.13 ---
if [ ! -d "$VENV_DIR" ]; then
  echo "[DEPLOY] Creating venv with python3.13 ..."
  "$PY313_BIN" -m venv "$VENV_DIR"
fi

if [ ! -x "$VENV_PY" ]; then
  echo "[ERROR] $VENV_PY not found or not executable."
  exit 1
fi

echo "[DEPLOY] Using interpreter: $( $VENV_PY -V )"

# --- Зависимости ---
echo "[DEPLOY] Installing requirements..."
"$VENV_PY" -m pip install --upgrade pip
"$VENV_PY" -m pip install -r requirements.txt

# --- .env ---
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo "[DEPLOY] Created .env from .env.example. ⚠️ Put real BOT_TOKEN in .env"
  else
    echo "[DEPLOY] ⚠️ .env not found and .env.example missing — create .env manually."
  fi
fi

# --- Останавливаем старый фоновый запуск (если был) ---
if [ -f "supervisor.pid" ]; then
  OLD_PID="$(cat supervisor.pid || true)"
  if [ -n "${OLD_PID}" ] && kill -0 "$OLD_PID" >/dev/null 2>&1; then
    echo "[DEPLOY] Stopping previous supervisor (PID=$OLD_PID)..."
    kill "$OLD_PID" || true
    sleep 1
  fi
  rm -f supervisor.pid
fi

if [ -f "bot.pid" ]; then
  OLD_PID="$(cat bot.pid || true)"
  if [ -n "${OLD_PID}" ] && kill -0 "$OLD_PID" >/dev/null 2>&1; then
    echo "[DEPLOY] Stopping previous bot (PID=$OLD_PID)..."
    kill "$OLD_PID" || true
    sleep 1
  fi
  rm -f bot.pid
fi

# --- Запуск supervisor (если есть), иначе напрямую bot.py ---
if [ -f "supervisor.py" ]; then
  echo "[DEPLOY] Launching supervisor.py in background..."
  nohup "$VENV_PY" supervisor.py >> supervisor.log 2>&1 &
  echo $! > supervisor.pid
  echo "[DEPLOY] ✅ Supervisor started. PID=$(cat supervisor.pid)"
  echo "[DEPLOY] Logs: tail -f supervisor.log bot.log"
else
  echo "[DEPLOY] Launching bot.py in background..."
  nohup "$VENV_PY" bot.py > bot.log 2>&1 &
  echo $! > bot.pid
  echo "[DEPLOY] ✅ Bot started. PID=$(cat bot.pid)"
  echo "[DEPLOY] Logs: tail -f bot.log"
fi
