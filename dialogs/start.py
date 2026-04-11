import json

from aiogram import Router, Bot
from aiogram.enums import ContentType
from aiogram.types import User, CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Select, Back, Group, SwitchTo
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Format, Const

from config.bot_settings import settings, logger, BASE_DIR
from config.media_ids import get_welcome_animation_file_id

from dialogs.states import StartSG, AddCarSG
from dialogs.type_factorys import conv_check

router = Router()

# Приветственный текст с шапкой KREX-PEX
WELCOME_TEXT = (
    "<b>KREX-PEX exchange 💸</b>\n"
    "сервис обмена валюты во Вьетнаме приветствует вас\n\n"
    "Нячанг | Дананг | Фукуок\n"
    "…а так же выдача наличных через банкомат, в любом городе Вьетнама\n\n"
    "🍀 ваш надёжный друг во Вьетнаме уже более трёх лет\n"
    "🍀 всегда честный курс – никаких скрытых комиссий\n"
    "🍀 первоклассный сервис до, во время и после сделки\n"
    "🍀 дарим тёплые сюрпризы каждому\n\n"
    "для оформления заявки выберите соответствующий пункт меню 👇"
)

# b. Как проходит сделка?
HOW_DEAL_TEXT = (
    "<b>Как проходит сделка?</b>\n\n"
    "1. Оставляете заявку — и мы сразу берём дело в свои руки. Наш курьер свяжется с вами, "
    "чтобы договориться о встрече в удобное для вас время и место.\n\n"
    "2. Остаёмся на связи: Курьер предупредит вас за несколько минут до приезда, "
    "чтобы вы спокойно могли спуститься в лобби. Никакого ожидания!\n\n"
    "3. Встреча и обмен: Вы получаете запечатанный конверт с донгами (VND), пересчитываете их "
    "и только после этого переводите рубли (или KZT, CNY, crypto) по реквизитам, которые предоставит курьер. "
    "Всё честно и прозрачно.\n\n"
    "4. Приятного отдыха! А мы будем ждать вашего следующего обращения."
)

# c. Как получить деньги в банкомате?
HOW_ATM_TEXT = (
    "<b>Как получить деньги в банкомате?</b>\n\n"
    "Раздел в разработке. Скоро здесь появится информация о получении денег в банкомате в любом городе Вьетнама."
)

# d. О нас
ABOUT_TEXT = (
    "Уже более трёх лет мы работаем для того, чтобы ваше пребывание во Вьетнаме было по-настоящему комфортным. "
    "С самого первого дня нам хотелось быть особенными — не просто ещё одним сервисом обмена, а чем-то большим.\n\n"
    "Сегодня мы с гордостью можем сказать: мы действительно уникальны. Мы создали свой неповторимый стиль, "
    "чтобы каждая встреча с нами была вам в радость.\n\n"
    "🍀 вы всегда узнаете нашего курьера — он приедет на фирменном скутере с логотипом сервиса.\n"
    "🍀 вы будете приятно удивлены, получив деньги в эксклюзивном конверте с \"пасхалкой\".\n"
    "🍀 внутри конверта вас ждёт маленький кусочек дома — ириска, специально привезённая для вас из России. Это наша традиция.\n"
    "🍀 для новых друзей у нас особый подарок — уникальный брелок высочайшего качества, в виде нашего фирменного скутера "
    "(спроектирован нами). Пусть он станет для вас приятным напоминанием о поездке и о нас 🤭.\n\n"
    "Спасибо, что выбираете нас. Сегодня мы — крупнейший сервис обмена валют во Вьетнаме, и это всё благодаря вашему доверию! 🫰"
)

async def start_getter(dialog_manager: DialogManager, event_from_user: User, bot: Bot, **kwargs):
    data = dialog_manager.dialog_data
    logger.debug("start_getter", dialog_data=data, start_data=dialog_manager.start_data)

    items = [
        (1, "Оформить заявку ✍️"),
        (2, "Как проходит сделка?"),
        (3, "Как получить деньги в банкомате?"),
        (4, "О нас"),
    ]
    is_admin = event_from_user.id in settings.ADMIN_IDS
    if is_admin:
        items.append((5, "Admin 🚷"))

    with open(BASE_DIR / "conv.ini", "r", encoding="utf-8") as file:
        convertation = json.loads(file.read())

    convertation_text = (
        f"<code>'₽ - ₫':           {convertation[0][0]}</code>\n"
        f"<code>'₽ - ₫ >= 100тыс': {convertation[0][1]}\n</code>"
        f"<code>'new $ - ₫':       {convertation[1]}\n</code>"
        f"<code>'old $ - ₫':       {convertation[2]}\n</code>"
        f"<code>'USDT - ₫':        {convertation[3]}\n\n</code>"
        "Введите новые курсы через ;"
    )

    welcome_media = None
    anim_id = get_welcome_animation_file_id()
    if anim_id:
        welcome_media = MediaAttachment(
            type=ContentType.ANIMATION,
            file_id=MediaId(file_id=anim_id),
        )

    return {
        "username": event_from_user.username,
        "welcome_text": WELCOME_TEXT,
        "welcome_media": welcome_media,
        "items": tuple(items),
        "convertation_text": convertation_text,
        "is_admin": is_admin,
        "how_deal_text": HOW_DEAL_TEXT,
        "how_atm_text": HOW_ATM_TEXT,
        "about_text": ABOUT_TEXT,
    }


async def main_menu_select(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    item_id = int(item_id)
    data = dialog_manager.dialog_data

    if item_id == 1:
        data.update(channel_id=item_id)
        await dialog_manager.start(AddCarSG.city, data=data)
    elif item_id == 2:
        await dialog_manager.switch_to(StartSG.how_deal)
    elif item_id == 3:
        await dialog_manager.switch_to(StartSG.how_atm)
    elif item_id == 4:
        await dialog_manager.switch_to(StartSG.about)
    elif item_id == 5:
        await dialog_manager.switch_to(StartSG.convert)


start_dialog = Dialog(
    Window(
        DynamicMedia(selector="welcome_media"),
        Format(text="{welcome_text}"),
        Group(
            Select(
                Format("{item[1]}"),
                id="start_poll",
                on_click=main_menu_select,
                items="items",
                item_id_getter=lambda x: x[0],
            ),
            width=1,
        ),
        state=StartSG.start,
        getter=start_getter,
    ),
    Window(
        Format(text="{convertation_text}"),
        TextInput(
            id="conv",
            type_factory=conv_check,
            on_success=Back(),
        ),
        Back(Const("Назад")),
        state=StartSG.convert,
        getter=start_getter,
    ),
    Window(
        Format(text="{how_deal_text}"),
        SwitchTo(Const("Назад"), id="back_to_start", state=StartSG.start),
        state=StartSG.how_deal,
        getter=start_getter,
    ),
    Window(
        Format(text="{how_atm_text}"),
        SwitchTo(Const("Назад"), id="back_to_start", state=StartSG.start),
        state=StartSG.how_atm,
        getter=start_getter,
    ),
    Window(
        Format(text="{about_text}"),
        SwitchTo(Const("Назад"), id="back_to_start", state=StartSG.start),
        state=StartSG.about,
        getter=start_getter,
    ),
)
