import json
import pickle
from pprint import pprint

from aiogram import Router, Bot
from aiogram.enums import ContentType
from aiogram.filters import BaseFilter
from aiogram.types import User, CallbackQuery, Message, Update
from aiogram_dialog import Dialog, Window, DialogManager, StartMode, ShowMode
from aiogram_dialog.widgets.input import MessageInput, TextInput, ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Select, Url, Column, Back, Next, Start
from aiogram_dialog.widgets.text import Format, Const

from config.bot_settings import settings, logger, BASE_DIR

from dialogs.states import StartSG, AddCarSG, ProfileSG
from dialogs.type_factorys import conv_check

router = Router()


async def start_getter(dialog_manager: DialogManager, event_from_user: User, bot: Bot, event_update: Update, **kwargs):
    data = dialog_manager.dialog_data
    logger.debug('start_getter', dialog_data=data, start_data=dialog_manager.start_data)

    hello_text = f'В этом боте вы сможете'
    items = (
        # (-1002092051636, 'Тестовый канал'),
        (1, 'ОФОРМИТЬ ЗАЯВКУ ✍️'),
    )
    with open(BASE_DIR / 'conv.ini', 'r') as file:
        convertation = json.loads(file.read())

    convertation_text = (
        f"<code>'₽ - ₫':           {convertation[0][0]}</code>\n"
        f"<code>'₽ - ₫ >= 100тыс': {convertation[0][1]}\n</code>"
        f"<code>'new $ - ₫':       {convertation[1]}\n</code>"
        f"<code>'old $ - ₫':       {convertation[2]}\n</code>"
        f"<code>'USDT - ₫':        {convertation[3]}\n\n</code>"
        f"Введите новые курсы через ;"
    )
    is_admin = event_from_user.id in settings.ADMIN_IDS
    return {'username': event_from_user.username, 'hello_text': hello_text, 'items': items, 'convertation_text': convertation_text, 'is_admin': is_admin}


async def channel_select(callback: CallbackQuery, widget: Select,
                         dialog_manager: DialogManager, item_id: str):
    data = dialog_manager.dialog_data
    data.update(channel_id=item_id)
    await dialog_manager.start(AddCarSG.convert, data=data)
    # await dialog_manager.start(AddCarSG.photo, data=data)


start_dialog = Dialog(
    Window(
        Format(text='{hello_text}'),
        Column(
            Select(Format('{item[1]}'),
                   id='start_poll',
                   on_click=channel_select,
                   items='items',
                   item_id_getter=lambda x: x[0]),
        ),
        Button(text=Const('admin'),
               on_click=Next(), id='contacts',
               when='is_admin'
               ),
        state=StartSG.start,
        getter=start_getter,
    ),
    Window(
        Format(text='{convertation_text}'),
        TextInput(
            id='conv',
            type_factory=conv_check,
            on_success=Back(),
        ),
        Back(Const('Назад')),
        state=StartSG.convert,
        getter=start_getter,

    )
)




