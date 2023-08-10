"""Update answers with event sync fields

Revision ID: 071cca4a1aa4
Revises: f41d934e88f9
Create Date: 2023-08-10 23:36:43.956482

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "071cca4a1aa4"
down_revision = "f41d934e88f9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "answers", sa.Column("is_flow_completed", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "answers_items",
        sa.Column("scheduled_event_id", sa.Text(), nullable=True),
    )
    op.add_column(
        "answers_items", sa.Column("local_end_date", sa.Date(), nullable=True)
    )
    op.add_column(
        "answers_items", sa.Column("local_end_time", sa.Time(), nullable=True)
    )
    op.create_index(
        op.f("ix_answers_items_local_end_date"),
        "answers_items",
        ["local_end_date"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        op.f("ix_answers_items_local_end_date"), table_name="answers_items"
    )
    op.drop_column("answers_items", "local_end_time")
    op.drop_column("answers_items", "local_end_date")
    op.drop_column("answers_items", "scheduled_event_id")
    op.drop_column("answers", "is_flow_completed")
    # ### end Alembic commands ###
