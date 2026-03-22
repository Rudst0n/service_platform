from flask import Blueprint

services_bp = Blueprint("services", __name__, url_prefix="/services")

from app.blueprints.services import routes