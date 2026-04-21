from datetime import datetime

from flask import flash, redirect, render_template, request, session, url_for

from app.blueprints.client_portal import client_portal_bp
from app.extensions import db
from app.models.customer import Customer
from app.models.service import Service


def get_logged_customer():
    customer_id = session.get("customer_id")

    if not customer_id:
        return None

    return Customer.query.get(customer_id)


def next_request_data(company_id):
    last_service = (
        Service.query
        .filter_by(company_id=company_id)
        .order_by(Service.request_number.desc(), Service.id.desc())
        .first()
    )

    next_number = 1 if not last_service else last_service.request_number + 1
    request_code = f"REQ-{str(next_number).zfill(3)}"

    return next_number, request_code


@client_portal_bp.route("/login", methods=["GET", "POST"])
def login():
    if get_logged_customer():
        return redirect(url_for("client_portal.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        customer = Customer.query.filter(
            db.func.lower(Customer.email) == email
        ).first()

        if not customer:
            flash("Cliente não encontrado.", "danger")
            return render_template("client_portal/login.html")

        if not customer.is_portal_active:
            flash("Seu acesso ao portal está desativado.", "warning")
            return render_template("client_portal/login.html")

        if not customer.check_password(password):
            flash("Senha inválida.", "danger")
            return render_template("client_portal/login.html")

        session["customer_id"] = customer.id
        customer.last_login_at = datetime.utcnow()
        db.session.commit()

        return redirect(url_for("client_portal.dashboard"))

    return render_template("client_portal/login.html")


@client_portal_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("customer_id", None)
    flash("Logout realizado com sucesso.", "success")
    return redirect(url_for("client_portal.login"))


@client_portal_bp.route("/dashboard")
def dashboard():
    customer = get_logged_customer()

    if not customer:
        return redirect(url_for("client_portal.login"))

    services = Service.query.filter_by(
        customer_id=customer.id,
        company_id=customer.company_id
    ).order_by(Service.created_at.desc()).all()

    return render_template(
        "client_portal/dashboard.html",
        customer=customer,
        services=services,
    )


@client_portal_bp.route("/services/new", methods=["GET", "POST"])
def new_service():
    customer = get_logged_customer()

    if not customer:
        return redirect(url_for("client_portal.login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Informe o título da solicitação.", "danger")
            return render_template(
                "client_portal/new_service.html",
                customer=customer
            )

        request_number, request_code = next_request_data(customer.company_id)

        service = Service(
            request_number=request_number,
            request_code=request_code,
            name=name,
            description=description or None,
            price=None,
            status="orcamento",
            customer_id=customer.id,
            company_id=customer.company_id,
            assigned_to_id=None,
            created_by_id=1
        )

        db.session.add(service)
        db.session.commit()

        flash("Solicitação enviada com sucesso.", "success")
        return redirect(url_for("client_portal.dashboard"))

    return render_template(
        "client_portal/new_service.html",
        customer=customer
    )