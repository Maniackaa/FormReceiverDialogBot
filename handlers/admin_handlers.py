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
from keyboards.keyboards import custom_kb


from config.bot_settings import logger
from services.db_func import get_obj

router: Router = Router()


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
