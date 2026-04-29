from app.extensions import db
from app.models.user import User


def login(client, login_value="admin@teste.com", password="Senha@123"):
    return client.post(
        "/auth/login",
        data={
            "login": login_value,
            "password": password,
        },
        follow_redirects=True,
    )


def assert_logged_in(response):
    assert response.status_code == 200
    assert b"Entrar | ServHub" not in response.data


def create_employee_user(
    company_id,
    name="Funcionario Extra",
    email="func.extra@gmail.com",
    cpf="333.444.555-66",
):
    user = User(
        name=name,
        email=email,
        cpf=cpf,
        system_role="company_user",
        company_role="funcionario",
        company_id=company_id,
        is_active=True,
        email_confirmed=True,
        must_change_password=False,
    )
    user.set_password("Senha@123")
    db.session.add(user)
    db.session.commit()
    return user.id


def test_admin_can_create_user_post(client, app, admin_user, company):
    assert_logged_in(login(client))

    response = client.post(
        "/users/new",
        data={
            "name": "Novo Usuario",
            "email": "novo.usuario@gmail.com",
            "cpf": "98765432100",
            "password": "Senha@123",
            "confirm_password": "Senha@123",
            "company_role": "funcionario",
            "is_active": "on",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        created = User.query.filter_by(
            email="novo.usuario@gmail.com",
            company_id=company.id,
        ).first()
        assert created is not None
        assert created.name == "Novo Usuario"
        assert created.company_role == "funcionario"
        assert created.is_active is True


def test_create_user_requires_required_fields(client, admin_user):
    assert_logged_in(login(client))

    response = client.post(
        "/users/new",
        data={
            "name": "",
            "email": "",
            "password": "",
            "confirm_password": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Preencha todos os campos obrigat" in response.data


def test_create_user_rejects_invalid_email(client, admin_user):
    assert_logged_in(login(client))

    response = client.post(
        "/users/new",
        data={
            "name": "Usuario Invalido",
            "email": "email-invalido",
            "cpf": "12345678901",
            "password": "Senha@123",
            "confirm_password": "Senha@123",
            "company_role": "funcionario",
            "is_active": "on",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"E-mail inv" in response.data


def test_create_user_rejects_duplicate_email(client, app, company, admin_user):
    with app.app_context():
        create_employee_user(
            company_id=company.id,
            name="Ja Existe",
            email="duplicado@gmail.com",
            cpf="444.555.666-77",
        )

    assert_logged_in(login(client))

    response = client.post(
        "/users/new",
        data={
            "name": "Outro Usuario",
            "email": "duplicado@gmail.com",
            "cpf": "99988877766",
            "password": "Senha@123",
            "confirm_password": "Senha@123",
            "company_role": "funcionario",
            "is_active": "on",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        users = User.query.filter_by(
            email="duplicado@gmail.com",
            company_id=company.id,
        ).all()

        assert len(users) == 1
        assert users[0].name == "Ja Existe"


def test_admin_can_edit_user(client, app, company, admin_user):
    with app.app_context():
        user_id = create_employee_user(
            company_id=company.id,
            name="Usuario Antigo",
            email="usuario.antigo@gmail.com",
            cpf="555.666.777-88",
        )

    assert_logged_in(login(client))

    response = client.post(
        f"/users/edit/{user_id}",
        data={
            "name": "Usuario Editado",
            "email": "usuario.editado@gmail.com",
            "cpf": "55566677788",
            "company_role": "visualizador",
            "is_active": "on",
            "password": "",
            "confirm_password": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        updated = db.session.get(User, user_id)
        assert updated is not None
        assert updated.name == "Usuario Editado"
        assert updated.email == "usuario.editado@gmail.com"
        assert updated.company_role == "visualizador"
        assert updated.is_active is True


def test_edit_user_can_change_password(client, app, company, admin_user):
    with app.app_context():
        user_id = create_employee_user(
            company_id=company.id,
            name="Usuario Senha",
            email="usuario.senha@gmail.com",
            cpf="666.777.888-99",
        )

    assert_logged_in(login(client))

    response = client.post(
        f"/users/edit/{user_id}",
        data={
            "name": "Usuario Senha",
            "email": "usuario.senha@gmail.com",
            "cpf": "66677788899",
            "company_role": "funcionario",
            "is_active": "on",
            "password": "NovaSenha@123",
            "confirm_password": "NovaSenha@123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        updated = db.session.get(User, user_id)
        assert updated is not None
        assert updated.check_password("NovaSenha@123") is True


def test_admin_can_update_user_role(client, app, company, admin_user):
    with app.app_context():
        user_id = create_employee_user(
            company_id=company.id,
            name="Usuario Papel",
            email="usuario.papel@gmail.com",
            cpf="777.888.999-00",
        )

    assert_logged_in(login(client))

    response = client.post(
        f"/users/{user_id}/update-role",
        data={
            "company_role": "visualizador",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        updated = db.session.get(User, user_id)
        assert updated is not None
        assert updated.company_role == "visualizador"


def test_admin_can_toggle_user_status(client, app, company, admin_user):
    with app.app_context():
        user_id = create_employee_user(
            company_id=company.id,
            name="Usuario Status",
            email="usuario.status@gmail.com",
            cpf="888.999.000-11",
        )

    assert_logged_in(login(client))

    response = client.post(
        f"/users/{user_id}/toggle-status",
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        updated = db.session.get(User, user_id)
        assert updated is not None
        assert updated.is_active is False


def test_admin_cannot_toggle_own_status(client, app, admin_user):
    assert_logged_in(login(client))

    response = client.post(
        f"/users/{admin_user.id}/toggle-status",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"pr\xc3\xb3prio status" in response.data.lower()

    with app.app_context():
        updated = db.session.get(User, admin_user.id)
        assert updated is not None
        assert updated.is_active is True


def test_admin_can_reset_user_password(client, app, company, admin_user):
    with app.app_context():
        user_id = create_employee_user(
            company_id=company.id,
            name="Usuario Reset",
            email="usuario.reset@gmail.com",
            cpf="999.000.111-22",
        )

    assert_logged_in(login(client))

    response = client.post(
        f"/users/{user_id}/reset-password",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Senha redefinida com sucesso" in response.data

    with app.app_context():
        updated = db.session.get(User, user_id)
        assert updated is not None
        assert updated.must_change_password is True


def test_admin_cannot_reset_own_password_from_admin_action(client, app, admin_user):
    assert_logged_in(login(client))

    response = client.post(
        f"/users/{admin_user.id}/reset-password",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Use a op\xc3\xa7\xc3\xa3o de altera\xc3\xa7\xc3\xa3o de senha" in response.data

    with app.app_context():
        updated = db.session.get(User, admin_user.id)
        assert updated is not None
        assert updated.must_change_password is False


def test_admin_can_delete_user(client, app, company, admin_user):
    with app.app_context():
        user_id = create_employee_user(
            company_id=company.id,
            name="Usuario Excluir",
            email="usuario.excluir@gmail.com",
            cpf="111.222.333-44",
        )

    assert_logged_in(login(client))

    response = client.post(
        f"/users/delete/{user_id}",
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        deleted = db.session.get(User, user_id)
        assert deleted is None


def test_admin_cannot_delete_own_user(client, app, admin_user):
    assert_logged_in(login(client))

    response = client.post(
        f"/users/delete/{admin_user.id}",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"n\xc3\xa3o pode excluir seu pr\xc3\xb3prio usu" in response.data.lower()

    with app.app_context():
        updated = db.session.get(User, admin_user.id)
        assert updated is not None


def test_visualizador_cannot_access_users_new_route(client, visualizador_user):
    assert_logged_in(login(client, "visualizador@teste.com"))

    response = client.get("/users/new", follow_redirects=True)

    assert response.status_code == 403