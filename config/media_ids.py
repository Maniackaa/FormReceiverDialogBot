"""Хранение file_id медиа (приветственная гифка и т.д.)."""
import json
from pathlib import Path

from config.bot_settings import BASE_DIR

MEDIA_IDS_PATH = BASE_DIR / "media_ids.json"
KEY_WELCOME_ANIMATION = "welcome_animation"

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


def load_media_ids() -> dict:
    if not MEDIA_IDS_PATH.exists():
        return {}
    try:
        with open(MEDIA_IDS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def get_welcome_animation_file_id() -> str | None:
    return load_media_ids().get(KEY_WELCOME_ANIMATION)


def get_atm_photo_file_ids() -> list[str]:
    return ATM_PHOTO_FILE_IDS


def get_atm_photo_paths() -> list[Path]:
    return ATM_PHOTO_PATHS


def save_welcome_animation_file_id(file_id: str) -> None:
    data = load_media_ids()
    data[KEY_WELCOME_ANIMATION] = file_id
    with open(MEDIA_IDS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
