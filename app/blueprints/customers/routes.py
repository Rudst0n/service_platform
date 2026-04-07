from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.blueprints.customers import customers_bp
from app.services.customer_service import (
    CustomerService,
    CustomerServiceError,
    CustomerValidationError,
)
from app.utils.permissions import require_company_role


@customers_bp.route("/")
@login_required
def list_customers():
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
@require_company_role("admin_empresa", "funcionario")
def new_customer():
    form_data = {
        "name": "",
        "phone": "",
        "email": "",
    }

    if request.method == "POST":
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

    return render_template("customers/new_customer.html", form_data=form_data)


@customers_bp.route("/edit/<int:customer_id>", methods=["GET", "POST"])
@login_required
@require_company_role("admin_empresa", "funcionario")
def edit_customer(customer_id):
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
@require_company_role("admin_empresa")
def delete_customer(customer_id):
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