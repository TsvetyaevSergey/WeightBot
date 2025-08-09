# -*- coding: utf-8 -*-
import json
from pathlib import Path
from datetime import date
from typing import Dict, List, Optional, Tuple

from config import DATA_PATH, USERS

class Storage:
    """
    JSON-хранилище.
    """
    def __init__(self, path: Path = Path(DATA_PATH)):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._init_file()

    def _init_file(self):
        data = {
            "users": {k: {"telegram_id": None, "name": v} for k, v in USERS.items()},
            "weights": [],
            "start_date": date.today().isoformat(),
        }
        self._write(data)

    def _read(self) -> dict:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict):
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # --- Пользователи ---
    def is_registered(self, tg_id: int) -> bool:
        data = self._read()
        return any(u.get("telegram_id") == tg_id for u in data["users"].values())

    def get_user_key_by_tg(self, tg_id: int) -> Optional[str]:
        data = self._read()
        for key, u in data["users"].items():
            if u.get("telegram_id") == tg_id:
                return key
        return None

    def register(self, user_key: str, tg_id: int) -> Tuple[bool, str]:
        if user_key not in USERS:
            return False, "Неизвестная роль."
        data = self._read()
        current_id = data["users"][user_key].get("telegram_id")
        if current_id and current_id != tg_id:
            return False, f"Роль «{USERS[user_key]}» уже занята."
        existing_key = self.get_user_key_by_tg(tg_id)
        if existing_key and existing_key != user_key:
            return False, f"Вы уже зарегистрированы как «{USERS[existing_key]}»."
        data["users"][user_key]["telegram_id"] = tg_id
        data["users"][user_key]["name"] = USERS[user_key]
        self._write(data)
        return True, f"Успех! Вы зарегистрированы как «{USERS[user_key]}»."

    def get_registered_users(self) -> Dict[str, Dict]:
        data = self._read()
        return {k: v for k, v in data["users"].items() if v.get("telegram_id")}

    # --- Вес ---
    def add_weight(self, user_key: str, weight: float, on_date: Optional[str] = None) -> Tuple[bool, str]:
        """
        Добавляет запись веса. Блокирует повторную запись в тот же день.
        Возвращает (успех, сообщение).
        """
        data = self._read()
        on_date = on_date or date.today().isoformat()

        # Запрет: только 1 запись в день
        if any(w["user_key"] == user_key and w["date"] == on_date for w in data["weights"]):
            return False, "На сегодня запись уже есть. Разрешена только одна запись в день."

        data["weights"].append({
            "user_key": user_key,
            "date": on_date,
            "weight": float(weight),
        })
        self._write(data)
        return True, "Записал! ✅"

    def get_all_weights(self) -> List[dict]:
        data = self._read()
        return data["weights"]

    def get_start_date(self) -> str:
        data = self._read()
        return data["start_date"]

    def get_user_series(self, user_key: str) -> List[dict]:
        return [w for w in self.get_all_weights() if w["user_key"] == user_key]

    # --- Редактирование последних записей ---
    def get_user_last_entries(self, user_key: str, n: int = 4) -> List[Tuple[int, dict]]:
        """
        Возвращает последние n записей пользователя как список (индекс_в_массиве, запись),
        где индекс — позиция в общем списке weights (для последующего обновления).
        """
        data = self._read()
        enumerated = [(i, w) for i, w in enumerate(data["weights"]) if w["user_key"] == user_key]
        enumerated.sort(key=lambda t: t[1]["date"])  # по дате
        return list(reversed(enumerated))[:n]

    def update_weight_by_index(self, global_index: int, new_weight: float) -> None:
        data = self._read()
        if 0 <= global_index < len(data["weights"]):
            data["weights"][global_index]["weight"] = float(new_weight)
            self._write(data)

    def get_day_entry(self, user_key: str, day_iso: str) -> Optional[Tuple[int, dict]]:
        """Найти запись конкретного дня и вернуть (глобальный_индекс, запись) или None."""
        data = self._read()
        for i, w in enumerate(data["weights"]):
            if w["user_key"] == user_key and w["date"] == day_iso:
                return i, w
        return None
