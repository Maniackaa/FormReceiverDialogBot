import json
import math, tempfile, os
from config.bot_settings import BASE_DIR, logger
from pathlib import Path

def positive_int_check(text: str) -> str:
    if all(ch.isdigit() for ch in text) and 0 <= int(text):
        return text
    raise ValueError


def tel_check(text: str) -> str:
    digits = [x for x in text if x.isdigit()]
    if len(digits) < 5 or len(digits) > 12:
        raise ValueError
    return text


# def conv_check(text: str) -> str:
#     try:
#         v1, v2, v3, v4, v5 = text.split(';')
#         with open(BASE_DIR / 'conv.ini', 'w') as file:
#             file.write(json.dumps([(float(v1), float(v2)), float(v3), float(v4), float(v5)]))
#         return text
#     except Exception as err:
#         logger.error(err)
#         raise ValueError


def _atomic_write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)  # атомарная подмена
    except Exception:
        try: os.remove(tmp)
        except OSError: pass
        raise


def conv_check(text: str) -> str:
    # 1) Парсинг и строгая валидация
    parts = [p.strip() for p in text.split(';')]
    if len(parts) != 5:
        raise ValueError("Ожидалось 5 чисел через ';'")

    try:
        v1, v2, v3, v4, v5 = (float(x) for x in parts)
    except ValueError as e:
        raise ValueError(f"Не удалось преобразовать к числу: {e}")

    # Запретим NaN/Inf, чтобы не получить нестандартный JSON
    nums = [v1, v2, v3, v4, v5]
    if any(math.isnan(x) or math.isinf(x) for x in nums):
        raise ValueError("Значения не должны быть NaN/Infinity")

    data = [(v1, v2), v3, v4, v5]   # tuple сохранится как JSON-массив

    path = BASE_DIR / "conv.ini"
    # 2) Атомарная запись
    _atomic_write_json(path, data)

    return text
