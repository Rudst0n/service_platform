from flask import flash, redirect, url_for
from flask_login import current_user


def block_if_trial_expired(resource_name='ações'):
    company = getattr(current_user, 'company', None)
    if company and company.trial_expired:
        flash(
            f'O período de teste expirou. Você ainda pode acessar o sistema, mas não pode criar ou editar {resource_name} até a renovação.',
            'warning',
        )
        return redirect(url_for('main.dashboard'))
    return None
