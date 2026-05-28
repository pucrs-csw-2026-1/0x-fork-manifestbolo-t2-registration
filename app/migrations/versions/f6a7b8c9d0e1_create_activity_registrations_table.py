"""create_activity_registrations_table

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-05-27 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the user activity registration table."""
    op.create_table(
        "activity_registrations",
        sa.Column("activity_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("activity_id", "user_id"),
    )
    op.create_index(
        "ix_activity_registrations_event_user",
        "activity_registrations",
        ["event_id", "user_id"],
    )
    op.execute(
        """
        CREATE FUNCTION set_activity_registrations_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_activity_registrations_updated_at
        BEFORE UPDATE ON activity_registrations
        FOR EACH ROW
        EXECUTE FUNCTION set_activity_registrations_updated_at()
        """
    )


def downgrade() -> None:
    """Drop the user activity registration table."""
    op.execute(
        "DROP TRIGGER IF EXISTS trg_activity_registrations_updated_at "
        "ON activity_registrations"
    )
    op.execute("DROP FUNCTION IF EXISTS set_activity_registrations_updated_at()")
    op.drop_index(
        "ix_activity_registrations_event_user",
        table_name="activity_registrations",
    )
    op.drop_table("activity_registrations")
