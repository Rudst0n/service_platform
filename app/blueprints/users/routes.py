from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.blueprints.users import users_bp
from app.extensions import db
from app.models import user
from app.models.user import User
from app.utils.audit import log_action
from app.utils.normalizer import normalize_email, normalize_text
from app.utils.permissions import require_company_role
from app.utils.plan_limits import is_limit_reached
from app.utils.security import (
    format_cpf,
    generate_temporary_password,
    is_strong_password,
    is_valid_email,
    only_digits,
)

ALLOWED_COMPANY_ROLES = {"funcionario", "visualizador"}
DEFAULT_COMPANY_ROLE = "funcionario"


def get_company_users_query():
    return User.query.filter_by(company_id=current_user.company_id)


def validate_company_role(company_role):
    return company_role in ALLOWED_COMPANY_ROLES


def sanitize_company_role(company_role):
    company_role = normalize_text(company_role or DEFAULT_COMPANY_ROLE)
    if not validate_company_role(company_role):
        return DEFAULT_COMPANY_ROLE
    return company_role


def find_duplicate_user(email, cpf, ignore_user_id=None):
    query = User.query.filter(User.company_id == current_user.company_id)

    filters = []
    if email:
        filters.append(User.email == email)
    if cpf:
        filters.append(User.cpf == cpf)

    if not filters:
        return None

    query = query.filter(or_(*filters))

    if ignore_user_id:
        query = query.filter(User.id != ignore_user_id)

    return query.first()


@users_bp.route("/")
@login_required
@require_company_role("admin_empresa")
def list_users():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()

    query = get_company_users_query()

    if search:
        search_digits = only_digits(search)
        filters = [
            User.name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
        ]

        if search_digits:
            filters.append(User.cpf.ilike(f"%{search_digits}%"))

        query = query.filter(or_(*filters))

    pagination = (
        query.order_by(User.id.desc())
        .paginate(page=page, per_page=10, error_out=False)
    )

    return render_template(
        "users/users.html",
        users=pagination.items,
        pagination=pagination,
        search=search,
    )


@users_bp.route("/new", methods=["GET", "POST"])
@login_required
@require_company_role("admin_empresa")
def new_user():
    if request.method == "POST":
        if is_limit_reached(current_user.company, User, "users"):
            flash("Você atingiu o limite de usuários do seu plano.", "warning")
            return redirect(url_for("users.list_users"))

        name = normalize_text(request.form.get("name"))
        email = normalize_email(request.form.get("email"))
        cpf = format_cpf(request.form.get("cpf", ""))
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        company_role = sanitize_company_role(request.form.get("company_role", DEFAULT_COMPANY_ROLE))
        is_active = request.form.get("is_active") == "on"

        if not name or not email or not password or not confirm_password:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template("users/new_user.html")

        if not is_valid_email(email):
            flash("E-mail inválido.", "danger")
            return render_template("users/new_user.html")

        valid_password, password_error = is_strong_password(password)
        if not valid_password:
            flash(password_error, "danger")
            return render_template("users/new_user.html")

        if password != confirm_password:
            flash("As senhas não coincidem.", "danger")
            return render_template("users/new_user.html")

        cpf_digits = only_digits(cpf)
        if cpf and (not cpf_digits or len(cpf_digits) != 11):
            flash("CPF inválido.", "danger")
            return render_template("users/new_user.html")

        duplicate_user = find_duplicate_user(email=email, cpf=cpf if cpf else None)
        if duplicate_user:
            if email and duplicate_user.email == email:
                flash("Já existe um usuário com este e-mail na sua empresa.", "danger")
            else:
                flash("Já existe um usuário com este CPF na sua empresa.", "danger")
            return render_template("users/new_user.html")

        try:
            user = User(
                name=name,
                email=email,
                cpf=cpf if cpf else None,
                company_id=current_user.company_id,
                system_role="company_user",
                company_role=company_role,
                is_active=is_active,
                email_confirmed=False,
                must_change_password=False,
            )
            user.set_password(password)

            db.session.add(user)
            db.session.flush()

            log_action(
                "create_user",
                "user",
                user.id,
                f"Usuário {user.name} criado.",
                company_id=current_user.company_id,
                user_id=current_user.id,
            )

            db.session.commit()

            flash("Usuário criado com sucesso.", "success")
            return redirect(url_for("users.list_users"))

        except Exception:
            db.session.rollback()
            flash("Erro ao criar usuário.", "danger")

    return render_template("users/new_user.html")


@users_bp.route("/edit/<int:user_id>", methods=["GET", "POST"])
@login_required
@require_company_role("admin_empresa")
def edit_user(user_id):
    user = get_company_users_query().filter_by(id=user_id).first_or_404()

    if request.method == "POST":
        name = normalize_text(request.form.get("name"))
        email = normalize_email(request.form.get("email"))
        cpf = format_cpf(request.form.get("cpf", ""))
        company_role = sanitize_company_role(request.form.get("company_role", user.company_role))
        is_active = request.form.get("is_active") == "on"
        new_password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email:
            flash("Nome e e-mail são obrigatórios.", "danger")
            return render_template("users/edit_user.html", user=user)

        if not is_valid_email(email):
            flash("E-mail inválido.", "danger")
            return render_template("users/edit_user.html", user=user)

        cpf_digits = only_digits(cpf)
        if cpf and (not cpf_digits or len(cpf_digits) != 11):
            flash("CPF inválido.", "danger")
            return render_template("users/edit_user.html", user=user)

        duplicate_user = find_duplicate_user(
            email=email,
            cpf=cpf if cpf else None,
            ignore_user_id=user.id,
        )
        if duplicate_user:
            if email and duplicate_user.email == email:
                flash("Já existe outro usuário com este e-mail na sua empresa.", "danger")
            else:
                flash("Já existe outro usuário com este CPF na sua empresa.", "danger")
            return render_template("users/edit_user.html", user=user)

        if new_password:
            valid_password, password_error = is_strong_password(new_password)
            if not valid_password:
                flash(password_error, "danger")
                return render_template("users/edit_user.html", user=user)

            if new_password != confirm_password:
                flash("As senhas não coincidem.", "danger")
                return render_template("users/edit_user.html", user=user)

        try:
            user.name = name
            user.email = email
            user.cpf = cpf if cpf else None
            user.company_role = company_role
            user.is_active = is_active

            if new_password:
                user.set_password(new_password)
                user.must_change_password = False
                user.reset_login_lock()

            log_action(
                "update_user",
                "user",
                user.id,
                f"Usuário {user.name} atualizado.",
                company_id=current_user.company_id,
                user_id=current_user.id,
            )

            db.session.commit()

            flash("Usuário atualizado com sucesso.", "success")
            return redirect(url_for("users.list_users"))

        except Exception:
            db.session.rollback()
            flash("Erro ao atualizar usuário.", "danger")

    return render_template("users/edit_user.html", user=user)


@users_bp.route("/<int:user_id>/update-role", methods=["POST"])
@login_required
@require_company_role("admin_empresa")
def update_user_role(user_id):
    user = get_company_users_query().filter_by(id=user_id).first_or_404()

    company_role = sanitize_company_role(request.form.get("company_role"))

    try:
        user.company_role = company_role

        log_action(
            "update_user_role",
            "user",
            user.id,
            f"Perfil alterado para {company_role}",
            company_id=current_user.company_id,
            user_id=current_user.id,
        )

        db.session.commit()

        flash("Perfil atualizado com sucesso.", "success")

    except Exception:
        db.session.rollback()
        flash("Erro ao atualizar perfil.", "danger")

    return redirect(url_for("users.list_users"))


@users_bp.route("/<int:user_id>/toggle-status", methods=["POST"])
@login_required
@require_company_role("admin_empresa")
def toggle_user_status(user_id):
    user = get_company_users_query().filter_by(id=user_id).first_or_404()

    if user.id == current_user.id:
        flash("Você não pode alterar seu próprio status.", "warning")
        return redirect(url_for("users.list_users"))

    try:
        user.is_active = not user.is_active

        log_action(
            "toggle_user_status",
            "user",
            user.id,
            "Status alterado",
            company_id=current_user.company_id,
            user_id=current_user.id,
        )

        db.session.commit()

        flash("Status atualizado.", "success")

    except Exception:
        db.session.rollback()
        flash("Erro ao alterar status.", "danger")

    return redirect(url_for("users.list_users"))


@users_bp.route("/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@require_company_role("admin_empresa")
def toggle_user_active(user_id):
    return toggle_user_status(user_id)


@users_bp.route("/<int:user_id>/reset-password", methods=["POST"])
@login_required
@require_company_role("admin_empresa")
def reset_user_password(user_id):
    user = get_company_users_query().filter_by(id=user_id).first_or_404()

    if user.id == current_user.id:
        flash("Use a opção de alteração de senha no seu próprio perfil.", "warning")
        return redirect(url_for("users.list_users"))

    try:
        temporary_password = generate_temporary_password()

        user.set_password(temporary_password)
        user.must_change_password = True
        user.reset_login_lock()

        log_action(
            "reset_user_password",
            "user",
            user.id,
            f"Senha do usuário {user.name} redefinida pelo administrador.",
            company_id=current_user.company_id,
            user_id=current_user.id,
        )

        db.session.commit()

        flash(
            f"Senha redefinida com sucesso. Nova senha temporária: {temporary_password}",
            "success",
        )

    except Exception:
        db.session.rollback()
        flash("Erro ao redefinir senha.", "danger")

    return redirect(url_for("users.list_users"))


@users_bp.route("/delete/<int:user_id>", methods=["POST"])
@login_required
@require_company_role("admin_empresa")
def delete_user(user_id):
    user = get_company_users_query().filter_by(id=user_id).first_or_404()

    if user.id == current_user.id:
        flash("Você não pode excluir seu próprio usuário.", "warning")
        return redirect(url_for("users.list_users"))

    try:
        log_action(
            "delete_user",
            "user",
            user.id,
            f"Usuário {user.name} excluído",
            company_id=current_user.company_id,
            user_id=current_user.id,
        )

        db.session.delete(user)
        db.session.commit()

        flash("Usuário excluído.", "success")

    except Exception:
        db.session.rollback()
        flash("Erro ao excluir usuário.", "danger")

    return redirect(url_for("users.list_users"))