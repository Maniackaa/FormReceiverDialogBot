"""Хранение file_id медиа (приветственная гифка и т.д.)."""
import json
from pathlib import Path

from config.bot_settings import BASE_DIR

MEDIA_IDS_PATH = BASE_DIR / "media_ids.json"
KEY_WELCOME_ANIMATION = "welcome_animation"  # legacy
KEY_WELCOME_MEDIA = "welcome_media"

ATM_PHOTO_FILE_IDS = [
    "AgACAgIAAxkBAALA_mozwGLNnaIrygwqyD5BpbYb7PBIAAI3GWsbLF6RSbSK-5OKbarqAQADAgADeQADPAQ",
    "AgACAgIAAxkBAALBAAFqM8CBGa4zMSMZ4HUJdQ_rmiozhQACOBlrGyxekUmk3i2eW6qnlQEAAwIAA3kAAzwE",
    "AgACAgIAAxkBAALBAmozwI5WwgQQKU6lbUuJ3--A5V5XAAI5GWsbLF6RSWAHB2YGqik2AQADAgADeQADPAQ",
]
ATM_PHOTO_PATHS = [
    BASE_DIR / "media" / "cash1.jpg",
    BASE_DIR / "media" / "cash2.jpg",
    BASE_DIR / "media" / "cash3.jpg",
]

# Типы для welcome_media["type"] — совпадают с ContentType.value в aiogram
WELCOME_TYPE_ANIMATION = "animation"
WELCOME_TYPE_PHOTO = "photo"
WELCOME_TYPE_VIDEO = "video"
WELCOME_TYPE_DOCUMENT = "document"


def load_media_ids() -> dict:
    if not MEDIA_IDS_PATH.exists():
        return {}
    try:
        with open(MEDIA_IDS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write_media_ids(data: dict) -> None:
    with open(MEDIA_IDS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_welcome_media() -> tuple[str | None, str | None]:
    """file_id и тип (animation / photo / video / document)."""
    data = load_media_ids()
    stored = data.get(KEY_WELCOME_MEDIA)
    if isinstance(stored, dict):
        file_id = stored.get("file_id")
        media_type = stored.get("type") or WELCOME_TYPE_ANIMATION
        if file_id:
            return file_id, media_type
    legacy = data.get(KEY_WELCOME_ANIMATION)
    if legacy:
        return legacy, WELCOME_TYPE_ANIMATION
    return None, None


def get_welcome_animation_file_id() -> str | None:
    file_id, _ = get_welcome_media()
    return file_id


def get_atm_photo_file_ids() -> list[str]:
    return ATM_PHOTO_FILE_IDS


def get_atm_photo_paths() -> list[Path]:
    return ATM_PHOTO_PATHS


def save_welcome_media(file_id: str, media_type: str) -> None:
    data = load_media_ids()
    data[KEY_WELCOME_MEDIA] = {"file_id": file_id, "type": media_type}
    data.pop(KEY_WELCOME_ANIMATION, None)
    _write_media_ids(data)


def save_welcome_animation_file_id(file_id: str) -> None:
    save_welcome_media(file_id, WELCOME_TYPE_ANIMATION)


def clear_welcome_media() -> None:
    data = load_media_ids()
    data.pop(KEY_WELCOME_MEDIA, None)
    data.pop(KEY_WELCOME_ANIMATION, None)
    _write_media_ids(data)


def fix_welcome_media_type_from_telegram_error(error_message: str) -> bool:
    """Если Telegram пишет «Photo as Animation» — сохраняем правильный тип и возвращаем True."""
    msg = error_message.lower()
    if "can't use file of type" not in msg:
        return False

    type_aliases = {
        "photo": WELCOME_TYPE_PHOTO,
        "video": WELCOME_TYPE_VIDEO,
        "animation": WELCOME_TYPE_ANIMATION,
        "document": WELCOME_TYPE_DOCUMENT,
        "audio": WELCOME_TYPE_DOCUMENT,
        "voice": WELCOME_TYPE_DOCUMENT,
    }
    actual_type = None
    for name, stored in type_aliases.items():
        if f"file of type {name}" in msg:
            actual_type = stored
            break
    if not actual_type:
        return False

    file_id, _ = get_welcome_media()
    if not file_id:
        return False

    save_welcome_media(file_id, actual_type)
    return True
