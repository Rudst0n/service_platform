from flask import Flask
from app.config import Config
from app.extensions import db, migrate, login_manager

from app.models.user import User

from app.blueprints.auth import auth_bp
from app.blueprints.main import main_bp
from app.blueprints.customers import customers_bp
from app.blueprints.users import users_bp


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(users_bp)

    return app