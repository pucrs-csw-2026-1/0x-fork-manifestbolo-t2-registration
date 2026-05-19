"""create_registration_slots_table

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-05-19 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "g7b8c9d0e1f2"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria a tabela de vínculo entre inscrições e slots de evento."""
    op.create_table(
        "registration_slots",
        sa.Column("slot_id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["slot_id"],
            ["event_slots.slot_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["event_id", "user_id"],
            ["registrations.event_id", "registrations.user_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("slot_id", "event_id", "user_id"),
    )

    op.create_index(
        "ix_registration_slots_event_user",
        "registration_slots",
        ["event_id", "user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_registration_slots_event_user", table_name="registration_slots")
    op.drop_table("registration_slots")
