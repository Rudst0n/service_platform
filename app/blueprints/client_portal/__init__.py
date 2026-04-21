from flask import Blueprint

client_portal_bp = Blueprint("client_portal", __name__)

from app.blueprints.client_portal import routes