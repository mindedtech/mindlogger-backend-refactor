"""workspase arbitrary extension

Revision ID: 83115d22e7ef
Revises: f90a62f155cc
Create Date: 2023-08-25 21:42:39.747122

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "83115d22e7ef"
down_revision = "f90a62f155cc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "user_applet_accesses",
        "invitor_id",
        existing_type=postgresql.UUID(),
        nullable=True,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "user_applet_accesses",
        "invitor_id",
        existing_type=postgresql.UUID(),
        nullable=False,
    )
    # ### end Alembic commands ###