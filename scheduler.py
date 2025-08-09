# -*- coding: utf-8 -*-
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from config import TIMEZONE
from storage import Storage

REMINDER_TEXT = (
    "Доброе утро! 🌅\n"
    "Пора отправить вес натощак. Нажмите «Внести вес» и введите число (например, 82.4)."
)

def setup_scheduler(bot: Bot, storage: Storage) -> AsyncIOScheduler:
    """
    Создаёт и запускает планировщик.
    В 08:00 Europe/Amsterdam шлём напоминание обоим зарегистрированным.
    """
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)

    async def morning_broadcast():
        users = storage.get_registered_users()
        for _, info in users.items():
            tg_id = info.get("telegram_id")
            if tg_id:
                try:
                    await bot.send_message(chat_id=tg_id, text=REMINDER_TEXT)
                except Exception:
                    # Игнорируем временные фейлы отправки
                    pass

    scheduler.add_job(
        morning_broadcast,
        trigger=CronTrigger(hour=8, minute=0, timezone=TIMEZONE),
        id="daily_reminder",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
