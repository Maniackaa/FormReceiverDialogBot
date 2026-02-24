import asyncio
import datetime
import pickle
from typing import Sequence

import numpy
from sqlalchemy import select, delete, RowMapping

from config.bot_settings import logger, settings
from database.db import Session, User, ObjModel


def check_user(id):
    """Возвращает найденных пользователей по tg_id"""
    # logger.debug(f'Ищем юзера {id}')
    with Session() as session:
        user: User = session.query(User).filter(User.tg_id == str(id)).one_or_none()
        # logger.debug(f'Результат: {user}')
        return user


def get_user_from_id(pk) -> User:
    session = Session(expire_on_commit=False)
    with session:
        q = select(User).filter(User.id == pk)
        print(q)
        user = session.execute(q).scalars().one_or_none()
        return user


def get_user_from_username(username) -> User:
    session = Session(expire_on_commit=False)
    with session:
        q = select(User).filter(User.username == username)
        user = session.execute(q).scalars().one_or_none()
        return user


def get_or_create_user(user) -> User:
    """Из юзера ТГ возвращает сущестующего User ли создает его"""
    try:
        tg_id = user.id
        username = user.username
        # logger.debug(f'username {username}')
        old_user = check_user(tg_id)
        if old_user:
            # logger.debug('Пользователь есть в базе')
            return old_user
        logger.debug('Добавляем пользователя')
        with Session() as session:
            new_user = User(tg_id=tg_id,
                            username=username,
                            register_date=datetime.datetime.now()
                            )
            session.add(new_user)
            session.commit()
            logger.debug(f'Пользователь создан: {new_user}')
        return new_user
    except Exception as err:
        logger.error('Пользователь не создан', exc_info=True)


def create_obj(user: User, text: str, photos: list, channel: int, target_time: datetime.datetime):
    session = Session(expire_on_commit=False)
    with session:
        new_obj = ObjModel(user=user,
                           text=text,
                           photos=photos,
                           channel=channel,
                           target_time=target_time
                           )
        session.add(new_obj)
        session.commit()
        return new_obj


def get_obj(pk):
    session = Session(expire_on_commit=False)
    with session:
        q = select(ObjModel).where(ObjModel.id == pk)
        result = session.execute(q).scalar_one_or_none()
        return result


def get_objs_to_send() -> Sequence[ObjModel]:
    session = Session(expire_on_commit=False)
    with session:
        now = settings.tz.localize(datetime.datetime.now())
        print(now)
        q = select(ObjModel).where(ObjModel.target_time <= now, ObjModel.posted_time.is_(None))
        result = session.execute(q).scalars().all()
        return result


async def main():
    user = get_user_from_id(1)
    x = get_objs_to_send()
    print(x)

if __name__ == '__main__':
    asyncio.run(main())

