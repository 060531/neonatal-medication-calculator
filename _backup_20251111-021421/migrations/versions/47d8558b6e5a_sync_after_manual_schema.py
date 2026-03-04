"""no-op sync after manual schema (fixed)"""

from alembic import op
import sqlalchemy as sa

# Alembic identifiers
revision = "47d8558b6e5a"
down_revision = "114c6b58e00a"
branch_labels = None
depends_on = None


def upgrade():
    # Database schema already in-sync; nothing to do.
    pass


def downgrade():
    # Nothing to undo because upgrade did nothing.
    pass
