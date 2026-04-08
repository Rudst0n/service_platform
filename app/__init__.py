from datetime import datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.config import config_by_name
from app.extensions import csrf, db, login_manager, migrate
from app.models.company import CompanyStatus
from app.utils.filters import brl, phone_mask
from app.utils.security import format_cnpj, format_cpf


def create_app(config_name="development"):
    app = Flask(__name__, instance_relative_config=True)

    config_class = config_by_name.get(config_name, config_by_name["development"])
    app.config.from_object(config_class)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    register_blueprints(app)
    register_login(app)
    register_context_processors(app)
    register_template_filters(app)
    register_middlewares(app)
    register_error_handlers(app)

    return app


def register_blueprints(app):
    from app.blueprints.admin import admin_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.customers import customers_bp
    from app.blueprints.main import main_bp
    from app.blueprints.protected_uploads import protected_uploads_bp
    from app.blueprints.services import services_bp
    from app.blueprints.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(customers_bp, url_prefix="/customers")
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(services_bp, url_prefix="/services")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(protected_uploads_bp, url_prefix="/uploads")


def register_login(app):
    from app.models.user import User

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para continuar."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


def register_context_processors(app):
    @app.context_processor
    def inject_globals():
        return {
            "app_name": app.config.get("APP_NAME"),
            "app_slogan": app.config.get("APP_SLOGAN"),
            "support_whatsapp": app.config.get("SUPPORT_WHATSAPP"),
            "support_email": app.config.get("SUPPORT_EMAIL"),
            "support_instagram": app.config.get("SUPPORT_INSTAGRAM"),
        }


def register_template_filters(app):
    @app.template_filter("cpf_mask")
    def cpf_mask(value):
        return format_cpf(value) if value else "-"

    @app.template_filter("cnpj_mask")
    def cnpj_mask(value):
        return format_cnpj(value) if value else "-"

    @app.template_filter("brl")
    def brl_filter(value):
        return brl(value)

    @app.template_filter("phone_mask")
    def phone_mask_filter(value):
        return phone_mask(value)


def register_middlewares(app):

    @app.before_request
    def enforce_company_access():
        if not current_user.is_authenticated:
            return None

        public_endpoints = {
            "auth.login",
            "auth.register",
            "auth.confirm_email",
            "auth.forgot_password",
            "auth.reset_password",
            "static",
        }

        if request.endpoint in public_endpoints:
            return None

        company = current_user.company

        if not company:
            flash("Usuário sem empresa vinculada.", "danger")
            return redirect(url_for("main.dashboard"))

        if not company.is_access_allowed:
            if company.status == CompanyStatus.PENDING:
                flash("Sua empresa ainda está pendente de liberação.", "warning")
            elif company.status == CompanyStatus.INACTIVE:
                flash("Sua empresa está inativa no momento.", "warning")
            elif company.status == CompanyStatus.BLOCKED:
                flash("Sua empresa foi bloqueada. Entre em contato com o suporte.", "danger")
            else:
                flash("Sua empresa não possui acesso liberado no momento.", "warning")

            return redirect(url_for("main.dashboard"))

        return None

    @app.after_request
    def update_last_activity(response):
        if current_user.is_authenticated:
            try:
                company = current_user.company
                if company:
                    now = datetime.utcnow()

                    if (
                        not company.last_activity_at
                        or (now - company.last_activity_at).total_seconds() > 900
                    ):
                        company.last_activity_at = now
                        db.session.commit()
            except Exception:
                db.session.rollback()

        return response


def register_error_handlers(app):

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500