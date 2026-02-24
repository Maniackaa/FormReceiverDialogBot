from aiogram import Router, Bot, F, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, CommandObject, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ErrorEvent, ReplyKeyboardRemove, CallbackQuery
from aiogram.utils.payload import decode_payload
from aiogram_dialog import DialogManager, StartMode, ShowMode

from config.bot_settings import logger, settings
from dialogs.add_car import add_car_dialog
from dialogs.start import start_dialog
from dialogs.states import StartSG
from services.db_func import get_or_create_user


class IsPrivate(BaseFilter):
    async def __call__(self, message: Message | CallbackQuery) -> bool:
        if isinstance(message, CallbackQuery):
            message = message.message
        # print(f'Проверка на частность: {message.chat.type}\n')
        return message.chat.type == 'private'


router = Router()
router.include_router(start_dialog)
router.include_router(add_car_dialog)
router.message.filter(IsPrivate())
router.callback_query.filter(IsPrivate())


@router.errors()
async def on_unknown_intent(event, dialog_manager: DialogManager, error: Exception):
    if isinstance(error, UnknownIntent):
        # Стек утерян/рассинхронизирован — начнём заново
        await dialog_manager.reset_stack()
        await dialog_manager.start(StartSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.DELETE_AND_SEND)
        return True  # ошибка обработана


@router.message(CommandStart())
async def start_cmd(message: Message, command: CommandObject, dialog_manager: DialogManager):
    args = (command.args or "").strip()
    data = {'org_key': args} if args else {}
    await dialog_manager.start(
        state=StartSG.start,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.DELETE_AND_SEND,
        data=data,
    )


@router.callback_query(F.data == 'start_test')
async def start_test(callback: CallbackQuery, state: FSMContext):
    user = get_or_create_user(callback.from_user)
    logger.info('Старт', user=user)



