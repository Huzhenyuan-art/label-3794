import io
import random
import string
import threading
import time
import uuid
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


_captcha_store: dict[str, dict] = {}
_store_lock = threading.Lock()

CAPTCHA_TTL_SECONDS = 300
CAPTCHA_THRESHOLD = 2


def _generate_code(length: int = 4) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


def _draw_captcha_image(code: str) -> bytes:
    width, height = 130, 48
    image = Image.new("RGB", (width, height), (245, 245, 245))
    draw = ImageDraw.Draw(image)

    for _ in range(6):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line(
            [(x1, y1), (x2, y2)],
            fill=(random.randint(150, 200), random.randint(150, 200), random.randint(150, 200)),
            width=1,
        )

    for _ in range(30):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point(
            (x, y),
            fill=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)),
        )

    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except OSError:
        font = ImageFont.load_default()

    for i, ch in enumerate(code):
        x = 18 + i * 28
        y = random.randint(5, 12)
        color = (random.randint(30, 100), random.randint(30, 100), random.randint(30, 100))
        draw.text((x, y), ch, font=font, fill=color)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def create_captcha() -> tuple[str, bytes]:
    code = _generate_code()
    captcha_id = uuid.uuid4().hex
    image_bytes = _draw_captcha_image(code)

    with _store_lock:
        now = time.time()
        for cid in list(_captcha_store.keys()):
            if _captcha_store[cid]["expire_at"] < now:
                del _captcha_store[cid]
        _captcha_store[captcha_id] = {"code": code, "expire_at": now + CAPTCHA_TTL_SECONDS}

    return captcha_id, image_bytes


def verify_captcha(captcha_id: Optional[str], user_code: Optional[str]) -> bool:
    if not captcha_id or not user_code:
        return False

    with _store_lock:
        entry = _captcha_store.pop(captcha_id, None)

    if not entry:
        return False

    if entry["expire_at"] < time.time():
        return False

    return user_code.strip().upper() == entry["code"].upper()
