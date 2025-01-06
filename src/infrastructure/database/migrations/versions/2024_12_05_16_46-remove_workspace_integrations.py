"""Remove workspace.integrations

Revision ID: dc2dd9e195d5
Revises: ab98161f1973
Create Date: 2024-12-05 16:46:12.341839

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "dc2dd9e195d5"
down_revision = "ab98161f1973"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("applets", "integrations")
    op.drop_column("users_workspaces", "integrations")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "users_workspaces",
        sa.Column("integrations", postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    )
    op.add_column(
        "applets",
        sa.Column("integrations", postgresql.ARRAY(sa.VARCHAR(length=32)), autoincrement=False, nullable=True),
    )
    # ### end Alembic commands ###