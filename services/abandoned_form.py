"""Неоконченные заявки: через N секунд после начала отправка уведомления в ABANDONED_CHANNEL."""
from __future__ import annotations

import asyncio
import html
import uuid
from typing import Any

from aiogram import Bot
from aiogram.types import User

from config.bot_settings import logger, settings

ABANDON_FORM_DELAY_SEC = 180

_LABELS: dict[str, str] = {
    "city_id": "город (id)",
    "city_str": "город",
    "currency_id": "валюта (id)",
    "currency_str": "направление обмена",
    "price": "сумма",
    "value": "сумма к получению (₫)",
    "koef": "коэффициент",
    "banks_id": "банк (id)",
    "banks_str": "банк",
    "bank": "банк (свой ввод)",
    "sbp_id": "СБП (id)",
    "sbp_str": "СБП",
    "net_id": "сеть (id)",
    "net_str": "сеть",
    "net": "сеть / кошелёк",
    "location": "локация / отель",
    "info": "комментарий",
    "result_text": "черновик заявки",
    "count": "№ счётчика черновика",
    "channel_id": "пункт меню",
}


_token_by_uid: dict[int, str] = {}
_snapshot_by_uid: dict[int, dict[str, Any]] = {}


def cancel_abandon_form_tracking(user_id: int) -> None:
    """Сброс только когда заявка реально отправлена (Подтвердить).

    Выход через «Сначала», «Отменить», /start и т.п. считается недооформленной заявкой —
    напоминание в канал по таймеру должно сохраниться.
    """
    _token_by_uid.pop(user_id, None)
    _snapshot_by_uid.pop(user_id, None)


def refresh_abandon_form_snapshot(user_id: int, dialog_data: dict) -> None:
    """Актуальные ответы формы (вызывается из getter диалога)."""
    snap: dict[str, Any] = {}
    skip = {"getter", "convertation", "minimum_post"}
    for k, v in dialog_data.items():
        if k in skip:
            continue
        if k == "currency" and isinstance(v, list):
            continue
        try:
            if isinstance(v, (dict, list, tuple)):
                snap[k] = repr(v)
            else:
                snap[k] = v
        except Exception:
            snap[k] = "<…>"
    _snapshot_by_uid[user_id] = snap


def _format_snapshot_block(snap: dict[str, Any]) -> str:
    if not snap:
        return "Данные формы не заполнены (пользователь на первом шаге или только открыл заявку)."

    lines: list[str] = []
    # Стабильный порядок: сначала известные поля, затем прочее
    keys = sorted(snap.keys(), key=lambda x: (_LABELS.get(x) is None, x))
    for key in keys:
        label = _LABELS.get(key, key)
        val = snap[key]
        sval = html.escape(str(val)) if val is not None else "—"
        if len(sval) > 1500:
            sval = sval[:1497] + "…"
        lines.append(f"• <b>{html.escape(label)}:</b> {sval}")
    return "\n".join(lines)


def format_abandon_message(user: User, snapshot: dict[str, Any]) -> str:
    parts = [
        "⚠️ <b>Заявка не завершена</b> (нет подтверждения более 3 мин.)",
        "",
        "<b>Telegram-профиль</b>",
        f"• <b>id:</b> <code>{user.id}</code>",
    ]
    username = getattr(user, "username", None) or None
    if username:
        parts.append(f'• <b>username:</b> @{html.escape(username)}')
    else:
        parts.append("• <b>username:</b> не указан (профиль без @username)")
    parts.append(f'• <b>имя:</b> {html.escape(user.first_name or "—")}')
    ln = getattr(user, "last_name", None)
    if ln:
        parts.append(f"• <b>фамилия:</b> {html.escape(ln)}")
    lang = getattr(user, "language_code", None)
    if lang:
        parts.append(f"• <b>язык:</b> <code>{html.escape(lang)}</code>")
    if getattr(user, "is_premium", False):
        parts.append("• <b>Telegram Premium:</b> да")
    parts.extend(["", "<b>Введённые данные по форме (на момент таймаута)</b>", _format_snapshot_block(snapshot)])
    return "\n".join(parts)


def arm_abandon_form_tracking(bot: Bot, user: User) -> None:
    uid = user.id
    token = uuid.uuid4().hex
    _token_by_uid[uid] = token

    async def _waiter() -> None:
        try:
            await asyncio.sleep(ABANDON_FORM_DELAY_SEC)
            if _token_by_uid.get(uid) != token:
                return

            snapshot = dict(_snapshot_by_uid.get(uid) or {})

            if settings.ABANDONED_CHANNEL is None:
                logger.warning(
                    "ABANDONED_CHANNEL не задан — уведомление о незавершённой заявке не отправлено",
                    user_id=uid,
                )
                return

            msg = format_abandon_message(user, snapshot)
            await bot.send_message(
                chat_id=settings.ABANDONED_CHANNEL,
                text=msg,
                disable_web_page_preview=True,
            )
            logger.info("Abandoned form notice sent", user_id=uid, channel=settings.ABANDONED_CHANNEL)
        except Exception as err:
            logger.error("Не удалось отправить уведомление о незавершённой форме", exc_info=True)
            logger.debug(str(err))
        finally:
            if _token_by_uid.get(uid) == token:
                _token_by_uid.pop(uid, None)
                _snapshot_by_uid.pop(uid, None)

    asyncio.create_task(_waiter())
