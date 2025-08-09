# meals.py
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from aiogram.types import Message

from config import TIMEZONE, BREAKFAST_FILE, LUNCH_FILE, DINNER_FILE, SNACK1_FILE, SNACK2_FILE

# ---------- helpers ----------
def _load_json(path: Path) -> list[dict]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)

def _num(x) -> Optional[float]:
    try:
        return None if x is None else float(x)
    except (TypeError, ValueError):
        return None

def _fmt_g(v: Optional[float]) -> str:
    if v is None: return "—"
    return f"{v:.0f} г" if abs(v - round(v)) < 1e-6 else f"{v:.1f} г"

def _fmt_kcal(v: Optional[float]) -> str:
    if v is None: return "—"
    return f"{v:.0f} ккал" if abs(v - round(v)) < 1e-6 else f"{v:.1f} ккал"

def _fmt_g_macro(v: Optional[float]) -> str:
    if v is None: return "—"
    return f"{v:.0f} г" if abs(v - round(v)) < 1e-6 else f"{v:.1f} г"

def _calc_meal_totals(items: list[dict]) -> Optional[dict]:
    has_any = False
    kcal = prot = fat = carb = 0.0
    for it in items:
        k = _num(it.get("kcal")); p = _num(it.get("protein_g"))
        f = _num(it.get("fat_g")); c = _num(it.get("carbs_g"))
        if any(v is not None for v in (k, p, f, c)):
            has_any = True
        kcal += 0.0 if k is None else k
        prot += 0.0 if p is None else p
        fat  += 0.0 if f is None else f
        carb += 0.0 if c is None else c
    if not has_any:
        return None
    return {"kcal": kcal, "protein_g": prot, "fat_g": fat, "carbs_g": carb}

def _meal_totals_or_recalc(meal: dict) -> Optional[dict]:
    mt = meal.get("meal_totals")
    if isinstance(mt, dict) and any(mt.values()):
        return mt
    items = meal.get("items")
    if isinstance(items, list) and items:
        return _calc_meal_totals(items)
    return None

def _format_item_line(it: dict) -> str:
    # поддержка разных ключей имени
    name = it.get("name") or it.get("item") or it.get("title") or "Позиция"
    raw_g    = _num(it.get("raw_g"))
    cooked_g = _num(it.get("cooked_g"))
    kcal     = _num(it.get("kcal"))
    p        = _num(it.get("protein_g"))
    f        = _num(it.get("fat_g"))
    c        = _num(it.get("carbs_g"))

    grams_parts = []
    if raw_g is not None:
        grams_parts.append(f"{_fmt_g(raw_g)} (сух.)")
    if cooked_g is not None:
        grams_parts.append(f"{_fmt_g(cooked_g)} (готов.)")
    grams_txt = " — " + ", ".join(grams_parts) if grams_parts else ""

    kji_txt = ""
    if any(v is not None for v in (kcal, p, f, c)):
        kji_txt = f" — {_fmt_kcal(kcal)}, Б/Ж/У: {_fmt_g_macro(p)}/{_fmt_g_macro(f)}/{_fmt_g_macro(c)}"

    return f" • <b>{name}</b>{grams_txt}{kji_txt}"

def _format_simple_meal(meal: dict) -> str:
    parts = [meal.get(f"item{i}") for i in range(1, 10) if meal.get(f"item{i}")]
    return "\n".join(f" • {p}" for p in parts) if parts else "—"

def _format_meal_block(title: str, emoji: str, meal: dict) -> tuple[str, Optional[dict]]:
    day_no = meal.get("day", "?")
    items = meal.get("items")
    if isinstance(items, list) and items:
        lines = "\n".join(_format_item_line(it) for it in items)
        totals = _meal_totals_or_recalc(meal)
        totals_txt = ""
        if totals:
            totals_txt = (
                f"\n<i>Итого:</i> "
                f"{_fmt_kcal(_num(totals.get('kcal')))}, "
                f"Б {_fmt_g_macro(_num(totals.get('protein_g')))}, "
                f"Ж {_fmt_g_macro(_num(totals.get('fat_g')))}, "
                f"У {_fmt_g_macro(_num(totals.get('carbs_g')))}"
            )
        block = f"{emoji} <b>{title}</b> (№{day_no})\n{lines}{totals_txt}"
        return block, totals
    else:
        # простой формат item1..itemN
        block = f"{emoji} <b>{title}</b> (№{day_no})\n{_format_simple_meal(meal)}"
        return block, None

def _pick_by_day(meals: list[dict], day_num: int) -> dict:
    """
    Берём запись с индексом = номер дня.
    Если длина списка < номер дня — делаем циклическое смещение (wrap-around).
    """
    if not meals:
        return {}
    idx = (day_num - 1) % len(meals)
    return meals[idx]

# ---------- handler ----------
async def handle_what_to_eat_today(message: Message):
    """
    Логика: сегодняшнее число по МСК -> один и тот же номер для:
    Завтрак, Перекус 1, Обед, Полдник, Ужин.
    Формат дат: ДД.ММ.ГГГГ.
    """
    today = datetime.now(TIMEZONE).date()
    date_human = today.strftime("%d.%m.%Y")
    day_num = today.day  # 1..31

    breakfasts = _load_json(BREAKFAST_FILE)
    lunches    = _load_json(LUNCH_FILE)
    dinners    = _load_json(DINNER_FILE)
    snack1     = _load_json(SNACK1_FILE)
    snack2     = _load_json(SNACK2_FILE)

    b = _pick_by_day(breakfasts, day_num)
    s1 = _pick_by_day(snack1, day_num)
    l = _pick_by_day(lunches, day_num)
    s2 = _pick_by_day(snack2, day_num)
    d = _pick_by_day(dinners, day_num)

    b_block, b_tot = _format_meal_block("Завтрак",  "☕️", b)
    s1_block, s1_tot = _format_meal_block("Перекус 1","🥪", s1)
    l_block, l_tot = _format_meal_block("Обед",      "🍲", l)
    s2_block, s2_tot = _format_meal_block("Полдник", "🍎", s2)
    d_block, d_tot = _format_meal_block("Ужин",      "🍛", d)

    # Общая сумма за день — если есть КБЖУ в источниках
    totals_list = [t for t in (b_tot, s1_tot, l_tot, s2_tot, d_tot) if t]
    footer = ""
    if totals_list:
        kcal = sum(_num(t.get("kcal")) or 0.0 for t in totals_list)
        prot = sum(_num(t.get("protein_g")) or 0.0 for t in totals_list)
        fat  = sum(_num(t.get("fat_g")) or 0.0 for t in totals_list)
        carb = sum(_num(t.get("carbs_g")) or 0.0 for t in totals_list)
        footer = (
            "\n\n<b>ИТОГО за день:</b>\n"
            f" • {_fmt_kcal(kcal)}\n"
            f" • Белки: {_fmt_g_macro(prot)}\n"
            f" • Жиры:  {_fmt_g_macro(fat)}\n"
            f" • Углев: {_fmt_g_macro(carb)}"
        )

    header = f"🍽 <b>Меню на {date_human}</b>\n<i>Номер дня по МСК: {day_num}</i>"
    text = f"{header}\n\n{b_block}\n\n{s1_block}\n\n{l_block}\n\n{s2_block}\n\n{d_block}{footer}"
    await message.answer(text)
