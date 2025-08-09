#!/usr/bin/env bash
set -euo pipefail

echo "[STOP] Остановка WeightBot..."
cd "$(dirname "$0")"

if command -v systemctl >/dev/null 2>&1; then
  UNIT_NAME="weightbot@$(whoami).service"
  systemctl --user stop "$UNIT_NAME" || true
  systemctl --user disable "$UNIT_NAME" || true
  systemctl --user daemon-reload
  echo "[STOP] Остановлен systemd unit $UNIT_NAME"
fi

if [ -f "supervisor.pid" ]; then
  PID="$(cat supervisor.pid || true)"
  if [ -n "${PID}" ] && kill -0 "$PID" >/dev/null 2>&1; then
    kill "$PID" || true
    echo "[STOP] Supervisor процесс $PID остановлен."
  fi
  rm -f supervisor.pid
fi

# про запас — гасим старые bot.py, если вдруг остались
pkill -f "python .*bot.py" >/dev/null 2>&1 || true
echo "[STOP] Done."
