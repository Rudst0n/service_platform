from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "63ad2059fe5f"
down_revision = "86a263342d2c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "company",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name")
    )

    with op.batch_alter_table("customer", schema=None) as batch_op:
        batch_op.add_column(sa.Column("company_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_customer_company_id",
            "company",
            ["company_id"],
            ["id"]
        )

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("company_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_user_company_id",
            "company",
            ["company_id"],
            ["id"]
        )


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_constraint("fk_user_company_id", type_="foreignkey")
        batch_op.drop_column("company_id")

    with op.batch_alter_table("customer", schema=None) as batch_op:
        batch_op.drop_constraint("fk_customer_company_id", type_="foreignkey")
        batch_op.drop_column("company_id")

    op.drop_table("company")