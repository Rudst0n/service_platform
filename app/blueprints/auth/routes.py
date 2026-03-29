from datetime import datetime, timedelta

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.blueprints.auth import auth_bp
from app.extensions import db
from app.models.company import Company, CompanyStatus
from app.models.user import User
from app.utils.audit import log_action
from app.utils.security import (
    format_cnpj,
    format_cpf,
    generate_token,
    is_strong_password,
    is_valid_email,
    normalize_text,
    only_digits,
    read_token,
)


CONFIRM_EMAIL_SALT = 'confirm-email'
RESET_PASSWORD_SALT = 'reset-password'


def get_company_status_message(status):
    messages = {
        CompanyStatus.PENDING: 'Sua empresa ainda está pendente de liberação.',
        CompanyStatus.INACTIVE: 'Sua empresa está inativa no momento.',
        CompanyStatus.BLOCKED: 'Sua empresa foi bloqueada. Entre em contato com o suporte.',
    }
    return messages.get(status, 'Sua empresa não possui acesso liberado no momento.')


def get_register_form_data():
    return {
        'company_name': normalize_text(request.form.get('company_name', '')),
        'cnpj': request.form.get('cnpj', '').strip(),
        'name': normalize_text(request.form.get('name', '')),
        'cpf': request.form.get('cpf', '').strip(),
        'email': request.form.get('email', '').strip().lower(),
    }


def render_register_with_data():
    return render_template('auth/register.html', form_data=get_register_form_data())



def build_absolute_link(endpoint, **values):
    return url_for(endpoint, _external=True, **values)



def send_local_email(subject, recipient, link):
    print(f'[EMAIL SIMULADO] {subject} | para: {recipient} | link: {link}')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Preencha e-mail e senha.', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('E-mail ou senha inválidos.', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('Este usuário está inativo. Entre em contato com o administrador da empresa.', 'warning')
            return render_template('auth/login.html')

        if current_app.config.get('REQUIRE_EMAIL_CONFIRMATION') and not user.email_confirmed:
            flash('Confirme seu e-mail antes de entrar. Use o link enviado no cadastro ou solicite um novo.', 'warning')
            return render_template('auth/login.html')

        company = user.company
        if not company:
            flash('Usuário sem empresa vinculada. Entre em contato com o suporte.', 'danger')
            return render_template('auth/login.html')

        if not company.is_access_allowed:
            flash(get_company_status_message(company.status), 'warning')
            return render_template('auth/login.html')

        login_user(user)

        now = datetime.utcnow()
        user.last_login_at = now
        company.last_activity_at = now
        log_action('login', 'user', user.id, 'Login realizado com sucesso.', company_id=company.id, user_id=user.id)
        db.session.commit()

        flash('Login realizado com sucesso.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        company_name = normalize_text(request.form.get('company_name', ''))
        cnpj = format_cnpj(request.form.get('cnpj', ''))
        name = normalize_text(request.form.get('name', ''))
        cpf = format_cpf(request.form.get('cpf', ''))
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not company_name or not name or not email or not password or not confirm_password or not cpf:
            flash('Preencha todos os campos obrigatórios, incluindo o CPF.', 'danger')
            return render_register_with_data()

        if not is_valid_email(email):
            flash('E-mail inválido.', 'danger')
            return render_register_with_data()

        valid_password, password_error = is_strong_password(password)
        if not valid_password:
            flash(password_error, 'danger')
            return render_register_with_data()

        if password == email:
            flash('A senha não pode ser igual ao e-mail.', 'danger')
            return render_register_with_data()

        if password != confirm_password:
            flash('As senhas não coincidem.', 'danger')
            return render_register_with_data()

        cpf_digits = only_digits(cpf)
        if not cpf_digits or len(cpf_digits) != 11:
            flash('CPF inválido.', 'danger')
            return render_register_with_data()

        cnpj_digits = only_digits(cnpj)
        if cnpj and (not cnpj_digits or len(cnpj_digits) != 14):
            flash('CNPJ inválido.', 'danger')
            return render_register_with_data()

        if User.query.filter_by(email=email).first():
            flash('Já existe um usuário com este e-mail.', 'danger')
            return render_register_with_data()

        if User.query.filter_by(cpf=cpf).first():
            flash('Já existe um usuário com este CPF.', 'danger')
            return render_register_with_data()

        if Company.query.filter_by(name=company_name).first():
            flash('Já existe uma empresa com este nome.', 'danger')
            return render_register_with_data()

        if cnpj and Company.query.filter_by(cnpj=cnpj).first():
            flash('Já existe uma empresa com este CNPJ.', 'danger')
            return render_register_with_data()

        try:
            company = Company(
                name=company_name,
                cnpj=cnpj,
                status=CompanyStatus.PENDING,
                last_activity_at=None,
                trial_ends_at=datetime.utcnow() + timedelta(days=current_app.config.get('TRIAL_DAYS', 7)),
            )
            db.session.add(company)
            db.session.flush()

            user = User(
                name=name,
                email=email,
                cpf=cpf,
                company_id=company.id,
                system_role='company_user',
                company_role='admin_empresa',
                is_active=True,
                email_confirmed=not current_app.config.get('REQUIRE_EMAIL_CONFIRMATION'),
                last_login_at=None,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            log_action('register_company', 'company', company.id, f'Empresa {company.name} criada com status pendente.', company_id=company.id, user_id=user.id)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Não foi possível criar a conta agora. Tente novamente.', 'danger')
            return render_register_with_data()

        confirm_token = generate_token({'user_id': user.id}, CONFIRM_EMAIL_SALT)
        confirm_link = build_absolute_link('auth.confirm_email', token=confirm_token)
        send_local_email('Confirmação de e-mail', user.email, confirm_link)

        if current_app.config.get('REQUIRE_EMAIL_CONFIRMATION'):
            flash('Conta criada com sucesso. Confirmamos o envio do link de confirmação por e-mail.', 'success')
        else:
            flash('Conta criada com sucesso. Aguarde a liberação para acessar o sistema.', 'success')
            flash(f'Link de confirmação local: {confirm_link}', 'info')

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form_data={})


@auth_bp.route('/confirm-email/<token>')
def confirm_email(token):
    try:
        data = read_token(token, CONFIRM_EMAIL_SALT, max_age=60 * 60 * 24)
    except Exception:
        flash('O link de confirmação é inválido ou expirou.', 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.get_or_404(data.get('user_id'))
    if user.email_confirmed:
        flash('Seu e-mail já foi confirmado.', 'info')
        return redirect(url_for('auth.login'))

    user.email_confirmed = True
    log_action('confirm_email', 'user', user.id, 'E-mail confirmado com sucesso.', company_id=user.company_id, user_id=user.id)
    db.session.commit()

    flash('E-mail confirmado com sucesso. Agora você pode entrar quando sua empresa for aprovada.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            token = generate_token({'user_id': user.id}, RESET_PASSWORD_SALT)
            reset_link = build_absolute_link('auth.reset_password', token=token)
            send_local_email('Redefinição de senha', user.email, reset_link)
            flash(f'Link de redefinição gerado para teste local: {reset_link}', 'info')

        flash('Se o e-mail existir na base, o link de redefinição foi gerado.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    try:
        data = read_token(token, RESET_PASSWORD_SALT, max_age=60 * 60 * 2)
    except Exception:
        flash('O link de redefinição é inválido ou expirou.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.get_or_404(data.get('user_id'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        valid_password, password_error = is_strong_password(password)
        if not valid_password:
            flash(password_error, 'danger')
            return render_template('auth/reset_password.html', token=token)

        if password != confirm_password:
            flash('As senhas não coincidem.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        user.set_password(password)
        log_action('reset_password', 'user', user.id, 'Senha redefinida por token.', company_id=user.company_id, user_id=user.id)
        db.session.commit()
        flash('Senha atualizada com sucesso.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/logout')
@login_required
def logout():
    log_action('logout', 'user', current_user.id, 'Logout realizado com sucesso.', company_id=current_user.company_id, user_id=current_user.id)
    db.session.commit()
    logout_user()
    flash('Você saiu da sua conta com sucesso.', 'success')
    return redirect(url_for('auth.login'))
