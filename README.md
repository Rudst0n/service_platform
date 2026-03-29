# ServHub

SaaS de gestão de serviços construído em Flask, com foco em operação simples, uso local para validação do MVP e base pronta para evoluir para produção.

## O que está pronto nesta versão

- multiempresa com isolamento por empresa
- cadastro, login e logout
- aprovação manual de empresas pelo painel do super admin
- gestão de clientes, funcionários e serviços
- controle de perfis por empresa
- limite por plano
- teste grátis de 7 dias cadastrado na empresa
- bloqueio de novas criações quando o teste expira
- redefinição de senha por token
- confirmação de e-mail por token, preparada para uso local e integração futura com SMTP
- auditoria das ações principais
- validação de upload de imagem com Pillow
- headers básicos de segurança
- configuração separada por ambiente

## Stack

- Python 3
- Flask
- Flask Login
- Flask SQLAlchemy
- Flask Migrate
- Flask WTF
- SQLite para ambiente local
- HTML, CSS e JavaScript

## Estrutura principal

```text
app/
  blueprints/
  models/
  static/
  templates/
  utils/
migrations/
instance/
run.py
requirements.txt
.env.example
```

## Como rodar localmente

1. Crie e ative um ambiente virtual.
2. Instale as dependências.
3. Copie `.env.example` para `.env`.
4. Rode as migrations.
5. Inicie a aplicação.

### Comandos

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask db upgrade
python run.py
```

A aplicação abre em:

```text
http://127.0.0.1:5000
```

## Super admin

Para criar um super admin local:

```bash
flask create-super-admin
```

## Observações importantes

- Por padrão, o ambiente local deixa `REQUIRE_EMAIL_CONFIRMATION=0` para facilitar testes.
- Mesmo assim, os links de confirmação e redefinição são gerados e exibidos no flash e no terminal.
- Para forçar confirmação de e-mail, altere `.env` para `REQUIRE_EMAIL_CONFIRMATION=1`.
- Para produção, troque o `DATABASE_URL` para PostgreSQL e configure envio real de e-mails.

## Checklist rápido de teste

1. Criar conta de empresa.
2. Criar super admin.
3. Aprovar a empresa no painel admin.
4. Entrar com a conta da empresa.
5. Cadastrar cliente.
6. Cadastrar funcionário.
7. Cadastrar serviço.
8. Testar troca de status.
9. Testar upload e exclusão de imagem.
10. Testar redefinição de senha.

## Melhorias futuras sugeridas

- integração real de e-mail com SMTP
- captcha no cadastro
- cobrança e assinatura
- relatórios exportáveis
- painel visual para auditoria
- testes automatizados
