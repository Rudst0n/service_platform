from datetime import datetime
import os

from flask import Flask, request, redirect, url_for, flash, render_template
from werkzeug.exceptions import RequestEntityTooLarge
from flask_login import current_user, logout_user

from app.config import config_by_name
from app.extensions import db, migrate, login_manager, csrf
from app.models.user import User
from app.models.company import CompanyStatus
from app.cli import create_super_admin
from app.utils.filters import brl

from app.blueprints.auth import auth_bp
from app.blueprints.main import main_bp
from app.blueprints.customers import customers_bp
from app.blueprints.users import users_bp
from app.blueprints.services import services_bp
from app.blueprints.admin import admin_bp


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app():
    app = Flask(__name__)
    env_name = os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(env_name, config_by_name["development"]))

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    @app.template_filter("cpf_mask")
    def cpf_mask(value):
        if not value:
            return ""

        digits = "".join(filter(str.isdigit, str(value)))

        if len(digits) != 11:
            return value

        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"

    @app.before_request
    def enforce_company_access_and_track_activity():
        if not request.endpoint:
            return None

        if request.endpoint.startswith("static") or request.endpoint == "auth.logout":
            return None

        if not current_user.is_authenticated:
            return None

        if not getattr(current_user, "is_active", False):
            logout_user()
            flash("Seu usuário está inativo.", "warning")
            return redirect(url_for("auth.login"))

        company = getattr(current_user, "company", None)
        if not company:
            logout_user()
            flash("Usuário sem empresa vinculada.", "danger")
            return redirect(url_for("auth.login"))

        if not company.is_active or company.status != CompanyStatus.ACTIVE:
            logout_user()
            if company.status == CompanyStatus.PENDING:
                flash("Sua empresa ainda está pendente de liberação.", "warning")
            elif company.status == CompanyStatus.INACTIVE:
                flash("Sua empresa está inativa no momento.", "warning")
            elif company.status == CompanyStatus.BLOCKED:
                flash("Sua empresa foi bloqueada. Entre em contato com o suporte.", "danger")
            else:
                flash("Sua empresa não possui acesso liberado no momento.", "warning")
            return redirect(url_for("auth.login"))

        now = datetime.utcnow()
        if not company.last_activity_at or (now - company.last_activity_at).total_seconds() >= 900:
            company.last_activity_at = now
            db.session.commit()

        return None

    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(error):
        flash("Arquivo muito grande. O limite permitido é de 5 MB.", "danger")
        return redirect(request.referrer or url_for("main.dashboard"))

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(admin_bp)

    app.jinja_env.filters["brl"] = brl

    @app.after_request
    def apply_security_headers(response):
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

    @app.context_processor
    def inject_app_context():
        return {
            "app_name": app.config.get("APP_NAME", "ServHub"),
            "app_slogan": app.config.get("APP_SLOGAN", ""),
            "support_whatsapp": app.config.get("SUPPORT_WHATSAPP", ""),
            "support_email": app.config.get("SUPPORT_EMAIL", ""),
            "support_instagram": app.config.get("SUPPORT_INSTAGRAM", ""),
        }

    app.cli.add_command(create_super_admin)

    return app