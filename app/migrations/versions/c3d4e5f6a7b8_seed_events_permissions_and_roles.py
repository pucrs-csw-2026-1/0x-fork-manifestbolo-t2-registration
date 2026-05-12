"""seed_events_permissions_and_roles

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-05-10 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixed UUIDs — stable across environments, required for clean downgrade.
PERM_EVENT_VIEW = "11111111-0000-0000-0000-000000000001"
PERM_EVENT_CREATE = "11111111-0000-0000-0000-000000000002"
PERM_EVENT_UPDATE = "11111111-0000-0000-0000-000000000003"
PERM_EVENT_DELETE = "11111111-0000-0000-0000-000000000004"

ROLE_PARTICIPANT = "22222222-0000-0000-0000-000000000001"
ROLE_ORGANIZER = "22222222-0000-0000-0000-000000000002"
ROLE_ADMINISTRATOR = "22222222-0000-0000-0000-000000000003"

RP_PARTICIPANT_VIEW = "33333333-0000-0000-0000-000000000001"
RP_ORGANIZER_VIEW = "33333333-0000-0000-0000-000000000002"
RP_ORGANIZER_CREATE = "33333333-0000-0000-0000-000000000003"
RP_ORGANIZER_UPDATE = "33333333-0000-0000-0000-000000000004"
RP_ADMIN_VIEW = "33333333-0000-0000-0000-000000000005"
RP_ADMIN_CREATE = "33333333-0000-0000-0000-000000000006"
RP_ADMIN_UPDATE = "33333333-0000-0000-0000-000000000007"
RP_ADMIN_DELETE = "33333333-0000-0000-0000-000000000008"

_permissions_table = sa.table(
    "permissions",
    sa.column("id", sa.Uuid()),
    sa.column("name", sa.String()),
    sa.column("description", sa.Text()),
)

_roles_table = sa.table(
    "roles",
    sa.column("id", sa.Uuid()),
    sa.column("name", sa.String()),
    sa.column("description", sa.Text()),
)

_role_permissions_table = sa.table(
    "role_permissions",
    sa.column("id", sa.Uuid()),
    sa.column("role_id", sa.Uuid()),
    sa.column("permission_id", sa.Uuid()),
)


def upgrade() -> None:
    """Insert seed permissions, roles and their associations."""
    op.bulk_insert(
        _permissions_table,
        [
            {"id": PERM_EVENT_VIEW, "name": "event:view", "description": "Can view events"},
            {"id": PERM_EVENT_CREATE, "name": "event:create", "description": "Can create events"},
            {"id": PERM_EVENT_UPDATE, "name": "event:update", "description": "Can update events"},
            {"id": PERM_EVENT_DELETE, "name": "event:delete", "description": "Can delete events"},
        ],
    )

    op.bulk_insert(
        _roles_table,
        [
            {"id": ROLE_PARTICIPANT, "name": "participant", "description": "Standard participant role"},
            {"id": ROLE_ORGANIZER, "name": "organizer", "description": "Organizer role for event creators"},
            {"id": ROLE_ADMINISTRATOR, "name": "administrator", "description": "Administrator with full access"},
        ],
    )

    op.bulk_insert(
        _role_permissions_table,
        [
            # participant: event:view only
            {"id": RP_PARTICIPANT_VIEW, "role_id": ROLE_PARTICIPANT, "permission_id": PERM_EVENT_VIEW},
            # organizer: event:view, event:create, event:update
            {"id": RP_ORGANIZER_VIEW, "role_id": ROLE_ORGANIZER, "permission_id": PERM_EVENT_VIEW},
            {"id": RP_ORGANIZER_CREATE, "role_id": ROLE_ORGANIZER, "permission_id": PERM_EVENT_CREATE},
            {"id": RP_ORGANIZER_UPDATE, "role_id": ROLE_ORGANIZER, "permission_id": PERM_EVENT_UPDATE},
            # administrator: all four
            {"id": RP_ADMIN_VIEW, "role_id": ROLE_ADMINISTRATOR, "permission_id": PERM_EVENT_VIEW},
            {"id": RP_ADMIN_CREATE, "role_id": ROLE_ADMINISTRATOR, "permission_id": PERM_EVENT_CREATE},
            {"id": RP_ADMIN_UPDATE, "role_id": ROLE_ADMINISTRATOR, "permission_id": PERM_EVENT_UPDATE},
            {"id": RP_ADMIN_DELETE, "role_id": ROLE_ADMINISTRATOR, "permission_id": PERM_EVENT_DELETE},
        ],
    )


def downgrade() -> None:
    """Remove all rows inserted by this seed."""
    all_rp_ids = ", ".join(f"'{i}'" for i in [
        RP_PARTICIPANT_VIEW,
        RP_ORGANIZER_VIEW, RP_ORGANIZER_CREATE, RP_ORGANIZER_UPDATE,
        RP_ADMIN_VIEW, RP_ADMIN_CREATE, RP_ADMIN_UPDATE, RP_ADMIN_DELETE,
    ])
    op.execute(sa.text(f"DELETE FROM role_permissions WHERE id IN ({all_rp_ids})"))
    op.execute(sa.text(
        f"DELETE FROM roles WHERE id IN ('{ROLE_PARTICIPANT}', '{ROLE_ORGANIZER}', '{ROLE_ADMINISTRATOR}')"
    ))
    op.execute(sa.text(
        f"DELETE FROM permissions WHERE id IN ('{PERM_EVENT_VIEW}', '{PERM_EVENT_CREATE}',"
        f"'{PERM_EVENT_UPDATE}', '{PERM_EVENT_DELETE}')"
    ))
