from pathlib import Path

from flask import Blueprint, abort, current_app, send_file
from flask_login import current_user, login_required

from app.models.service_image import ServiceImage

protected_uploads_bp = Blueprint("protected_uploads", __name__)


def user_can_access_service(service):
    if not current_user.is_authenticated:
        return False

    if getattr(current_user, "system_role", None) == "super_admin":
        return True

    if getattr(current_user, "company_id", None) != getattr(service, "company_id", None):
        return False

    return True


@protected_uploads_bp.route("/service-image/<int:image_id>")
@login_required
def service_image(image_id):
    image = ServiceImage.query.get_or_404(image_id)
    service = image.service

    if not user_can_access_service(service):
        abort(403)

    full_path = Path(current_app.config["UPLOAD_FOLDER"]) / image.file_path

    if not full_path.exists() or not full_path.is_file():
        abort(404)

    return send_file(full_path)