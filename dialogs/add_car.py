import asyncio
import datetime
import json
import pickle
from pprint import pprint

from aiogram import Router, Bot, F
from aiogram.enums import ContentType
from aiogram.filters import BaseFilter
from aiogram.types import User, CallbackQuery, Message, Update, InputMediaPhoto
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram_dialog import Dialog, Window, DialogManager, StartMode, ShowMode
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.common import ManagedScroll
from aiogram_dialog.widgets.input import MessageInput, TextInput, ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Select, Url, Column, Back, Next, StubScroll, Group, NumberedPager, \
    SwitchTo, Start
from aiogram_dialog.widgets.media import DynamicMedia, StaticMedia
from aiogram_dialog.widgets.text import Format, Const

from config.bot_settings import settings, logger, BASE_DIR
from dialogs.buttons import go_start

from dialogs.states import StartSG, AddCarSG
from dialogs.type_factorys import positive_int_check, tel_check
from services.db_func import create_obj, get_or_create_user
from services.email_func import send_obj_to_admin


async def car_getter(dialog_manager: DialogManager, event_from_user: User, bot: Bot, event_update: Update, **kwargs):
    data = dialog_manager.dialog_data
    with open(BASE_DIR / 'conv.ini', 'r') as file:
        convertation = json.loads(file.read())
    data['convertation'] = convertation
    with open(BASE_DIR / 'count.ini') as file:
        count = int(file.read())
    currency = ['₽', 'new $', 'old $', 'USDT']
    minimum_post = [20000, 200, 200, 200]

    banks = ['Т банк', 'Сбер', 'Альфа', 'Райффайзен', 'ВТБ']
    net = ['TON', 'TRC20', 'BEP20', 'BYBIT UID']
    car_data = {
        'currency': currency,
        'banks': banks,
        'sbp': ['Да', 'Нет'],
        'convertation': convertation,
        'net': net
    }
    result = {}
    for key, values in car_data.items():
        items = []
        for index, item in enumerate(values):
            if key == 'currency':
                items.append((index, f'{item} - ₫'))
            else:
                items.append((index, item))
        result[f'{key}_items'] = items

    data['getter'] = result
    data['convertation'] = convertation
    data['minimum_post'] = minimum_post
    result['city_items'] = tuple(CITY_ITEMS)

    logger.debug(data)

    price_str = f"{int(data.get('price', 0)):,}".replace(',', ' ')
    dong = f"{data.get('value', 0):,}".replace(',', ' ')
    currency_id = int(data.get('currency_id', 0))
    amount_currency = currency[currency_id]  # ₽, new $, old $, USDT
    result_text = (
        f"💸 ЗАЯВКА 💸 № {count}\n"
        f"📍 {data.get('city_str', '')}\n"
        f"{data.get('currency_str')}\n"
        f"______________________________\n\n"
        
        f"🧔‍♀ ️{event_from_user.first_name}\n"
        f"🤖  @{event_from_user.username}\n"
        f"🪙  {data.get('banks_str') or data.get('net') or data.get('net_str') or data.get('bank') or ''}\n"
        f"💸  {data.get('sbp_str') or ''}\n\n"
        f"сумма:  {price_str} {amount_currency}\n\n"
        f"📍 {data.get('location') or ''}\n\n"
        f"ℹ️   {data.get('info') or ''}\n\n"
        f"отдаем ₫: {dong}"

    )
    result['result_text'] = result_text
    data['result_text'] = result_text
    data['count'] = count
    result['currency_str'] = data.get('currency_str', '')
    data['currency'] = currency
    return result


async def next_window(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.next()


def int_check(text: str) -> str:
    if all(ch.isdigit() for ch in text) and 0 <= int(text) <= 120:
        return text
    raise ValueError


CITY_ITEMS = [
    (1, 'Нячанг'),
    (2, 'Дананг'),
    (3, 'Фукуок'),
    (4, 'Снятие денег в банкомате, в любом городе Вьетнама'),
]


async def city_select(callback: CallbackQuery, widget: Select,
                      dialog_manager: DialogManager, item_id: str):
    data = dialog_manager.dialog_data
    idx = int(item_id)
    data['city_id'] = item_id
    data['city_str'] = next((c[1] for c in CITY_ITEMS if c[0] == idx), '')
    await dialog_manager.next()
    logger.debug(f'data: {data}')


async def item_select(callback: CallbackQuery, widget: Select,
                       dialog_manager: DialogManager, item_id: str):
    data = dialog_manager.dialog_data
    getter = data['getter']
    field = widget.widget_id
    data[f'{field}_id'] = item_id
    data[f'{field}_str'] = getter[f'{field}_items'][int(item_id)][1]
    if field == 'sbp':
        await dialog_manager.switch_to(AddCarSG.location)
    else:
        await dialog_manager.next()
    logger.debug(f'data: {data}')


async def text_input(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str) -> None:
    data = dialog_manager.dialog_data
    logger.debug(data)
    field = widget.widget.widget_id
    data[field] = text
    currency_id = int(data['currency_id'])
    if field == 'price':
        convertation = data['convertation']
        price = float(text)
        data[field] = price

        if currency_id == 0:
            if price >= 100000:
                koef = convertation[0][1]
            else:
                koef = convertation[0][0]
        else:
            koef = convertation[currency_id]
        data['koef'] = koef

        limit = int(data['minimum_post'][currency_id])
        total_value = int(koef * price)
        if price < limit:
            await message.answer(f'Бесплатная доставка осуществляется при обмене от {limit} {data["currency"][currency_id]}. Вычитается стоимость доставки – 70 000 ₫')
            total_value -= 70000
        total_value += 10000  # бонус 10 000 ₫
        data['value'] = total_value
        await message.answer(f"Сумма к получению: {total_value:,} ₫".replace(',', ' '))
        if currency_id == 0:
            await dialog_manager.switch_to(AddCarSG.bank)
        elif currency_id == 3:
            await dialog_manager.switch_to(AddCarSG.net)
        elif currency_id in [1, 2]:
            await dialog_manager.switch_to(AddCarSG.location)
        return
    await dialog_manager.next()
    logger.debug(f'data: {data}')


async def confirm(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    data = dialog_manager.dialog_data
    with open(BASE_DIR / 'count.ini', 'w') as file:
        file.write(str(data['count']+1))

    data = dialog_manager.dialog_data
    await callback.message.answer(text=f'Ваша заявка отправлена')
    await callback.bot.send_message(chat_id=settings.CHANNEL, text=f'{data["result_text"]}')
    if not callback.from_user.username:
        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=f'Внимание - ваш профиль закрыт. Мы не сможем с вами связаться, поэтому напишите @operator_krexpex')
    await callback.message.copy_to(chat_id=settings.ADMIN_IDS[0])
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK)

add_car_dialog = Dialog(
    Window(
        Format(text="""Выберите город:"""),
        Group(
            Select(Format('{item[1]}'),
                   id='city',
                   on_click=city_select,
                   items='city_items',
                   item_id_getter=lambda x: x[0]),
            width=1
        ),
        Start(Const('Сначала'), state=StartSG.start, id='start_menu'),
        state=AddCarSG.city,
        getter=car_getter,
    ),
    Window(
        Format(text="""Выберете направления обмена:"""),
        Group(
            Select(Format('{item[1]}'),
                   id='currency',
                   on_click=item_select,
                   items='currency_items',
                   item_id_getter=lambda x: x[0]),
            width=1
        ),

        Start(Const('Сначала'), state=StartSG.start, id='start_menu'),
        state=AddCarSG.convert,
        getter=car_getter,
    ),
    Window(
        Format(text='ВВЕДИТЕ СУММУ {currency_str} 💬'),
        TextInput(
            id='price',
            type_factory=positive_int_check,
            on_success=text_input,
        ),
        Start(Const('Сначала'), state=StartSG.start, id='start_menu'),
        state=AddCarSG.price,
        getter=car_getter,
    ),
    Window(
        Format(text='Выберите банк или напишите свой 💬'),
        Group(
            Select(Format('{item[1]}'),
                   id='banks',
                   on_click=item_select,
                   items='banks_items',
                   item_id_getter=lambda x: x[0]),
            width=1
        ),
        TextInput(
            id='bank',
            on_success=text_input,
        ),
        Start(Const('Сначала'), state=StartSG.start, id='start_menu'),
        state=AddCarSG.bank,
        getter=car_getter
    ),
    Window(
        Format(text='СБП?'),
        Group(
            Select(Format('{item[1]}'),
                   id='sbp',
                   on_click=item_select,
                   items='sbp_items',
                   item_id_getter=lambda x: x[0]),
            width=1
        ),
        Start(Const('Сначала'), state=StartSG.start, id='start_menu'),
        state=AddCarSG.sbp,
        getter=car_getter
    ),
    Window(
        Format(text="""Выберите сеть или напишите свою"""),
        Group(
            Select(Format('{item[1]}'),
                   id='net',
                   on_click=item_select,
                   items='net_items',
                   item_id_getter=lambda x: x[0]),
            width=1
        ),
        TextInput(
            id='net',
            on_success=text_input,
        ),
        Start(Const('Сначала'), state=StartSG.start, id='start_menu'),
        state=AddCarSG.net,
        getter=car_getter,
    ),
    Window(
        # StaticMedia(
        #     path='link_img.jpg',
        #     type=ContentType.PHOTO
        # ),
        # Format(text=' Локация (скопированная ссылка из Google Maps)'),
        Format(text='Название вашего отеля (ссылка) 💬'),
        TextInput(
            id='location',
            on_success=text_input,
        ),
        Start(Const('Сначала'), state=StartSG.start, id='start_menu'),
        state=AddCarSG.location,
    ),
    Window(
        Format(text='Info (любая дополнительная информация которая может пригодиться, например желаемое время встречи)'),
        TextInput(
            id='info',
            on_success=text_input,
        ),
        Next(Const('Далее'), id='skip_info'),
        Start(Const('Сначала'), state=StartSG.start, id='start_menu'),
        state=AddCarSG.info,
    ),

    Window(
        Format(text='{result_text}'),
        Button(text=Const('Подтвердить'),
               on_click=confirm,
               id='confirm'),
        Button(text=Const('Отменить'),
               on_click=go_start,
               id='start'),
        state=AddCarSG.confirm,
        getter=car_getter,
    ),
)