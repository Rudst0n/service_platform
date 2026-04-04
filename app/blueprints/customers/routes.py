from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.blueprints.customers import customers_bp
from app.extensions import db
from app.models.customer import Customer
from app.utils.audit import log_action
from app.utils.normalizer import normalize_email, normalize_phone, normalize_text
from app.utils.permissions import require_company_role


@customers_bp.route('/')
@login_required
def list_customers():
    page = request.args.get('page', 1, type=int)

    pagination = Customer.query.filter_by(
        company_id=current_user.company_id
    ).order_by(Customer.id.desc()).paginate(page=page, per_page=10)

    return render_template(
        'customers/customers.html',
        customers=pagination.items,
        pagination=pagination
    )


@customers_bp.route('/new', methods=['GET', 'POST'])
@login_required
@require_company_role('admin_empresa', 'funcionario')
def new_customer():
    if request.method == 'POST':
        name = normalize_text(request.form.get('name'))
        phone = normalize_phone(request.form.get('phone'))
        email = normalize_email(request.form.get('email'))

        if not name:
            flash('Nome é obrigatório.', 'danger')
            return redirect(url_for('customers.new_customer'))

        try:
            customer = Customer(
                name=name,
                phone=phone,
                email=email,
                company_id=current_user.company_id
            )

            db.session.add(customer)
            db.session.flush()

            log_action(
                'create_customer',
                'customer',
                customer.id,
                f'Cliente {customer.name} criado.',
                company_id=current_user.company_id,
                user_id=current_user.id
            )

            db.session.commit()

            flash('Cliente criado com sucesso.', 'success')
            return redirect(url_for('customers.list_customers'))

        except Exception:
            db.session.rollback()
            flash('Erro ao criar cliente.', 'danger')
            return redirect(url_for('customers.new_customer'))

    return render_template('customers/new_customer.html')


@customers_bp.route('/edit/<int:customer_id>', methods=['GET', 'POST'])
@login_required
@require_company_role('admin_empresa', 'funcionario')
def edit_customer(customer_id):
    customer = Customer.query.filter_by(
        id=customer_id,
        company_id=current_user.company_id
    ).first_or_404()

    if request.method == 'POST':
        name = normalize_text(request.form.get('name'))
        phone = normalize_phone(request.form.get('phone'))
        email = normalize_email(request.form.get('email'))

        if not name:
            flash('Nome é obrigatório.', 'danger')
            return redirect(url_for('customers.edit_customer', customer_id=customer.id))

        try:
            customer.name = name
            customer.phone = phone
            customer.email = email

            log_action(
                'update_customer',
                'customer',
                customer.id,
                f'Cliente {customer.name} atualizado.',
                company_id=current_user.company_id,
                user_id=current_user.id
            )

            db.session.commit()

            flash('Cliente atualizado.', 'success')
            return redirect(url_for('customers.list_customers'))

        except Exception:
            db.session.rollback()
            flash('Erro ao atualizar cliente.', 'danger')
            return redirect(url_for('customers.edit_customer', customer_id=customer.id))

    return render_template('customers/edit_customer.html', customer=customer)


@customers_bp.route('/delete/<int:customer_id>', methods=['POST'])
@login_required
@require_company_role('admin_empresa')
def delete_customer(customer_id):
    customer = Customer.query.filter_by(
        id=customer_id,
        company_id=current_user.company_id
    ).first_or_404()

    try:
        log_action(
            'delete_customer',
            'customer',
            customer.id,
            f'Cliente {customer.name} excluído',
            company_id=current_user.company_id,
            user_id=current_user.id
        )

        db.session.delete(customer)
        db.session.commit()

        flash('Cliente excluído.', 'success')

    except Exception:
        db.session.rollback()
        flash('Erro ao excluir cliente.', 'danger')

    return redirect(url_for('customers.list_customers'))