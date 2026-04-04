from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.blueprints.services import services_bp
from app.extensions import db
from app.models.service import Service
from app.models.customer import Customer
from app.utils.audit import log_action
from app.utils.normalizer import normalize_text
from app.utils.permissions import require_company_role


@services_bp.route('/')
@login_required
def list_services():
    services = Service.query.filter_by(
        company_id=current_user.company_id
    ).order_by(Service.id.desc()).all()

    return render_template('services/services.html', services=services)


@services_bp.route('/new', methods=['GET', 'POST'])
@login_required
@require_company_role('admin_empresa')
def new_service():
    customers = Customer.query.filter_by(
        company_id=current_user.company_id
    ).all()

    if request.method == 'POST':
        name = normalize_text(request.form.get('name'))
        customer_id = request.form.get('customer_id')

        if not name or not customer_id:
            flash('Preencha os campos obrigatórios.', 'danger')
            return redirect(url_for('services.new_service'))

        try:
            service = Service(
                name=name,
                customer_id=customer_id,
                company_id=current_user.company_id
            )

            db.session.add(service)
            db.session.flush()

            log_action(
                'create_service',
                'service',
                service.id,
                f'Serviço {name} criado.',
                company_id=current_user.company_id,
                user_id=current_user.id
            )

            db.session.commit()

            flash('Serviço criado.', 'success')
            return redirect(url_for('services.list_services'))

        except Exception:
            db.session.rollback()
            flash('Erro ao criar serviço.', 'danger')

    return render_template('services/new_service.html', customers=customers)


@services_bp.route('/edit/<int:service_id>', methods=['GET', 'POST'])
@login_required
@require_company_role('admin_empresa')
def edit_service(service_id):
    service = Service.query.filter_by(
        id=service_id,
        company_id=current_user.company_id
    ).first_or_404()

    customers = Customer.query.filter_by(
        company_id=current_user.company_id
    ).all()

    if request.method == 'POST':
        try:
            service.name = normalize_text(request.form.get('name'))
            service.customer_id = request.form.get('customer_id')

            if not service.name or not service.customer_id:
                flash('Preencha os campos obrigatórios.', 'danger')
                return redirect(url_for('services.edit_service', service_id=service.id))

            log_action(
                'update_service',
                'service',
                service.id,
                'Serviço atualizado',
                company_id=current_user.company_id,
                user_id=current_user.id
            )

            db.session.commit()

            flash('Serviço atualizado.', 'success')
            return redirect(url_for('services.list_services'))

        except Exception:
            db.session.rollback()
            flash('Erro ao atualizar serviço.', 'danger')

    return render_template('services/edit_service.html', service=service, customers=customers)


@services_bp.route('/delete/<int:service_id>', methods=['POST'])
@login_required
@require_company_role('admin_empresa')
def delete_service(service_id):
    service = Service.query.filter_by(
        id=service_id,
        company_id=current_user.company_id
    ).first_or_404()

    try:
        log_action(
            'delete_service',
            'service',
            service.id,
            f'Serviço {service.name} excluído',
            company_id=current_user.company_id,
            user_id=current_user.id
        )

        db.session.delete(service)
        db.session.commit()

        flash('Serviço excluído.', 'success')

    except Exception:
        db.session.rollback()
        flash('Erro ao excluir serviço.', 'danger')

    return redirect(url_for('services.list_services'))