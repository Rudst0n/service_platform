from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.blueprints.customers import customers_bp
from app.models.customer import Customer
from app.models.user import User
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


def can_manage_users():
    return current_user.system_role == "super_admin" or current_user.company_role == "admin_empresa"


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


# =========================
# USUÁRIOS
# =========================

@customers_bp.route("/users")
@login_required
def list_users():
    if not can_manage_users():
        flash("Você não tem permissão para gerenciar usuários.", "danger")
        return redirect(url_for("main.dashboard"))

    users = (
        User.query
        .filter_by(company_id=current_user.company_id)
        .order_by(User.name.asc())
        .all()
    )

    return render_template("users.html", users=users)


@customers_bp.route("/users/new", methods=["GET", "POST"])
@login_required
def new_user():
    if not can_manage_users():
        flash("Você não tem permissão para cadastrar usuários.", "danger")
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        cpf = request.form.get("cpf", "").strip()
        password = request.form.get("password", "").strip()
        company_role = request.form.get("company_role", "").strip()

        allowed_roles = ["admin_empresa", "funcionario", "visualizador"]

        if not name or not email or not password:
            flash("Nome, e-mail e senha são obrigatórios.", "danger")
            return render_template("new_user.html")

        if company_role not in allowed_roles:
            flash("Perfil de usuário inválido.", "danger")
            return render_template("new_user.html")

        if User.query.filter_by(email=email).first():
            flash("Já existe um usuário com esse e-mail.", "warning")
            return render_template("new_user.html")

        if cpf and User.query.filter_by(cpf=cpf).first():
            flash("Já existe um usuário com esse CPF.", "warning")
            return render_template("new_user.html")

        user = User(
            name=name,
            email=email,
            cpf=cpf or None,
            system_role="company_user",
            company_role=company_role,
            company_id=current_user.company_id,
            is_active=True
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("Usuário cadastrado com sucesso.", "success")
        return redirect(url_for("customers.list_users"))

    return render_template("new_user.html")


@customers_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    if not can_manage_users():
        flash("Você não tem permissão.", "danger")
        return redirect(url_for("main.dashboard"))

    user = User.query.filter_by(
        id=user_id,
        company_id=current_user.company_id
    ).first_or_404()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        cpf = request.form.get("cpf", "").strip() or None

        if not name or not email:
            flash("Nome e e-mail são obrigatórios.", "danger")
            return render_template("edit_user.html", user=user)

        email_exists = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()
        if email_exists:
            flash("Já existe outro usuário com esse e-mail.", "warning")
            return render_template("edit_user.html", user=user)

        if cpf:
            cpf_exists = User.query.filter(
                User.cpf == cpf,
                User.id != user.id
            ).first()
            if cpf_exists:
                flash("Já existe outro usuário com esse CPF.", "warning")
                return render_template("edit_user.html", user=user)

        user.name = name
        user.email = email
        user.cpf = cpf

        db.session.commit()

        flash("Usuário atualizado com sucesso.", "success")
        return redirect(url_for("customers.list_users"))

    return render_template("edit_user.html", user=user)


@customers_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
def update_user_role(user_id):
    if not can_manage_users():
        flash("Você não tem permissão.", "danger")
        return redirect(url_for("main.dashboard"))

    user = User.query.filter_by(
        id=user_id,
        company_id=current_user.company_id
    ).first_or_404()

    new_role = request.form.get("company_role", "").strip()

    allowed_roles = ["admin_empresa", "funcionario", "visualizador"]

    if new_role not in allowed_roles:
        flash("Perfil inválido.", "danger")
        return redirect(url_for("customers.list_users"))

    if user.id == current_user.id and new_role != "admin_empresa":
        flash("Você não pode remover seu próprio acesso de admin.", "warning")
        return redirect(url_for("customers.list_users"))

    user.company_role = new_role
    db.session.commit()

    flash("Perfil atualizado com sucesso.", "success")
    return redirect(url_for("customers.list_users"))


@customers_bp.route("/users/<int:user_id>/reset-password", methods=["GET", "POST"])
@login_required
def reset_user_password(user_id):
    if not can_manage_users():
        flash("Você não tem permissão para resetar senha.", "danger")
        return redirect(url_for("main.dashboard"))

    user = User.query.filter_by(
        id=user_id,
        company_id=current_user.company_id
    ).first_or_404()

    if request.method == "POST":
        new_password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not new_password or not confirm_password:
            flash("Preencha os dois campos de senha.", "danger")
            return render_template("reset_user_password.html", user=user)

        if len(new_password) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "warning")
            return render_template("reset_user_password.html", user=user)

        if new_password != confirm_password:
            flash("As senhas não coincidem.", "danger")
            return render_template("reset_user_password.html", user=user)

        user.set_password(new_password)
        db.session.commit()

        flash("Senha redefinida com sucesso.", "success")
        return redirect(url_for("customers.list_users"))

    return render_template("reset_user_password.html", user=user)


@customers_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
def toggle_user_active(user_id):
    if not can_manage_users():
        flash("Você não tem permissão para alterar status de usuário.", "danger")
        return redirect(url_for("main.dashboard"))

    user = User.query.filter_by(
        id=user_id,
        company_id=current_user.company_id
    ).first_or_404()

    if user.id == current_user.id and user.is_active:
        flash("Você não pode inativar seu próprio usuário.", "warning")
        return redirect(url_for("customers.list_users"))

    user.is_active = not user.is_active
    db.session.commit()

    if user.is_active:
        flash("Usuário ativado com sucesso.", "success")
    else:
        flash("Usuário inativado com sucesso.", "success")

    return redirect(url_for("customers.list_users"))