import os
import secrets
import shutil
import time
import zipfile
from pathlib import Path

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from ..errors import ApiError


def _extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def _file_size(file_storage: FileStorage) -> int:
    stream = file_storage.stream
    current = stream.tell()
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(current, os.SEEK_SET)
    return size


def _ensure_safe_main_page(main_page: str) -> None:
    if ".." in main_page or main_page.startswith("/"):
        raise ApiError(400, "主页面路径非法")


def _validate_extension(ext: str, allowed_extensions: list[str], blocked_extensions: list[str]) -> None:
    if ext in blocked_extensions:
        raise ApiError(400, f"禁止上传高危文件类型: {ext}")
    if ext not in allowed_extensions:
        raise ApiError(400, f"文件类型不被允许: {ext}")


def _validate_binary_signature(file_storage: FileStorage) -> None:
    stream = file_storage.stream
    current = stream.tell()
    stream.seek(0)
    header = stream.read(4)
    stream.seek(current)
    if header.startswith(b"MZ"):
        raise ApiError(400, "检测到可执行文件签名，已拒绝上传")


def _validate_mime_type(mime_type: str, allowed_mime_types: list[str]) -> None:
    if not allowed_mime_types:
        return

    normalized = (mime_type or "").lower()
    if normalized == "application/octet-stream":
        return

    # PHP 文件 MIME 类型通常被浏览器标记为多种变体，统一放行
    php_mime_types = {
        "application/x-httpd-php",
        "application/x-php",
        "application/php",
        "text/x-php",
        "text/php",
    }
    if normalized in php_mime_types:
        return

    for allowed in allowed_mime_types:
        allowed_lower = allowed.lower().strip()
        if not allowed_lower:
            continue
        if allowed_lower.endswith("/*") and normalized.startswith(allowed_lower[:-1]):
            return
        if normalized == allowed_lower:
            return

    raise ApiError(400, f"MIME 类型不被允许: {mime_type}")


def _create_unique_folder(upload_root: str) -> tuple[str, str]:
    timestamp = int(time.time())
    random_suffix = secrets.token_hex(3)
    folder_name = f"{timestamp}-{random_suffix}"
    folder_path = os.path.join(upload_root, folder_name)
    os.makedirs(folder_path, exist_ok=False)
    return folder_name, folder_path


def _extract_zip(zip_path: str, target_dir: str, allowed_extensions: list[str], blocked_extensions: list[str]) -> None:
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        for member in zip_ref.infolist():
            member_name = member.filename.replace("\\", "/")
            if member.is_dir():
                continue
            if ".." in member_name.split("/"):
                raise ApiError(400, "压缩包包含非法路径")

            ext = _extension(member_name)
            _validate_extension(ext, allowed_extensions, blocked_extensions)

            output_path = os.path.normpath(os.path.join(target_dir, member_name))
            target_root = os.path.abspath(target_dir)
            if not output_path.startswith(target_root):
                raise ApiError(400, "压缩包路径越界")

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with zip_ref.open(member, "r") as src, open(output_path, "wb") as dst:
                shutil.copyfileobj(src, dst)


def store_uploaded_assets(
    upload_file: FileStorage,
    upload_root: str,
    main_page: str,
    allowed_extensions: list[str],
    allowed_mime_types: list[str],
    blocked_extensions: list[str],
    max_size_bytes: int,
) -> tuple[str, str, str]:
    _ensure_safe_main_page(main_page)

    os.makedirs(upload_root, exist_ok=True)

    filename = secure_filename(upload_file.filename or "")
    if not filename:
        raise ApiError(400, "上传文件名不能为空")

    file_ext = _extension(filename)
    _validate_extension(file_ext, allowed_extensions, blocked_extensions)
    _validate_mime_type(upload_file.mimetype, allowed_mime_types)

    size = _file_size(upload_file)
    if size > max_size_bytes:
        raise ApiError(400, f"上传文件超过限制，最大允许 {max_size_bytes // (1024 * 1024)}MB")

    _validate_binary_signature(upload_file)

    folder_name, folder_path = _create_unique_folder(upload_root)

    try:
        if file_ext == "zip":
            zip_path = os.path.join(folder_path, filename)
            upload_file.save(zip_path)
            _extract_zip(zip_path, folder_path, allowed_extensions, blocked_extensions)
            os.remove(zip_path)
        else:
            target_file = os.path.join(folder_path, filename)
            upload_file.save(target_file)

        main_page_path = os.path.join(folder_path, main_page)
        if not os.path.isfile(main_page_path):
            raise ApiError(400, f"主页面 {main_page} 不存在，请确认压缩包内路径")

        storage_folder = os.path.join("static", "pages", folder_name)
        route_path = f"/pages/{folder_name}/{main_page}"
        return folder_name, storage_folder, route_path
    except Exception:
        shutil.rmtree(folder_path, ignore_errors=True)
        raise


def delete_assets(upload_root: str, storage_folder: str) -> None:
    abs_path = os.path.abspath(os.path.join(upload_root, os.path.basename(storage_folder)))
    upload_root_abs = os.path.abspath(upload_root)
    if abs_path.startswith(upload_root_abs) and os.path.exists(abs_path):
        shutil.rmtree(abs_path, ignore_errors=True)
