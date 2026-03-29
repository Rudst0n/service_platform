import click
from getpass import getpass

from app.extensions import db
from app.models.user import User
from app.models.company import Company, CompanyStatus


@click.command("create-super-admin")
@click.option("--email", prompt=True)
@click.option("--name", prompt=True)
def create_super_admin(email, name):
    password = getpass("Senha: ")
    confirm = getpass("Confirmar senha: ")

    if password != confirm:
        click.echo("As senhas não coincidem.")
        return

    existing = User.query.filter_by(email=email.strip().lower()).first()
    if existing:
        click.echo("Já existe um usuário com esse e-mail.")
        return

    company = Company(
        name=f"Admin {name.strip()}",
        status=CompanyStatus.ACTIVE,
        is_active=True,
    )
    db.session.add(company)
    db.session.flush()

    user = User(
        name=name.strip(),
        email=email.strip().lower(),
        system_role="super_admin",
        company_role="admin_empresa",
        company_id=company.id,
        is_active=True,
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    click.echo("Super admin criado com sucesso.")
