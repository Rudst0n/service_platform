from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.blueprints.users import users_bp
from app.extensions import db
from app.models.user import User


def can_manage_users():
    return (
        current_user.is_authenticated
        and getattr(current_user, "company_role", None) == "admin_empresa"
        and getattr(current_user, "is_active", False)
    )


@users_bp.route("/")
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

    return render_template("users/users.html", users=users)


@users_bp.route("/new", methods=["GET", "POST"])
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
            return render_template("users/new_user.html")

        if company_role not in allowed_roles:
            flash("Perfil de usuário inválido.", "danger")
            return render_template("users/new_user.html")

        if User.query.filter_by(email=email).first():
            flash("Já existe um usuário com esse e-mail.", "warning")
            return render_template("users/new_user.html")

        if cpf and User.query.filter_by(cpf=cpf).first():
            flash("Já existe um usuário com esse CPF.", "warning")
            return render_template("users/new_user.html")

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
        return redirect(url_for("users.list_users"))

    return render_template("users/new_user.html")


@users_bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
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
            return render_template("users/edit_user.html", user=user)

        email_exists = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()
        if email_exists:
            flash("Já existe outro usuário com esse e-mail.", "warning")
            return render_template("users/edit_user.html", user=user)

        if cpf:
            cpf_exists = User.query.filter(
                User.cpf == cpf,
                User.id != user.id
            ).first()
            if cpf_exists:
                flash("Já existe outro usuário com esse CPF.", "warning")
                return render_template("users/edit_user.html", user=user)

        user.name = name
        user.email = email
        user.cpf = cpf

        db.session.commit()

        flash("Usuário atualizado com sucesso.", "success")
        return redirect(url_for("users.list_users"))

    return render_template("users/edit_user.html", user=user)


@users_bp.route("/<int:user_id>/role", methods=["POST"])
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
        return redirect(url_for("users.list_users"))

    if user.id == current_user.id and new_role != "admin_empresa":
        flash("Você não pode remover seu próprio acesso de admin.", "warning")
        return redirect(url_for("users.list_users"))

    user.company_role = new_role
    db.session.commit()

    flash("Perfil atualizado com sucesso.", "success")
    return redirect(url_for("users.list_users"))


@users_bp.route("/<int:user_id>/reset-password", methods=["GET", "POST"])
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
            return render_template("users/reset_user_password.html", user=user)

        if len(new_password) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "warning")
            return render_template("users/reset_user_password.html", user=user)

        if new_password != confirm_password:
            flash("As senhas não coincidem.", "danger")
            return render_template("users/reset_user_password.html", user=user)

        user.set_password(new_password)
        db.session.commit()

        flash("Senha redefinida com sucesso.", "success")
        return redirect(url_for("users.list_users"))

    return render_template("users/reset_user_password.html", user=user)


@users_bp.route("/<int:user_id>/toggle-active", methods=["POST"])
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
        return redirect(url_for("users.list_users"))

    user.is_active = not user.is_active
    db.session.commit()

    if user.is_active:
        flash("Usuário ativado com sucesso.", "success")
    else:
        flash("Usuário inativado com sucesso.", "success")

    return redirect(url_for("users.list_users"))