import io
import logging
import os
from urllib.parse import urljoin

import qrcode
from flask import current_app

logger = logging.getLogger(__name__)

QRCODE_FOLDER = "qrcodes"


def _get_qrcode_storage_path() -> str:
    upload_root = current_app.config["UPLOAD_ROOT"]
    qrcode_dir = os.path.join(os.path.dirname(upload_root), QRCODE_FOLDER)
    os.makedirs(qrcode_dir, exist_ok=True)
    return qrcode_dir


def generate_qrcode_image(url: str, file_name: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    qrcode_dir = _get_qrcode_storage_path()
    if not file_name.lower().endswith(".png"):
        file_name = f"{file_name}.png"
    file_path = os.path.join(qrcode_dir, file_name)

    img.save(file_path, format="PNG")
    logger.info("二维码已生成: %s", file_path)
    return file_path


def get_qrcode_url(file_name: str) -> str:
    if not file_name.lower().endswith(".png"):
        file_name = f"{file_name}.png"
    return f"/static/qrcodes/{file_name}"


def get_qrcode_absolute_url(request_base_url: str, file_name: str) -> str:
    relative_url = get_qrcode_url(file_name)
    return urljoin(request_base_url, relative_url)


def delete_qrcode(file_name: str) -> None:
    if not file_name:
        return
    if not file_name.lower().endswith(".png"):
        file_name = f"{file_name}.png"
    qrcode_dir = _get_qrcode_storage_path()
    file_path = os.path.join(qrcode_dir, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info("二维码已删除: %s", file_path)


def get_qrcode_image_bytes(url: str) -> bytes:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
