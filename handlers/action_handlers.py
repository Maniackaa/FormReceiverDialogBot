import datetime

import structlog
from aiogram import Router, Bot, F
from aiogram.filters import Command, ChatMemberUpdatedFilter, MEMBER, LEFT, ADMINISTRATOR, KICKED, CREATOR
from aiogram.types import CallbackQuery, Message, ChatInviteLink, \
    InlineKeyboardButton, ChatMemberUpdated


logger = structlog.get_logger()

router: Router = Router()


# Действия юзеров
@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=LEFT))
@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def user_kick(event: ChatMemberUpdated, bot: Bot):
    logger.debug('USER KICKED or LEFT')
    try:
        chat = event.chat
        user = event.old_chat_member.user
        logger.info(f'Юзер {user.username} {user.id} KICKED/LEFT с канала {chat.id} {chat.title} ')


    except Exception as err:
        logger.error(err)
        raise err


@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=CREATOR))
@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=ADMINISTRATOR))
@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def user_join(event: ChatMemberUpdated, bot: Bot):
    # GROUP_ID = conf.tg_bot.GROUP_ID
    logger.debug('USER MEMBER')
    try:
        chat = event.chat
        # if chat.id == -1001829561831:
        #     return
        logger.debug(f'{chat.id} {chat.title}')
        member = event.new_chat_member.user
        logger.debug(f'member: {member}')
        logger.info(f'Юзер {member.username} {member.id} присоединился к каналу {chat.id} {chat.title} ')

    except Exception as err:
        logger.error(err)
        raise err


# Действия бота
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def as_member(event: ChatMemberUpdated, bot: Bot):
    logger.debug('MY event MEMBER')
    try:
        chat = event.chat
        owner = event.from_user
        logger.info(f'Бот добавлен в канал {chat.id} {chat.title} как MEMBER  пользователем {owner.username} {owner.id}')
        # await bot.send_message(chat_id=owner.id, text=f'Бот добавлен в канал {chat.id} {chat.title} как MEMBER  пользователем {owner.username} {owner.id}')
    except Exception as err:
        logger.error(err)
        raise err


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=(LEFT | KICKED)))
async def left(event: ChatMemberUpdated, bot: Bot):
    logger.debug('MY event LEFT')
    try:
        logger.debug(event)
        chat = event.chat
        owner = event.from_user
        logger.info(f'Бот удален с канала {chat.id} {chat.title} пользователем {owner.username} {owner.id}')
    except Exception as err:
        logger.error(err)
        raise err


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=ADMINISTRATOR))
async def as_admin(event: ChatMemberUpdated, bot: Bot):
    logger.debug('MY event ADMINISTRATOR')
    try:
        chat = event.chat
        owner = event.from_user
        logger.info(f'Бот добавлен в канал {chat.id} {chat.title} как ADMINISTRATOR пользователем {owner.username} {owner.id}')

    except Exception as err:
        logger.error(err)
        raise err


