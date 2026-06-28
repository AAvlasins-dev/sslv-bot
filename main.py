"""Entry point. Preloads cache, sets bot commands, starts polling + monitor."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommandScopeDefault, MenuButtonDefault, ErrorEvent

import cache
import config
import db
import bot as botmod
import i18n
import monitor
import parser as p

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("main")


async def main():
    await db.init(config.DB_PATH)
    log.info("DB: %s", config.DB_PATH)

    bot = Bot(token=config.BOT_TOKEN)
    dp  = Dispatcher()
    dp.include_router(botmod.router)

    # Глобальная страховка: любое необработанное исключение в хендлере не должно
    # оставлять пользователя с «висящими часиками» — даём явный ответ.
    @dp.errors()
    async def _on_error(event: ErrorEvent):
        log.exception("unhandled handler error: %s", event.exception)
        upd = event.update
        try:
            if getattr(upd, "callback_query", None):
                await upd.callback_query.answer(
                    "⚠️ Ошибка. Откройте меню заново: /add", show_alert=True)
            elif getattr(upd, "message", None):
                await upd.message.answer("⚠️ Что-то пошло не так. Откройте меню заново: /add")
        except Exception:
            pass
        return True   # помечаем обработанным — диспетчер не падает

    # Меню команд «/» НЕ используем — у бота есть постоянные кнопки внизу (main_kb),
    # чтобы не было дублирующегося меню. Чистим ранее установленные команды и
    # возвращаем кнопке меню поведение по умолчанию (без списка команд).
    for lc in (None, "ru", "lv", "en"):
        try:
            if lc is None:
                await bot.delete_my_commands(scope=BotCommandScopeDefault())
            else:
                await bot.delete_my_commands(scope=BotCommandScopeDefault(), language_code=lc)
        except Exception as e:
            log.warning("delete_my_commands %s: %s", lc, e)
    try:
        await bot.set_chat_menu_button(menu_button=MenuButtonDefault())
    except Exception as e:
        log.warning("set_chat_menu_button: %s", e)
    log.info("Bot command menu removed (using reply keyboard only)")

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
