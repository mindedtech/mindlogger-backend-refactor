"""start_date to DAtetime from Date

Revision ID: 14c4f2e988c5
Revises: 6594a374a3e1
Create Date: 2023-05-26 09:30:57.435693

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "14c4f2e988c5"
down_revision = "6594a374a3e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "periodicity",
        "start_date",
        existing_type=sa.DATE(),
        type_=sa.DateTime(),
        existing_nullable=True,
    )
    op.alter_column(
        "periodicity",
        "end_date",
        existing_type=sa.DATE(),
        type_=sa.DateTime(),
        existing_nullable=True,
    )
    op.alter_column(
        "periodicity",
        "selected_date",
        existing_type=sa.DATE(),
        type_=sa.DateTime(),
        existing_nullable=True,
    )
    op.add_column(
        "notifications",
        sa.Column(
            "order",
            sa.Integer(),
            nullable=True,
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("notifications", "order")
    op.alter_column(
        "periodicity",
        "selected_date",
        existing_type=sa.DateTime(),
        type_=sa.DATE(),
        existing_nullable=True,
    )
    op.alter_column(
        "periodicity",
        "end_date",
        existing_type=sa.DateTime(),
        type_=sa.DATE(),
        existing_nullable=True,
    )
    op.alter_column(
        "periodicity",
        "start_date",
        existing_type=sa.DateTime(),
        type_=sa.DATE(),
        existing_nullable=True,
    )
    # ### end Alembic commands ###