# -*- coding: utf-8 -*-
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
from config import USERS

def registration_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"Зарегистрироваться как {title}", callback_data=f"register:{key}")]
        for key, title in USERS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Внести вес")],
            [KeyboardButton(text="📈 Показать результаты")],
            [KeyboardButton(text="✏️ Исправить последние записи")],
            [KeyboardButton(text="🍽 Что мне поесть сегодня?")]# NEW
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие…",
    )


def edit_choose_kb(entries: list) -> InlineKeyboardMarkup:
    rows = []
    for idx, rec in entries:
        # форматируем дату в ДД.ММ.ГГГГ
        dt_str = datetime.fromisoformat(rec["date"]).strftime("%d.%m.%Y")
        text = f"{dt_str} — {rec['weight']} кг"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"editpick:{idx}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


