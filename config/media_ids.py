"""Хранение file_id медиа (приветственная гифка и т.д.)."""
import json
from pathlib import Path

from config.bot_settings import BASE_DIR

MEDIA_IDS_PATH = BASE_DIR / "media_ids.json"
KEY_WELCOME_ANIMATION = "welcome_animation"


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


def save_welcome_animation_file_id(file_id: str) -> None:
    data = load_media_ids()
    data[KEY_WELCOME_ANIMATION] = file_id
    with open(MEDIA_IDS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
