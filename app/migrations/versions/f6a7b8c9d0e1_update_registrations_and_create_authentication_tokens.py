"""update_registrations_and_create_authentication_tokens

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-05-21 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Update registrations and replace confirmation tokens with auth tokens."""
    with op.batch_alter_table("registrations") as batch_op:
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(length=32),
                server_default=sa.text("'REGISTERED'"),
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True)
        )

    op.execute(
        """
        UPDATE registrations
        SET
            status = CASE
                WHEN confirmation_timestamp IS NULL THEN 'REGISTERED'
                ELSE 'CONFIRMED'
            END,
            created_at = registration_timestamp,
            updated_at = confirmation_timestamp
        """
    )

    with op.batch_alter_table("registrations") as batch_op:
        batch_op.drop_column("confirmation_timestamp")
        batch_op.drop_column("registration_timestamp")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_registrations_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_registrations_updated_at
        BEFORE UPDATE ON registrations
        FOR EACH ROW
        EXECUTE FUNCTION set_registrations_updated_at();
        """
    )

    op.drop_index("ix_confirmation_tokens_user_event", table_name="confirmation_tokens")
    op.drop_table("confirmation_tokens")

    op.create_table(
        "authentication_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(length=8), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id", "user_id"],
            ["registrations.event_id", "registrations.user_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Restore the old registrations schema and confirmation tokens table."""
    op.drop_table("authentication_tokens")

    with op.batch_alter_table("registrations") as batch_op:
        batch_op.add_column(
            sa.Column("confirmation_timestamp", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "registration_timestamp",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            )
        )

    op.execute(
        """
        UPDATE registrations
        SET
            registration_timestamp = created_at,
            confirmation_timestamp = CASE
                WHEN status = 'CONFIRMED' THEN updated_at
                ELSE NULL
            END
        """
    )

    op.execute("DROP TRIGGER IF EXISTS trg_registrations_updated_at ON registrations")
    op.execute("DROP FUNCTION IF EXISTS set_registrations_updated_at()")

    with op.batch_alter_table("registrations") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")
        batch_op.drop_column("status")

    op.create_table(
        "confirmation_tokens",
        sa.Column("confirmation_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("codigo", sa.String(length=8), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("confirmation_id"),
    )
    op.create_index(
        "ix_confirmation_tokens_user_event",
        "confirmation_tokens",
        ["user_id", "event_id"],
    )
