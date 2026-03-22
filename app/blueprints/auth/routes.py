from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.blueprints.auth import auth_bp
from app.models.user import User
from app.models.company import Company
from app.extensions import db


def only_digits(value):
    if not value:
        return None
    return "".join(filter(str.isdigit, value))


def format_cpf(value):
    value = only_digits(value)
    if not value:
        return None
    if len(value) != 11:
        return value
    return f"{value[:3]}.{value[3:6]}.{value[6:9]}-{value[9:]}"


def format_cnpj(value):
    value = only_digits(value)
    if not value:
        return None
    if len(value) != 14:
        return value
    return f"{value[:2]}.{value[2:5]}.{value[5:8]}/{value[8:12]}-{value[12:]}"


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Preencha e-mail e senha.", "danger")
            return render_template("auth/login.html")

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("E-mail ou senha inválidos.", "danger")
            return render_template("auth/login.html")

        if not user.is_active:
            flash("Este usuário está inativo. Entre em contato com o administrador da empresa.", "warning")
            return render_template("auth/login.html")

        login_user(user)
        flash("Login realizado com sucesso.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip()
        cnpj = format_cnpj(request.form.get("cnpj"))
        name = request.form.get("name", "").strip()
        cpf = format_cpf(request.form.get("cpf"))
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not company_name or not name or not email or not password or not cpf:
            flash("Preencha todos os campos obrigatórios, incluindo o CPF.", "danger")
            return render_template("auth/register.html")

        if len(only_digits(cpf)) != 11:
            flash("CPF inválido.", "danger")
            return render_template("auth/register.html")

        if cnpj and len(only_digits(cnpj)) != 14:
            flash("CNPJ inválido.", "danger")
            return render_template("auth/register.html")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Já existe um usuário com este e-mail.", "danger")
            return render_template("auth/register.html")

        existing_cpf = User.query.filter_by(cpf=cpf).first()
        if existing_cpf:
            flash("Já existe um usuário com este CPF.", "danger")
            return render_template("auth/register.html")

        existing_company = Company.query.filter_by(name=company_name).first()
        if existing_company:
            flash("Já existe uma empresa com este nome.", "danger")
            return render_template("auth/register.html")

        if cnpj:
            existing_cnpj = Company.query.filter_by(cnpj=cnpj).first()
            if existing_cnpj:
                flash("Já existe uma empresa com este CNPJ.", "danger")
                return render_template("auth/register.html")

        company = Company(
            name=company_name,
            cnpj=cnpj
        )
        db.session.add(company)
        db.session.flush()

        user = User(
            name=name,
            email=email,
            cpf=cpf,
            company_id=company.id,
            system_role="company_user",
            company_role="admin_empresa",
            is_active=True
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("Conta criada com sucesso. Faça seu login para continuar.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout realizado com sucesso.", "success")
    return redirect(url_for("auth.login"))