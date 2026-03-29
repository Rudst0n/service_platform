from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.blueprints.users import users_bp
from app.extensions import db
from app.models.user import User
from app.utils.access import block_if_trial_expired
from app.utils.audit import log_action
from app.utils.plan_limits import is_limit_reached
from app.utils.security import format_cpf, is_strong_password, is_valid_email


ALLOWED_ROLES = ['admin_empresa', 'funcionario', 'visualizador']



def can_manage_users():
    return (
        current_user.is_authenticated
        and getattr(current_user, 'company_role', None) == 'admin_empresa'
        and getattr(current_user, 'is_active', False)
    )


@users_bp.route('/')
@login_required
def list_users():
    if not can_manage_users():
        flash('Você não tem permissão para gerenciar funcionários.', 'danger')
        return redirect(url_for('main.dashboard'))

    page = request.args.get('page', 1, type=int)
    pagination = (
        User.query.filter_by(company_id=current_user.company_id)
        .order_by(User.name.asc())
        .paginate(page=page, per_page=10, error_out=False)
    )
    return render_template('users/users.html', users=pagination.items, pagination=pagination)


@users_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_user():
    if not can_manage_users():
        flash('Você não tem permissão para cadastrar funcionários.', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        trial_block = block_if_trial_expired('funcionários')
        if trial_block:
            return trial_block

        if is_limit_reached(current_user.company, User, 'users'):
            flash('Você atingiu o limite de funcionários do seu plano.', 'warning')
            return redirect(url_for('users.list_users'))

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        cpf = format_cpf(request.form.get('cpf', '').strip())
        password = request.form.get('password', '').strip()
        company_role = request.form.get('company_role', '').strip()

        if not name or not email or not password:
            flash('Nome, e-mail e senha do funcionário são obrigatórios.', 'danger')
            return render_template('users/new_user.html')

        if not is_valid_email(email):
            flash('E-mail inválido.', 'warning')
            return render_template('users/new_user.html')

        if company_role not in ALLOWED_ROLES:
            flash('Perfil de funcionário inválido.', 'danger')
            return render_template('users/new_user.html')

        if User.query.filter_by(email=email).first():
            flash('Já existe um funcionário com esse e-mail.', 'warning')
            return render_template('users/new_user.html')

        if cpf and User.query.filter_by(cpf=cpf).first():
            flash('Já existe um funcionário com esse CPF.', 'warning')
            return render_template('users/new_user.html')

        valid_password, password_error = is_strong_password(password)
        if not valid_password:
            flash(password_error, 'warning')
            return render_template('users/new_user.html')

        user = User(
            name=name,
            email=email,
            cpf=cpf or None,
            system_role='company_user',
            company_role=company_role,
            company_id=current_user.company_id,
            is_active=True,
            email_confirmed=True,
        )
        user.set_password(password)

        db.session.add(user)
        db.session.flush()
        log_action('create_user', 'user', user.id, f'Funcionário {name} cadastrado com perfil {company_role}.')
        db.session.commit()

        flash('Funcionário cadastrado com sucesso.', 'success')
        return redirect(url_for('users.list_users'))

    return render_template('users/new_user.html')


@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not can_manage_users():
        flash('Você não tem permissão.', 'danger')
        return redirect(url_for('main.dashboard'))

    user = User.query.filter_by(id=user_id, company_id=current_user.company_id).first_or_404()

    if request.method == 'POST':
        trial_block = block_if_trial_expired('funcionários')
        if trial_block:
            return trial_block

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        cpf = format_cpf(request.form.get('cpf', '').strip()) or None

        if not name or not email:
            flash('Nome e e-mail são obrigatórios.', 'danger')
            return render_template('users/edit_user.html', user=user)

        if not is_valid_email(email):
            flash('E-mail inválido.', 'warning')
            return render_template('users/edit_user.html', user=user)

        email_exists = User.query.filter(User.email == email, User.id != user.id).first()
        if email_exists:
            flash('Já existe outro funcionário com esse e-mail.', 'warning')
            return render_template('users/edit_user.html', user=user)

        if cpf:
            cpf_exists = User.query.filter(User.cpf == cpf, User.id != user.id).first()
            if cpf_exists:
                flash('Já existe outro funcionário com esse CPF.', 'warning')
                return render_template('users/edit_user.html', user=user)

        user.name = name
        user.email = email
        user.cpf = cpf

        log_action('update_user', 'user', user.id, f'Funcionário {user.name} atualizado.')
        db.session.commit()

        flash('Funcionário atualizado com sucesso.', 'success')
        return redirect(url_for('users.list_users'))

    return render_template('users/edit_user.html', user=user)


@users_bp.route('/<int:user_id>/role', methods=['POST'])
@login_required
def update_user_role(user_id):
    if not can_manage_users():
        flash('Você não tem permissão.', 'danger')
        return redirect(url_for('main.dashboard'))

    user = User.query.filter_by(id=user_id, company_id=current_user.company_id).first_or_404()
    new_role = request.form.get('company_role', '').strip()

    if new_role not in ALLOWED_ROLES:
        flash('Perfil inválido.', 'danger')
        return redirect(url_for('users.list_users'))

    if user.id == current_user.id and new_role != 'admin_empresa':
        flash('Você não pode remover seu próprio acesso de admin.', 'warning')
        return redirect(url_for('users.list_users'))

    user.company_role = new_role
    log_action('update_user_role', 'user', user.id, f'Perfil alterado para {new_role}.')
    db.session.commit()

    flash('Perfil do funcionário atualizado com sucesso.', 'success')
    return redirect(url_for('users.list_users'))


@users_bp.route('/<int:user_id>/reset-password', methods=['GET', 'POST'])
@login_required
def reset_user_password(user_id):
    if not can_manage_users():
        flash('Você não tem permissão para redefinir senha de funcionário.', 'danger')
        return redirect(url_for('main.dashboard'))

    user = User.query.filter_by(id=user_id, company_id=current_user.company_id).first_or_404()

    if request.method == 'POST':
        trial_block = block_if_trial_expired('funcionários')
        if trial_block:
            return trial_block

        new_password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not new_password or not confirm_password:
            flash('Preencha os dois campos de senha.', 'danger')
            return render_template('users/reset_user_password.html', user=user)

        valid_password, password_error = is_strong_password(new_password)
        if not valid_password:
            flash(password_error, 'warning')
            return render_template('users/reset_user_password.html', user=user)

        if new_password != confirm_password:
            flash('As senhas não coincidem.', 'danger')
            return render_template('users/reset_user_password.html', user=user)

        user.set_password(new_password)
        log_action('reset_user_password', 'user', user.id, 'Senha redefinida por administrador.')
        db.session.commit()

        flash('Senha redefinida com sucesso.', 'success')
        return redirect(url_for('users.list_users'))

    return render_template('users/reset_user_password.html', user=user)


@users_bp.route('/<int:user_id>/toggle-active', methods=['POST'])
@login_required
def toggle_user_active(user_id):
    if not can_manage_users():
        flash('Você não tem permissão para alterar status de funcionário.', 'danger')
        return redirect(url_for('main.dashboard'))

    user = User.query.filter_by(id=user_id, company_id=current_user.company_id).first_or_404()

    if user.id == current_user.id and user.is_active:
        flash('Você não pode inativar seu próprio usuário de acesso.', 'warning')
        return redirect(url_for('users.list_users'))

    user.is_active = not user.is_active
    log_action('toggle_user_active', 'user', user.id, f'Status do funcionário alterado para {user.is_active}.')
    db.session.commit()

    flash('Funcionário ativado com sucesso.' if user.is_active else 'Funcionário inativado com sucesso.', 'success')
    return redirect(url_for('users.list_users'))
