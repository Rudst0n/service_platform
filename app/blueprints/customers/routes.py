from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.blueprints.customers import customers_bp
from app.models.customer import Customer
from app.models.service import Service
from app.services.customer_service import (
    CustomerService,
    CustomerServiceError,
    CustomerValidationError,
)
from app.utils.permissions import (
    can_create_customer,
    can_edit_customer,
    is_company_admin,
    is_super_admin,
)
from app.utils.plan_limits import is_limit_reached


def can_access_customers_area():
    return (
        is_super_admin()
        or is_company_admin()
        or current_user.company_role == "funcionario"
    )


@customers_bp.route("/")
@login_required
def list_customers():
    if not can_access_customers_area():
        flash("Você não tem permissão para acessar clientes.", "danger")
        return redirect(url_for("main.dashboard"))

    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()

    pagination = CustomerService.list_paginated(
        company_id=current_user.company_id,
        page=page,
        per_page=10,
        search=search,
    )

    return render_template(
        "customers/customers.html",
        customers=pagination.items,
        pagination=pagination,
        search=search,
    )


@customers_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_customer():
    if not can_create_customer():
        flash("Você não tem permissão para cadastrar clientes.", "danger")
        return redirect(url_for("customers.list_customers"))

    form_data = {
        "name": "",
        "phone": "",
        "email": "",
        "cpf": "",
    }

    if request.method == "POST":
        if is_limit_reached(current_user.company, Customer, "customers"):
            flash("Você atingiu o limite de clientes do seu plano.", "warning")
            return redirect(url_for("customers.list_customers"))

        form_data = CustomerService.normalize_form_data(request.form)

        try:
            CustomerService.create_customer(
                data=form_data,
                company_id=current_user.company_id,
                actor_user_id=current_user.id,
            )

            flash("Cliente criado com sucesso.", "success")
            return redirect(url_for("customers.list_customers"))

        except CustomerValidationError as exc:
            flash(str(exc), "danger")

        except CustomerServiceError as exc:
            flash(str(exc), "danger")

    return render_template(
        "customers/new_customer.html",
        form_data=form_data,
    )


@customers_bp.route("/edit/<int:customer_id>", methods=["GET", "POST"])
@login_required
def edit_customer(customer_id):
    if not can_edit_customer():
        flash("Você não tem permissão para editar clientes.", "danger")
        return redirect(url_for("customers.list_customers"))

    customer = CustomerService.get_or_404(
        customer_id=customer_id,
        company_id=current_user.company_id,
    )

    form_data = None

    if request.method == "POST":
        form_data = CustomerService.normalize_form_data(request.form)

        try:
            customer = CustomerService.update_customer(
                customer=customer,
                data=form_data,
                actor_user_id=current_user.id,
            )

            flash("Cliente atualizado com sucesso.", "success")
            return redirect(url_for("customers.list_customers"))

        except CustomerValidationError as exc:
            flash(str(exc), "danger")

        except CustomerServiceError as exc:
            flash(str(exc), "danger")

    return render_template(
        "customers/edit_customer.html",
        customer=customer,
        form_data=form_data,
    )


@customers_bp.route("/delete/<int:customer_id>", methods=["POST"])
@login_required
def delete_customer(customer_id):
    if not (is_company_admin() or is_super_admin()):
        flash("Você não tem permissão para excluir clientes.", "danger")
        return redirect(url_for("customers.list_customers"))

    customer = CustomerService.get_or_404(
        customer_id=customer_id,
        company_id=current_user.company_id,
    )

    try:
        CustomerService.delete_customer(
            customer=customer,
            actor_user_id=current_user.id,
        )
        flash("Cliente excluído com sucesso.", "success")

    except CustomerServiceError as exc:
        flash(str(exc), "danger")

    return redirect(url_for("customers.list_customers"))


@customers_bp.route("/<int:customer_id>")
@login_required
def detail_customer(customer_id):
    if not can_access_customers_area():
        flash("Você não tem permissão para acessar clientes.", "danger")
        return redirect(url_for("main.dashboard"))

    customer = Customer.query.filter_by(
        id=customer_id,
        company_id=current_user.company_id,
    ).first_or_404()

    services = Service.query.filter_by(
        customer_id=customer.id,
        company_id=current_user.company_id,
    ).order_by(Service.created_at.desc()).all()

    return render_template(
        "customers/detail_customer.html",
        customer=customer,
        services=services,
    )