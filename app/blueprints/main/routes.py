from flask import render_template
from flask_login import login_required, current_user
from app.blueprints.main import main_bp
from app.models.customer import Customer


@main_bp.route("/")
def landing_page():
    return render_template("landing.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    total_customers = Customer.query.filter_by(company_id=current_user.company_id).count()

    return render_template(
        "home.html",
        total_customers=total_customers,
        company=current_user.company
    )