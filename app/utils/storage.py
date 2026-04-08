import uuid
from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_private_file(file_storage, subfolder=""):
    if not file_storage or not file_storage.filename:
        raise ValueError("Arquivo inválido.")

    if not allowed_file(file_storage.filename):
        raise ValueError("Tipo de arquivo não permitido.")

    original_name = secure_filename(file_storage.filename)
    extension = original_name.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{extension}"

    upload_root = Path(current_app.config["UPLOAD_FOLDER"])
    destination_dir = upload_root / subfolder if subfolder else upload_root
    destination_dir.mkdir(parents=True, exist_ok=True)

    final_path = destination_dir / unique_name
    file_storage.save(final_path)

    relative_path = str((Path(subfolder) / unique_name) if subfolder else unique_name)
    return relative_path.replace("\\", "/")