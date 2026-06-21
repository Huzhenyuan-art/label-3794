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

CAPTCHA_TTL_SECONDS = 600
CAPTCHA_THRESHOLD = 2
CAPTCHA_MAX_RETRIES = 10
CAPTCHA_COOLDOWN_SECONDS = 2
CAPTCHA_MAX_VERIFICATIONS = 3


def _generate_code(length: int = 4) -> str:
    chars = string.ascii_uppercase + string.digits
    filtered = chars.replace("O", "").replace("0", "").replace("I", "").replace("1", "").replace("L", "")
    return "".join(random.choices(filtered, k=length))


def _draw_captcha_image(code: str) -> bytes:
    char_count = len(code)
    char_width = 46
    padding_x = 24
    padding_y = 8
    width = padding_x * 2 + char_width * char_count + (char_count - 1) * 4
    height = 64

    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    for _ in range(4):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line(
            [(x1, y1), (x2, y2)],
            fill=(random.randint(200, 230), random.randint(200, 230), random.randint(200, 230)),
            width=1,
        )

    for _ in range(15):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point(
            (x, y),
            fill=(random.randint(180, 220), random.randint(180, 220), random.randint(180, 220)),
        )

    try:
        font = ImageFont.truetype("arial.ttf", 42)
    except OSError:
        try:
            font = ImageFont.truetype("Arial.ttf", 42)
        except OSError:
            font = ImageFont.load_default(size=42)

    bold_colors = [
        (0, 0, 0),
        (30, 30, 80),
        (80, 20, 20),
        (20, 60, 20),
        (60, 20, 80),
        (0, 40, 80),
    ]

    for i, ch in enumerate(code):
        x = padding_x + i * (char_width + 4)
        y = random.randint(padding_y, padding_y + 6)
        color = random.choice(bold_colors)
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
        _captcha_store[captcha_id] = {
            "code": code,
            "expire_at": now + CAPTCHA_TTL_SECONDS,
            "fail_count": 0,
            "last_fail_at": 0.0,
            "success_count": 0,
        }

    return captcha_id, image_bytes


def verify_captcha(captcha_id: Optional[str], user_code: Optional[str]) -> tuple[bool, str]:
    if not captcha_id or not user_code:
        return False, "请输入验证码"

    with _store_lock:
        entry = _captcha_store.get(captcha_id)
        if not entry:
            return False, "验证码已失效，请点击右侧刷新按钮重新获取"

        if entry["expire_at"] < time.time():
            _captcha_store.pop(captcha_id, None)
            return False, "验证码已过期，请点击右侧刷新按钮重新获取"

        if entry["success_count"] >= CAPTCHA_MAX_VERIFICATIONS:
            _captcha_store.pop(captcha_id, None)
            return False, "验证码使用次数过多，请点击右侧刷新按钮重新获取"

        now = time.time()
        if entry["fail_count"] > 0 and now - entry["last_fail_at"] < CAPTCHA_COOLDOWN_SECONDS:
            return False, "操作过于频繁，请稍后重试"

        if user_code.strip().upper() == entry["code"].upper():
            entry["success_count"] += 1
            return True, ""

        entry["fail_count"] += 1
        entry["last_fail_at"] = now

        if entry["fail_count"] >= CAPTCHA_MAX_RETRIES:
            _captcha_store.pop(captcha_id, None)
            return False, "验证码错误次数过多，请点击右侧刷新按钮重新获取"

        remaining = CAPTCHA_MAX_RETRIES - entry["fail_count"]
        return False, f"验证码错误，还可尝试 {remaining} 次，看不清可点击右侧刷新"


def consume_captcha(captcha_id: Optional[str]) -> None:
    if not captcha_id:
        return
    with _store_lock:
        _captcha_store.pop(captcha_id, None)
