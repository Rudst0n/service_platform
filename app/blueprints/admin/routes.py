from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models.company import Company, CompanyStatus
from app.models.user import User
from app.models.customer import Customer
from app.models.service import Service
from app.blueprints.admin import admin_bp
from app.utils.audit import log_action


def is_super_admin():
    return current_user.is_authenticated and current_user.system_role == "super_admin"


@admin_bp.route("/companies")
@login_required
def list_companies():
    if not is_super_admin():
        flash("Acesso negado.", "danger")
        return redirect(url_for("main.dashboard"))

    status_filter = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)

    query = Company.query
    if status_filter:
        query = query.filter(Company.status == status_filter)

    pagination = query.order_by(Company.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    companies = pagination.items

    data = []
    for company in companies:
        users_count = User.query.filter_by(company_id=company.id).count()
        customers_count = Customer.query.filter_by(company_id=company.id).count()
        services_count = Service.query.filter_by(company_id=company.id).count()

        data.append({
            "company": company,
            "users": users_count,
            "customers": customers_count,
            "services": services_count,
        })

    return render_template("admin/companies.html", data=data, pagination=pagination, status_filter=status_filter)


@admin_bp.route("/companies/<int:company_id>/activate", methods=["POST"])
@login_required
def activate_company(company_id):
    if not is_super_admin():
        flash("Acesso negado.", "danger")
        return redirect(url_for("main.dashboard"))

    company = Company.query.get_or_404(company_id)
    company.status = CompanyStatus.ACTIVE
    company.is_active = True
    log_action('activate_company', 'company', company.id, f'Empresa {company.name} ativada.')
    db.session.commit()

    flash("Empresa ativada com sucesso.", "success")
    return redirect(url_for("admin.list_companies"))


@admin_bp.route("/companies/<int:company_id>/block", methods=["POST"])
@login_required
def block_company(company_id):
    if not is_super_admin():
        flash("Acesso negado.", "danger")
        return redirect(url_for("main.dashboard"))

    company = Company.query.get_or_404(company_id)

    if company.id == current_user.company_id:
        flash("Você não pode bloquear sua própria empresa.", "warning")
        return redirect(url_for("admin.list_companies"))

    company.status = CompanyStatus.BLOCKED
    log_action('block_company', 'company', company.id, f'Empresa {company.name} bloqueada.')
    db.session.commit()

    flash("Empresa bloqueada.", "warning")
    return redirect(url_for("admin.list_companies"))


@admin_bp.route("/companies/<int:company_id>/deactivate", methods=["POST"])
@login_required
def deactivate_company(company_id):
    if not is_super_admin():
        flash("Acesso negado.", "danger")
        return redirect(url_for("main.dashboard"))

    company = Company.query.get_or_404(company_id)

    if company.id == current_user.company_id:
        flash("Você não pode inativar sua própria empresa.", "warning")
        return redirect(url_for("admin.list_companies"))

    company.status = CompanyStatus.INACTIVE
    log_action('deactivate_company', 'company', company.id, f'Empresa {company.name} inativada.')
    db.session.commit()

    flash("Empresa inativada com sucesso.", "success")
    return redirect(url_for("admin.list_companies"))


@admin_bp.route("/companies/<int:company_id>/plan", methods=["POST"])
@login_required
def update_company_plan(company_id):
    if not is_super_admin():
        flash("Acesso negado.", "danger")
        return redirect(url_for("main.dashboard"))

    company = Company.query.get_or_404(company_id)
    new_plan = request.form.get("plan", "").strip()

    if new_plan not in {"starter", "pro", "business"}:
        flash("Plano inválido.", "danger")
        return redirect(url_for("admin.list_companies"))

    company.plan = new_plan
    log_action('update_company_plan', 'company', company.id, f'Plano alterado para {new_plan}.')
    db.session.commit()

    flash("Plano da empresa atualizado com sucesso.", "success")
    return redirect(url_for("admin.list_companies"))
