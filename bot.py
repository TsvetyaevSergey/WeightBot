# -*- coding: utf-8 -*-
from dotenv import load_dotenv
load_dotenv()
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from datetime import datetime
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, USERS, TIMEZONE
from keyboards import registration_kb, main_menu_kb, edit_choose_kb
from storage import Storage
from charts import build_weight_chart
from scheduler import setup_scheduler


# --- FSM для ввода веса ---
class WeightForm(StatesGroup):
    waiting_for_weight = State()
    editing_wait_value = State()   # NEW


storage = Storage()

async def on_startup(bot: Bot):
    setup_scheduler(bot, storage)

# --- Хэндлеры ---
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    if storage.is_registered(message.from_user.id):
        user_key = storage.get_user_key_by_tg(message.from_user.id)
        name = USERS.get(user_key, "Участник")
        await message.answer(
            f"Привет, {name}! 👋\nГотов к замерам?",
            reply_markup=main_menu_kb()
        )
    else:
        await message.answer(
            "Этот бот — для дуэли по снижению веса между Семёном и Сержантом.\n"
            "Выберите, кем вы являетесь для регистрации:",
            reply_markup=registration_kb()
        )

async def register_cb(call: CallbackQuery):
    await call.answer()
    if not call.data or ":" not in call.data:
        return
    _, user_key = call.data.split(":", 1)
    ok, msg = storage.register(user_key=user_key, tg_id=call.from_user.id)
    if ok:
        await call.message.edit_text(msg)
        await call.message.answer("Главное меню:", reply_markup=main_menu_kb())
    else:
        await call.message.answer(f"❗ {msg}")

async def add_weight_entry(message: Message, state: FSMContext):
    if not storage.is_registered(message.from_user.id):
        await message.answer("Сначала зарегистрируйтесь: /start")
        return
    await state.set_state(WeightForm.waiting_for_weight)
    await message.answer("Введите вес в кг (например, 82.4):")

async def weight_input(message: Message, state: FSMContext):
    # вычисляем "сегодня" по МСК
    today_msk = datetime.now(TIMEZONE).date().isoformat()

    text = (message.text or "").replace(",", ".").strip()
    try:
        value = float(text)
        if value <= 0 or value > 500:
            raise ValueError
    except ValueError:
        await message.answer("Некорректное число. Пример: 82.4")
        return

    user_key = storage.get_user_key_by_tg(message.from_user.id)

    ok, msg = storage.add_weight(user_key, value, on_date=today_msk)
    if not ok:
        await message.answer(f"❗ {msg}\nЕсли опечатались — используйте «✏️ Исправить последние записи».")
        return

    await state.clear()
    await message.answer(msg, reply_markup=main_menu_kb())


async def show_results(message: Message):
    if not storage.is_registered(message.from_user.id):
        await message.answer("Сначала зарегистрируйтесь: /start")
        return

    img_path = build_weight_chart(storage.get_all_weights(), storage.get_start_date())
    await message.answer_photo(
        photo=FSInputFile(img_path),
        caption="Ваши результаты 📈"
    )

# --- Быстрая команда /weight 82.4 ---
async def weight_cmd(message: Message, state: FSMContext):
    if not storage.is_registered(message.from_user.id):
        await message.answer("Сначала зарегистрируйтесь: /start")
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Использование: /weight 82.4")
        return

    text = parts[1].replace(",", ".").strip()
    try:
        value = float(text)
        if value <= 0 or value > 500:
            raise ValueError
    except ValueError:
        await message.answer("Некорректное число. Пример: 82.4")
        return

    today_msk = datetime.now(TIMEZONE).date().isoformat()
    user_key = storage.get_user_key_by_tg(message.from_user.id)
    ok, msg = storage.add_weight(user_key, value, on_date=today_msk)
    if not ok:
        await message.answer(f"❗ {msg}\nЕсли опечатались — используйте «✏️ Исправить последние записи».")
        return

    await state.clear()
    await message.answer(msg, reply_markup=main_menu_kb())

async def open_edit_menu(message: Message, state: FSMContext):
    if not storage.is_registered(message.from_user.id):
        await message.answer("Сначала зарегистрируйтесь: /start")
        return
    user_key = storage.get_user_key_by_tg(message.from_user.id)
    last_entries = storage.get_user_last_entries(user_key, n=4)
    if not last_entries:
        await message.answer("У вас пока нет записей для редактирования.")
        return
    await message.answer(
        "Выберите запись для исправления (последние 4):",
        reply_markup=edit_choose_kb(last_entries)
    )

async def edit_pick_cb(call: CallbackQuery, state: FSMContext):
    await call.answer()
    if not call.data or ":" not in call.data:
        return
    _, idx_str = call.data.split(":", 1)
    try:
        global_index = int(idx_str)
    except ValueError:
        return
    # Запомним, какую запись редактируем
    await state.update_data(edit_global_index=global_index)
    await state.set_state(WeightForm.editing_wait_value)
    await call.message.answer("Введите новое значение веса (кг), например 82.1:")

async def edit_apply_value(message: Message, state: FSMContext):
    text = (message.text or "").replace(",", ".").strip()
    try:
        value = float(text)
        if value <= 0 or value > 500:
            raise ValueError
    except ValueError:
        await message.answer("Некорректное число. Пример: 82.1")
        return

    data = await state.get_data()
    global_index = data.get("edit_global_index")
    if global_index is None:
        await message.answer("Не могу найти выбранную запись. Откройте меню редактирования ещё раз.")
        await state.clear()
        return

    storage.update_weight_by_index(global_index, value)
    await state.clear()
    await message.answer("Готово! Запись обновлена. ✅", reply_markup=main_menu_kb())


def register_routes(dp: Dispatcher):
    dp.message.register(start_cmd, CommandStart())
    dp.callback_query.register(register_cb, F.data.startswith("register:"))

    dp.message.register(add_weight_entry, F.text == "➕ Внести вес")
    dp.message.register(show_results,  F.text == "📈 Показать результаты")
    dp.message.register(open_edit_menu, F.text == "✏️ Исправить последние записи")  # NEW

    dp.callback_query.register(edit_pick_cb, F.data.startswith("editpick:"))  # NEW
    dp.message.register(edit_apply_value, WeightForm.editing_wait_value)      # NEW

    dp.message.register(weight_cmd, Command("weight"))
    dp.message.register(weight_input, WeightForm.waiting_for_weight)


async def main():
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    register_routes(dp)
    await on_startup(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
