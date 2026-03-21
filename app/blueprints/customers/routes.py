from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.blueprints.customers import customers_bp
from app.models.customer import Customer
from app.extensions import db


# =========================
# PERMISSÕES
# =========================

def can_create_customer():
    return current_user.system_role == "super_admin" or current_user.company_role in [
        "admin_empresa",
        "funcionario",
    ]


def can_edit_customer():
    return current_user.system_role == "super_admin" or current_user.company_role in [
        "admin_empresa",
        "funcionario",
    ]


def can_delete_customer():
    return current_user.system_role == "super_admin" or current_user.company_role == "admin_empresa"


def can_view_customer():
    return current_user.system_role == "super_admin" or current_user.company_role in [
        "admin_empresa",
        "funcionario",
        "visualizador",
    ]


# =========================
# CLIENTES
# =========================

@customers_bp.route("/")
@login_required
def list_customers():
    if not can_view_customer():
        flash("Você não tem permissão para visualizar clientes.", "danger")
        return redirect(url_for("main.dashboard"))

    search = request.args.get("search", "").strip()

    query = Customer.query.filter_by(company_id=current_user.company_id)

    if search:
        query = query.filter(Customer.name.ilike(f"%{search}%"))

    customers = query.order_by(Customer.id.desc()).all()

    return render_template(
        "customers.html",
        customers=customers,
        search=search
    )


@customers_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_customer():
    if not can_create_customer():
        flash("Você não tem permissão para cadastrar clientes.", "danger")
        return redirect(url_for("customers.list_customers"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()

        if not name:
            flash("O nome do cliente é obrigatório.", "danger")
            return render_template("new_customer.html")

        customer = Customer(
            name=name,
            phone=phone or None,
            email=email or None,
            company_id=current_user.company_id
        )

        db.session.add(customer)
        db.session.commit()

        flash("Cliente cadastrado com sucesso.", "success")
        return redirect(url_for("customers.list_customers"))

    return render_template("new_customer.html")


@customers_bp.route("/<int:customer_id>/edit", methods=["GET", "POST"])
@login_required
def edit_customer(customer_id):
    if not can_edit_customer():
        flash("Você não tem permissão para editar clientes.", "danger")
        return redirect(url_for("customers.list_customers"))

    customer = Customer.query.filter_by(
        id=customer_id,
        company_id=current_user.company_id
    ).first_or_404()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()

        if not name:
            flash("O nome do cliente é obrigatório.", "danger")
            return render_template("edit_customer.html", customer=customer)

        customer.name = name
        customer.phone = phone or None
        customer.email = email or None

        db.session.commit()

        flash("Cliente atualizado com sucesso.", "success")
        return redirect(url_for("customers.list_customers"))

    return render_template("edit_customer.html", customer=customer)


@customers_bp.route("/<int:customer_id>/delete", methods=["POST"])
@login_required
def delete_customer(customer_id):
    if not can_delete_customer():
        flash("Você não tem permissão para excluir clientes.", "danger")
        return redirect(url_for("customers.list_customers"))

    customer = Customer.query.filter_by(
        id=customer_id,
        company_id=current_user.company_id
    ).first_or_404()

    db.session.delete(customer)
    db.session.commit()

    flash("Cliente excluído com sucesso.", "success")
    return redirect(url_for("customers.list_customers"))