"""allow null company role for super admin"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5d525a59c894"
down_revision = "9c2f6b1d4a77"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column(
            "company_role",
            existing_type=sa.String(length=50),
            nullable=True
        )


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column(
            "company_role",
            existing_type=sa.String(length=50),
            nullable=False
        )