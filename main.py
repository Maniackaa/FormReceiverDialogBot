import asyncio
import time

import aioschedule
import schedule
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from aiogram_dialog import setup_dialogs

from config.bot_settings import logger, settings, BASE_DIR
from handlers import user_handlers, action_handlers, admin_handlers
from services.db_func import get_objs_to_send
from services.email_func import send_obj


async def set_commands(bot: Bot):
    commands = [
        BotCommand(
            command="start",
            description="Start",
        ),
    ]

    admin_commands = commands.copy()
    admin_commands.append(
        BotCommand(
            command="admin",
            description="Admin panel",
        )
    )

    await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.set_my_commands(
                commands=admin_commands,
                scope=BotCommandScopeChat(
                    chat_id=admin_id,
                ),
            )
        except Exception as err:
            logger.info(f'Админ id {admin_id}  ошибочен')


async def send_job(bot):
    while True:
        try:
            objs_to_send = get_objs_to_send()
            logger.debug(f'obj to send: {objs_to_send}')
            for obj in objs_to_send:
                try:
                    await send_obj(obj, bot)
                    await asyncio.sleep(0.1)
                except Exception as err:
                    logger.error(err)
            await asyncio.sleep(30)
        except Exception as err:
            logger.error(err)
            pass


async def count_reset():
    with open(BASE_DIR / 'count.ini', 'w') as file:
        file.write('0')


async def shedule_start():
    schedule.every().day.at("00:00", "Europe/Moscow").do(count_reset)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(60)


async def main():
    if settings.USE_REDIS:
        storage = RedisStorage.from_url(
            url=f"redis://{settings.REDIS_HOST}",
            connection_kwargs={
                "db": 0,
            },
            key_builder=DefaultKeyBuilder(with_destiny=True),
        )
    else:
        storage = MemoryStorage()

    bot = Bot(token=settings.BOT_TOKEN,  default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage, events_isolation=SimpleEventIsolation())

    try:
        dp.include_router(admin_handlers.router)
        dp.include_router(user_handlers.router)
        dp.include_router(action_handlers.router)
        setup_dialogs(dp)

        await set_commands(bot)
        # await bot.get_updates(offset=-1)
        await bot.delete_webhook(drop_pending_updates=True)
        try:
            await bot.send_message(chat_id=settings.ADMIN_IDS[0], text='Бот запущен')
        except Exception as err:
            logger.warning(err)

        asyncio.create_task(shedule_start())
        # await bot.send_message(chat_id=config.tg_bot.GROUP_ID, text='Бот запущен', reply_markup=begin_kb)
        await dp.start_polling(bot, config=settings)
    finally:
        await dp.fsm.storage.close()
        await bot.session.close()


try:
    asyncio.run(main())
except (KeyboardInterrupt, SystemExit):
    logger.error("Bot stopped!")
