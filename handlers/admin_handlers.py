import datetime
from pathlib import Path

import pandas as pd
from aiogram import Bot, F, Router
from aiogram.filters import (ADMINISTRATOR, KICKED, LEFT, MEMBER,
                             ChatMemberUpdatedFilter, Command, StateFilter)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (CallbackQuery, ChatInviteLink, ChatMemberUpdated,
                           InlineKeyboardButton, Message, FSInputFile)
from aiogram_dialog import DialogManager

from config.bot_settings import BASE_DIR, settings
from config.media_ids import save_welcome_animation_file_id
from keyboards.keyboards import custom_kb

from config.bot_settings import logger
from services.db_func import get_obj

router: Router = Router()


@router.message((F.animation | F.document | F.photo) & F.from_user.as_("user"))
async def admin_get_file_id(message: Message, user):
    """Админ скидывает файл — бот возвращает file_id и сохраняет как приветственную анимацию."""
    if user.id not in settings.ADMIN_IDS:
        return
    file_id = None
    kind = None
    if message.animation:
        file_id = message.animation.file_id
        kind = "анимация (GIF)"
    elif message.document:
        file_id = message.document.file_id
        kind = "документ"
    elif message.photo:
        file_id = message.photo[-1].file_id
        kind = "фото"

    if file_id:
        save_welcome_animation_file_id(file_id)
        await message.reply(
            f"<b>file_id получен</b> ({kind}):\n"
            f"<code>{file_id}</code>\n\n"
            "Сохранён как приветственная анимация на старте бота."
        )


@router.callback_query(F.data.startswith('obj:'))
async def start_test(callback: CallbackQuery, state: FSMContext):
    logger.debug(f'{callback.data}')
    _, pk, delay = callback.data.split(':')
    pk = int(pk)
    delay = int(delay)
    if delay == 0:
        obj = get_obj(pk)
        obj.set('target_time', settings.tz.localize(datetime.datetime.now()))
    await callback.message.delete()
