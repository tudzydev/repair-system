"""ฟังก์ชันช่วย: เลขใบแจ้งซ่อมและการตรวจสอบไฟล์ภาพ."""
from datetime import datetime
from pathlib import Path
from uuid import uuid4
import warnings

from flask import current_app
from PIL import Image, UnidentifiedImageError
from sqlalchemy.dialects.sqlite import insert
from werkzeug.utils import secure_filename

from models import db, RequestCounter


def generate_request_no(sequence_number: int, now=None) -> str:
    now = now or datetime.now()
    if not 1 <= sequence_number <= 999:
        raise ValueError("รูปแบบเลข 3 หลักรองรับสูงสุด 999 ใบต่อเดือน")
    return f"RP-{now:%Y%m}-{str(sequence_number).zfill(3)}"


def next_request_no() -> str:
    now = datetime.now()
    stmt = insert(RequestCounter).values(month=now.strftime("%Y%m"), sequence=1)
    stmt = stmt.on_conflict_do_update(
        index_elements=[RequestCounter.month],
        set_={"sequence": RequestCounter.sequence + 1},
    ).returning(RequestCounter.sequence)
    sequence = db.session.execute(stmt).scalar_one()
    # ตัวนับและใบแจ้งซ่อมจะ commit ใน transaction เดียวกันที่ route
    return generate_request_no(sequence, now)


def save_image(file) -> str:
    safe_name = secure_filename(file.filename or "")
    extension = Path(safe_name).suffix.lower()
    formats = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".gif": "GIF"}
    if extension not in formats:
        raise ValueError("อนุญาตเฉพาะไฟล์ JPG, PNG และ GIF")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(file.stream)
            if image.format != formats[extension]:
                raise ValueError("เนื้อหาไฟล์ไม่ตรงกับนามสกุลภาพ")
            image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise ValueError("ไฟล์ภาพไม่ถูกต้องหรือมีขนาดพิกเซลใหญ่เกินไป") from exc
    file.stream.seek(0)
    filename = f"{uuid4().hex}{extension}"
    file.save(Path(current_app.config["UPLOAD_FOLDER"]) / filename)
    return filename
