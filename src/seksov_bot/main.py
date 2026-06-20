from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from .bot import build_router
from .config import load_settings
from .storage import Storage


async def run() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    storage = Storage(settings.database_path)
    storage.migrate()
    bot = Bot(settings.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(
        build_router(
            storage,
            settings.standard_dose_ml,
            authorized_user_ids=settings.authorized_telegram_user_ids,
            registration_code=settings.registration_code,
        )
    )
    try:
        await dispatcher.start_polling(bot)
    finally:
        storage.close()
        await bot.session.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
