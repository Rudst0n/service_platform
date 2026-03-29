from flask import render_template, redirect, url_for
from flask_login import current_user, login_required

from app.utils.plan_limits import get_usage_data
from app.blueprints.main import main_bp
from app.models.company import Company
from app.models.customer import Customer
from app.models.service import Service
from app.extensions import db


@main_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("landing.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    is_super_admin = current_user.system_role == "super_admin"
    is_employee = current_user.company_role == "funcionario" and not is_super_admin
    company = None if is_super_admin else current_user.company

    if is_employee:
        if not company:
            return redirect(url_for("auth.login"))

        total_services = Service.query.filter_by(
            company_id=company.id,
            assigned_to_id=current_user.id
        ).count()

        services_em_andamento = Service.query.filter_by(
            company_id=company.id,
            assigned_to_id=current_user.id,
            status="em_andamento"
        ).count()

        services_finalizado = Service.query.filter_by(
            company_id=company.id,
            assigned_to_id=current_user.id,
            status="finalizado"
        ).count()

        services_pendentes = Service.query.filter(
            Service.company_id == company.id,
            Service.assigned_to_id == current_user.id,
            Service.status.in_(["orcamento", "aprovado"])
        ).count()

        latest_services = Service.query.filter_by(
            company_id=company.id,
            assigned_to_id=current_user.id
        ).order_by(
            Service.created_at.desc()
        ).limit(5).all()

        return render_template(
            "dashboard/dashboard_employee.html",
            total_services=total_services,
            services_em_andamento=services_em_andamento,
            services_finalizado=services_finalizado,
            services_pendentes=services_pendentes,
            latest_services=latest_services,
        )

    if is_super_admin:
        total_companies = Company.query.count()
        total_customers = Customer.query.count()
        total_services = Service.query.count()

        total_revenue = db.session.query(
            db.func.coalesce(db.func.sum(Service.price), 0)
        ).filter(
            Service.status == "finalizado"
        ).scalar()

        latest_services = Service.query.order_by(
            Service.created_at.desc()
        ).limit(10).all()

        top_customer = db.session.query(
            Customer.name,
            Customer.company_id,
            db.func.count(Service.id).label("services_count")
        ).join(
            Service, Service.customer_id == Customer.id
        ).group_by(
            Customer.id,
            Customer.name,
            Customer.company_id
        ).order_by(
            db.desc("services_count")
        ).first()

        services_orcamento = Service.query.filter_by(status="orcamento").count()
        services_aprovado = Service.query.filter_by(status="aprovado").count()
        services_em_andamento = Service.query.filter_by(status="em_andamento").count()
        services_finalizado = Service.query.filter_by(status="finalizado").count()
        services_cancelado = Service.query.filter_by(status="cancelado").count()

        return render_template(
            "dashboard/dashboard.html",
            company=None,
            total_companies=total_companies,
            total_customers=total_customers,
            total_services=total_services,
            total_revenue=total_revenue,
            latest_services=latest_services,
            top_customer=top_customer,
            services_orcamento=services_orcamento,
            services_aprovado=services_aprovado,
            services_em_andamento=services_em_andamento,
            services_finalizado=services_finalizado,
            services_cancelado=services_cancelado,
            plan_usage=None,
            is_super_admin=True,
        )

    if not company:
        return redirect(url_for("auth.login"))

    total_customers = Customer.query.filter_by(company_id=company.id).count()
    total_services = Service.query.filter_by(company_id=company.id).count()

    total_revenue = db.session.query(
        db.func.coalesce(db.func.sum(Service.price), 0)
    ).filter(
        Service.company_id == company.id,
        Service.status == "finalizado"
    ).scalar()

    latest_services = Service.query.filter_by(
        company_id=company.id
    ).order_by(
        Service.created_at.desc()
    ).limit(5).all()

    top_customer = db.session.query(
        Customer.name,
        db.func.count(Service.id).label("services_count")
    ).join(
        Service, Service.customer_id == Customer.id
    ).filter(
        Customer.company_id == company.id
    ).group_by(
        Customer.id,
        Customer.name
    ).order_by(
        db.desc("services_count")
    ).first()

    services_orcamento = Service.query.filter_by(
        company_id=company.id,
        status="orcamento"
    ).count()

    services_aprovado = Service.query.filter_by(
        company_id=company.id,
        status="aprovado"
    ).count()

    services_em_andamento = Service.query.filter_by(
        company_id=company.id,
        status="em_andamento"
    ).count()

    services_finalizado = Service.query.filter_by(
        company_id=company.id,
        status="finalizado"
    ).count()

    services_cancelado = Service.query.filter_by(
        company_id=company.id,
        status="cancelado"
    ).count()

    plan_usage = get_usage_data(company)

    return render_template(
        "dashboard/dashboard.html",
        company=company,
        total_companies=None,
        total_customers=total_customers,
        total_services=total_services,
        total_revenue=total_revenue,
        latest_services=latest_services,
        top_customer=top_customer,
        services_orcamento=services_orcamento,
        services_aprovado=services_aprovado,
        services_em_andamento=services_em_andamento,
        services_finalizado=services_finalizado,
        services_cancelado=services_cancelado,
        plan_usage=plan_usage,
        is_super_admin=False,
    )