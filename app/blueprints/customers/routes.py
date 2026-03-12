from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.blueprints.customers import customers_bp
from app.models.customer import Customer
from app.extensions import db


@customers_bp.route("/")
@login_required
def list_customers():
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

    if request.method == "POST":

        name = request.form.get("name")
        phone = request.form.get("phone")
        email = request.form.get("email")

        if not name:
            flash("O nome do cliente é obrigatório.", "danger")
            return render_template("new_customer.html")

        customer = Customer(
            name=name,
            phone=phone,
            email=email,
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
    customer = Customer.query.filter_by(
        id=customer_id,
        company_id=current_user.company_id
    ).first_or_404()

    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        email = request.form.get("email")

        if not name:
            flash("O nome do cliente é obrigatório.", "danger")
            return render_template("edit_customer.html", customer=customer)

        customer.name = name
        customer.phone = phone
        customer.email = email

        db.session.commit()

        flash("Cliente atualizado com sucesso.", "success")
        return redirect(url_for("customers.list_customers"))

    return render_template("edit_customer.html", customer=customer)


@customers_bp.route("/<int:customer_id>/delete", methods=["POST"])
@login_required
def delete_customer(customer_id):

    customer = Customer.query.filter_by(
        id=customer_id,
        company_id=current_user.company_id
    ).first_or_404()

    db.session.delete(customer)
    db.session.commit()

    flash("Cliente excluído com sucesso.", "success")
    return redirect(url_for("customers.list_customers"))