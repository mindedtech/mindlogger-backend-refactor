"""Add new input_subject_id to answers

Revision ID: 0adb2ad133d0
Revises: 267dd5b56abf
Create Date: 2024-06-10 15:54:17.466637

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0adb2ad133d0"
down_revision = "267dd5b56abf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "answers",
        sa.Column("input_subject_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        op.f("ix_answers_input_subject_id"),
        "answers",
        ["input_subject_id"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_answers_input_subject_id"), table_name="answers")
    op.drop_column("answers", "input_subject_id")
    # ### end Alembic commands ###