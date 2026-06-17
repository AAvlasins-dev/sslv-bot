"""Entry point. Preloads cache, sets bot commands, starts polling + monitor."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault, MenuButtonCommands

import cache
import config
import db
import bot as botmod
import monitor
import parser as p

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("main")

BOT_COMMANDS = [
    BotCommand(command="start",    description="🚀 Запустить бота / Start"),
    BotCommand(command="add",      description="➕ Добавить фильтр"),
    BotCommand(command="list",     description="📋 Мои фильтры"),
    BotCommand(command="stats",    description="📊 Статистика"),
    BotCommand(command="location", description="📍 Моё местоположение"),
    BotCommand(command="lang",     description="🌐 Выбрать язык"),
    BotCommand(command="cancel",   description="❌ Отмена"),
]


async def main():
    await db.init(config.DB_PATH)
    log.info("DB: %s", config.DB_PATH)

    bot = Bot(token=config.BOT_TOKEN)
    dp  = Dispatcher()
    dp.include_router(botmod.router)

    # Команды и кнопка меню
    await bot.set_my_commands(BOT_COMMANDS, scope=BotCommandScopeDefault())
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    log.info("Bot commands set (%d)", len(BOT_COMMANDS))

    # Монитор
    asyncio.create_task(monitor.monitor_loop(
        bot,
        base_interval=config.CHECK_INTERVAL_SEC,
        max_per_cycle=config.MAX_NOTIFICATIONS_PER_CYCLE,
    ))

    # Предзагрузка кэша в фоне (не блокирует старт бота)
    asyncio.create_task(cache.preload(p))

    await bot.delete_webhook(drop_pending_updates=True)
    log.info("ss.lv monitor started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nbye")
