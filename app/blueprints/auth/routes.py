from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.blueprints.auth import auth_bp
from app.models.user import User
from app.models.company import Company
from app.extensions import db


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Login realizado com sucesso.", "success")
            return redirect(url_for("main.dashboard"))

        flash("E-mail ou senha inválidos.", "danger")

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        company_name = request.form.get("company_name")
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if not company_name or not name or not email or not password:
            flash("Preencha todos os campos.", "danger")
            return render_template("register.html")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Já existe um usuário com este e-mail.", "danger")
            return render_template("register.html")

        existing_company = Company.query.filter_by(name=company_name).first()
        if existing_company:
            flash("Já existe uma empresa com este nome.", "danger")
            return render_template("register.html")

        company = Company(name=company_name)
        db.session.add(company)
        db.session.flush()

        user = User(
            name=name,
            email=email,
            company_id=company.id
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("Conta criada com sucesso.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout realizado com sucesso.", "success")
    return redirect(url_for("auth.login"))