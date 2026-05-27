"""create_confirmation_tokens_table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-19 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria a tabela auxiliar de tokens de confirmação de inscrição."""
    op.create_table(
        "confirmation_tokens",
        # PK: identificador único desta solicitação de confirmação
        sa.Column("confirmation_id", sa.Uuid(), nullable=False),

        # Referência ao usuário e ao evento (par que identifica a inscrição)
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),

        # Código alfanumérico de 6 ou 8 caracteres gerado pelo backend
        sa.Column("codigo", sa.String(length=8), nullable=False),

        # Controle de ciclo de vida
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,  # preenchido quando a confirmação é realizada
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint("confirmation_id"),
    )

    # Índice para busca rápida por usuário + evento (evita duplicatas em andamento)
    op.create_index(
        "ix_confirmation_tokens_user_event",
        "confirmation_tokens",
        ["user_id", "event_id"],
    )


def downgrade() -> None:
    """Remove a tabela de tokens de confirmação."""
    op.drop_index("ix_confirmation_tokens_user_event", table_name="confirmation_tokens")
    op.drop_table("confirmation_tokens")
