import asyncio
import datetime
import json
import os
from smtplib import SMTPException
import logging
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError

from config.bot_settings import logger, settings
from database.db import ObjModel
from keyboards.keyboards import custom_kb

from services.db_func import get_user_from_username


async def send_mail(recipient, subject, content):
    logger.debug('Начало отправки почты')
    sender_email = settings.EMAIL_HOST_USER
    password = settings.EMAIL_HOST_PASSWORD
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient
    try:
        text = content
        html = content
        part1 = MIMEText(text, "plain")
        # part2 = MIMEText(html, "html")
        message.attach(part1)
        # message.attach(part2)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.SERVER_EMAIL, settings.EMAIL_PORT, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(
                sender_email, recipient, message.as_string())
        logger.debug('Почта отправлена')
    except SMTPException as e:
        logger.warning(u'Не удалось отправить письмо получателю {} из-за ошибки: {}'.format(recipient, e.strerror))


async def send_tg_message(ids_to_send: list[str], text: str):
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    for tg_id in ids_to_send:
        try:
            await bot.send_message(tg_id, text)
            await asyncio.sleep(0.1)
            logger.info(f'Сообщение {tg_id} отправлено')
        except TelegramForbiddenError as err:
            logger.warning(f'Ошибка отправки сообщения для {tg_id}: {err}')
        except Exception as err:
            logger.error(f'ошибка отправки сообщения пользователю {tg_id}: {err}', exc_info=False)


async def send_obj(obj: ObjModel, bot: Bot):
    logger.debug(f'send_obj: {obj}')
    await bot.send_media_group(chat_id=obj.channel, media=obj.get_media_group())
    now = settings.tz.localize(datetime.datetime.now())
    obj.set('posted_time', now)
    logger.debug(f'posted_time: {now}')


async def send_obj_to_admin(obj, bot: Bot):
    try:
        logger.debug(f'Отправляю админу {settings.ADMIN_IDS[0]}')
        await bot.send_media_group(chat_id=settings.ADMIN_IDS[0], media=obj.get_media_group())
        bns = {'Оставить обычное время': f'obj:{obj.id}:15', 'Отправить сразу': f'obj:{obj.id}:0'}
        kb = custom_kb(1, bns)
        await bot.send_message(
            chat_id=settings.ADMIN_IDS[0],
            text=f'Выберите действие к объявлению {obj.id} от пользователя @{obj.user.username}',
            reply_markup=kb)
        logger.debug('Админу отправлено')
    except Exception as err:
        logger.error(err)




async def main():
    pass


if __name__ == '__main__':
    asyncio.run(main())
