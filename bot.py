import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

import config
import database as db
from handlers import registration, admin, user

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    await db.init_db()
    logger.info("Ma'lumotlar bazasi tayyor.")

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())

    # Tartib muhim: registratsiya -> admin -> oddiy user (fallback handlerlar oxirida)
    dp.include_router(registration.router)
    dp.include_router(admin.router)
    dp.include_router(user.router)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot ishga tushdi (polling rejimida).")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
