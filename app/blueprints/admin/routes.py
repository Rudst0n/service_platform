from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.blueprints.admin import admin_bp
from app.extensions import db
from app.models.company import Company, CompanyStatus
from app.models.customer import Customer
from app.models.service import Service
from app.models.user import User
from app.utils.audit import log_action
from app.utils.normalizer import only_digits
from app.utils.permissions import require_system_role


VALID_PLANS = {"starter", "pro", "business"}
DEFAULT_COMPANY_ADMIN_PASSWORD = "12345678"


def parse_trial_end_date(value):
    value = (value or "").strip()
    if not value:
        return None

    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
        return parsed.replace(hour=23, minute=59, second=59)
    except ValueError:
        return None


def format_cnpj_from_digits(value):
    digits = only_digits(value)
    if not digits:
        return None

    if len(digits) != 14:
        return None

    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


def get_company_admin_user(company_id):
    return (
        User.query
        .filter_by(company_id=company_id, company_role="admin_empresa")
        .order_by(User.is_active.desc(), User.id.asc())
        .first()
    )


@admin_bp.route("/companies")
@login_required
@require_system_role("super_admin")
def list_companies():
    status_filter = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)

    query = Company.query
    if status_filter:
        query = query.filter(Company.status == status_filter)

    pagination = (
        query.order_by(Company.created_at.desc())
        .paginate(page=page, per_page=10, error_out=False)
    )
    companies = pagination.items

    data = []
    for company in companies:
        users_count = User.query.filter_by(company_id=company.id).count()
        customers_count = Customer.query.filter_by(company_id=company.id).count()
        services_count = Service.query.filter_by(company_id=company.id).count()
        admin_user = get_company_admin_user(company.id)

        data.append(
            {
                "company": company,
                "users": users_count,
                "customers": customers_count,
                "services": services_count,
                "admin_user": admin_user,
            }
        )

    return render_template(
        "admin/companies.html",
        data=data,
        pagination=pagination,
        status_filter=status_filter,
    )


@admin_bp.route("/companies/<int:company_id>/edit", methods=["GET", "POST"])
@login_required
@require_system_role("super_admin")
def edit_company(company_id):
    company = Company.query.get_or_404(company_id)
    admin_user = get_company_admin_user(company.id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        cnpj_raw = request.form.get("cnpj", "").strip()
        plan = request.form.get("plan", "").strip()
        status = request.form.get("status", "").strip()
        is_active = request.form.get("is_active") == "1"
        trial_ends_at_raw = request.form.get("trial_ends_at", "").strip()

        if not name:
            flash("O nome da empresa é obrigatório.", "danger")
            return render_template(
                "admin/edit_company.html",
                company=company,
                admin_user=admin_user,
                status_options=CompanyStatus.ALL,
            )

        if plan not in VALID_PLANS:
            flash("Plano inválido.", "danger")
            return render_template(
                "admin/edit_company.html",
                company=company,
                admin_user=admin_user,
                status_options=CompanyStatus.ALL,
            )

        if status not in CompanyStatus.ALL:
            flash("Status inválido.", "danger")
            return render_template(
                "admin/edit_company.html",
                company=company,
                admin_user=admin_user,
                status_options=CompanyStatus.ALL,
            )

        existing_name = Company.query.filter(
            Company.name == name,
            Company.id != company.id,
        ).first()
        if existing_name:
            flash("Já existe uma empresa com esse nome.", "danger")
            return render_template(
                "admin/edit_company.html",
                company=company,
                admin_user=admin_user,
                status_options=CompanyStatus.ALL,
            )

        cnpj_digits = only_digits(cnpj_raw)
        if cnpj_digits:
            if len(cnpj_digits) != 14:
                flash("CNPJ inválido. Deve conter 14 números.", "danger")
                return render_template(
                    "admin/edit_company.html",
                    company=company,
                    admin_user=admin_user,
                    status_options=CompanyStatus.ALL,
                )

            cnpj = format_cnpj_from_digits(cnpj_digits)
        else:
            cnpj = None

        if cnpj:
            existing_cnpj = Company.query.filter(
                Company.cnpj == cnpj,
                Company.id != company.id,
            ).first()
            if existing_cnpj:
                flash("Já existe uma empresa com esse CNPJ.", "danger")
                return render_template(
                    "admin/edit_company.html",
                    company=company,
                    admin_user=admin_user,
                    status_options=CompanyStatus.ALL,
                )

        parsed_trial_ends_at = parse_trial_end_date(trial_ends_at_raw)
        if trial_ends_at_raw and parsed_trial_ends_at is None:
            flash("Data de trial inválida.", "danger")
            return render_template(
                "admin/edit_company.html",
                company=company,
                admin_user=admin_user,
                status_options=CompanyStatus.ALL,
            )

        company.name = name
        company.cnpj = cnpj
        company.plan = plan
        company.status = status
        company.is_active = is_active
        company.trial_ends_at = parsed_trial_ends_at

        log_action(
            "edit_company",
            "company",
            company.id,
            f"Empresa {company.name} editada pelo super admin.",
            company_id=company.id,
            user_id=current_user.id,
        )

        db.session.commit()

        flash("Empresa atualizada com sucesso.", "success")
        return redirect(url_for("admin.list_companies"))

    return render_template(
        "admin/edit_company.html",
        company=company,
        admin_user=admin_user,
        status_options=CompanyStatus.ALL,
    )


@admin_bp.route("/companies/<int:company_id>/reset-admin-password", methods=["POST"])
@login_required
@require_system_role("super_admin")
def reset_company_admin_password(company_id):
    company = Company.query.get_or_404(company_id)
    admin_user = get_company_admin_user(company.id)

    if not admin_user:
        flash("Esta empresa não possui usuário administrador cadastrado.", "warning")
        return redirect(url_for("admin.edit_company", company_id=company.id))

    try:
        admin_user.set_password(DEFAULT_COMPANY_ADMIN_PASSWORD)
        admin_user.must_change_password = True
        admin_user.reset_login_lock()

        log_action(
            "reset_company_admin_password",
            "user",
            admin_user.id,
            f"Senha do administrador da empresa {company.name} redefinida pelo super admin.",
            company_id=company.id,
            user_id=current_user.id,
        )

        db.session.commit()

        flash(
            f"Senha do administrador redefinida com sucesso. Nova senha temporária: {DEFAULT_COMPANY_ADMIN_PASSWORD}",
            "success",
        )
    except Exception:
        db.session.rollback()
        flash("Erro ao redefinir a senha do administrador da empresa.", "danger")

    return redirect(url_for("admin.edit_company", company_id=company.id))


@admin_bp.route("/companies/<int:company_id>/activate", methods=["POST"])
@login_required
@require_system_role("super_admin")
def activate_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.status = CompanyStatus.ACTIVE
    company.is_active = True

    log_action(
        "activate_company",
        "company",
        company.id,
        f"Empresa {company.name} ativada.",
        company_id=company.id,
        user_id=current_user.id,
    )

    db.session.commit()

    flash("Empresa ativada com sucesso.", "success")
    return redirect(url_for("admin.list_companies"))


@admin_bp.route("/companies/<int:company_id>/block", methods=["POST"])
@login_required
@require_system_role("super_admin")
def block_company(company_id):
    company = Company.query.get_or_404(company_id)

    if company.id == current_user.company_id:
        flash("Você não pode bloquear sua própria empresa.", "warning")
        return redirect(url_for("admin.list_companies"))

    company.status = CompanyStatus.BLOCKED
    company.is_active = False

    log_action(
        "block_company",
        "company",
        company.id,
        f"Empresa {company.name} bloqueada.",
        company_id=company.id,
        user_id=current_user.id,
    )

    db.session.commit()

    flash("Empresa bloqueada.", "warning")
    return redirect(url_for("admin.list_companies"))


@admin_bp.route("/companies/<int:company_id>/deactivate", methods=["POST"])
@login_required
@require_system_role("super_admin")
def deactivate_company(company_id):
    company = Company.query.get_or_404(company_id)

    if company.id == current_user.company_id:
        flash("Você não pode inativar sua própria empresa.", "warning")
        return redirect(url_for("admin.list_companies"))

    company.status = CompanyStatus.INACTIVE
    company.is_active = False

    log_action(
        "deactivate_company",
        "company",
        company.id,
        f"Empresa {company.name} inativada.",
        company_id=company.id,
        user_id=current_user.id,
    )

    db.session.commit()

    flash("Empresa inativada com sucesso.", "success")
    return redirect(url_for("admin.list_companies"))


@admin_bp.route("/companies/<int:company_id>/plan", methods=["POST"])
@login_required
@require_system_role("super_admin")
def update_company_plan(company_id):
    company = Company.query.get_or_404(company_id)
    new_plan = request.form.get("plan", "").strip()

    if new_plan not in VALID_PLANS:
        flash("Plano inválido.", "danger")
        return redirect(url_for("admin.list_companies"))

    company.plan = new_plan

    log_action(
        "update_company_plan",
        "company",
        company.id,
        f"Plano alterado para {new_plan}.",
        company_id=company.id,
        user_id=current_user.id,
    )

    db.session.commit()

    flash("Plano da empresa atualizado com sucesso.", "success")
    return redirect(url_for("admin.list_companies"))