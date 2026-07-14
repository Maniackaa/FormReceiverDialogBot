from aiogram import Router, Bot, F, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, CommandObject, BaseFilter, ExceptionTypeFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ErrorEvent, ReplyKeyboardRemove, CallbackQuery
from aiogram.utils.payload import decode_payload
from aiogram_dialog import DialogManager, StartMode, ShowMode
from aiogram_dialog.api.exceptions import UnknownIntent

from config.bot_settings import logger, settings
from config.media_ids import clear_welcome_media, fix_welcome_media_type_from_telegram_error
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


@router.errors(ExceptionTypeFilter(TelegramBadRequest))
async def on_telegram_bad_request(event: ErrorEvent, dialog_manager: DialogManager):
    err = event.exception
    msg = str(err)
    if "can't use file of type" in msg:
        if fix_welcome_media_type_from_telegram_error(msg):
            logger.warning("Исправлен тип welcome-медиа после ошибки Telegram", error=msg)
        else:
            clear_welcome_media()
            logger.warning("Удалено некорректное welcome-медиа", error=msg)
        await dialog_manager.reset_stack()
        await dialog_manager.start(
            StartSG.start,
            mode=StartMode.RESET_STACK,
            show_mode=ShowMode.DELETE_AND_SEND,
        )
        return True
    return False


@router.errors(ExceptionTypeFilter(UnknownIntent))
async def on_unknown_intent(event: ErrorEvent, dialog_manager: DialogManager):
    # Стек утерян/рассинхронизирован — начнём заново (исключение: event.exception).
    # Отслеживание незавершённой заявки не сбрасываем — пользователь не нажимал «Подтвердить».
    await dialog_manager.reset_stack()
    await dialog_manager.start(StartSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.DELETE_AND_SEND)
    return True


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



