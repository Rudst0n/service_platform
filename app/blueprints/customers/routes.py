from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.blueprints.customers import customers_bp
from app.models.customer import Customer
from app.models.service import Service
from app.extensions import db
from app.utils.plan_limits import is_limit_reached
from app.utils.access import block_if_trial_expired
from app.utils.audit import log_action


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


@customers_bp.route("/")
@login_required
def list_customers():
    if not can_view_customer():
        flash("Você não tem permissão para visualizar clientes.", "danger")
        return redirect(url_for("main.dashboard"))

    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)

    query = Customer.query.filter_by(company_id=current_user.company_id)

    if search:
        query = query.filter(Customer.name.ilike(f"%{search}%"))

    pagination = query.order_by(Customer.id.desc()).paginate(page=page, per_page=10, error_out=False)
    customers = pagination.items

    return render_template(
        "customers/customers.html",
        customers=customers,
        search=search,
        pagination=pagination,
    )


@customers_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_customer():
    if not can_create_customer():
        flash("Você não tem permissão para cadastrar clientes.", "danger")
        return redirect(url_for("customers.list_customers"))

    if request.method == "POST":
        trial_block = block_if_trial_expired('clientes')
        if trial_block:
            return trial_block
        if is_limit_reached(current_user.company, Customer, "customers"):
            flash("Você atingiu o limite de clientes do seu plano.", "warning")
            return redirect(url_for("customers.list_customers"))

        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()

        if not name:
            flash("O nome do cliente é obrigatório.", "danger")
            return render_template("customers/new_customer.html")

        customer = Customer(
            name=name,
            phone=phone or None,
            email=email or None,
            company_id=current_user.company_id
        )

        db.session.add(customer)
        log_action('create_customer', 'customer', description=f'Cliente {name} cadastrado.')
        db.session.commit()

        flash('Cliente cadastrado com sucesso.', 'success')
        return redirect(url_for("customers.list_customers"))

    return render_template("customers/new_customer.html")


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
        trial_block = block_if_trial_expired('clientes')
        if trial_block:
            return trial_block
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()

        if not name:
            flash("O nome do cliente é obrigatório.", "danger")
            return render_template("customers/edit_customer.html", customer=customer)

        customer.name = name
        customer.phone = phone or None
        customer.email = email or None

        log_action('update_customer', 'customer', customer.id, f'Cliente {customer.name} atualizado.')
        db.session.commit()

        flash('Cliente atualizado com sucesso.', 'success')
        return redirect(url_for("customers.list_customers"))

    return render_template("customers/edit_customer.html", customer=customer)


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

    linked_services = Service.query.filter_by(
        customer_id=customer.id,
        company_id=current_user.company_id
    ).count()

    if linked_services > 0:
        flash("Não é possível excluir este cliente porque existem serviços vinculados a ele.", "warning")
        return redirect(url_for("customers.list_customers"))

    log_action('delete_customer', 'customer', customer.id, f'Cliente {customer.name} excluído.')
    db.session.delete(customer)
    db.session.commit()

    flash('Cliente excluído com sucesso.', 'success')
    return redirect(url_for("customers.list_customers"))
