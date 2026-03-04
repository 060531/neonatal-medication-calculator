from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '61c10be41e68'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = set(insp.get_table_names())

    # --- access_logs -> access_log ---
    if 'access_log' not in existing and 'access_logs' in existing:
        op.rename_table('access_logs', 'access_log')
        existing.add('access_log')
    if 'access_log' not in existing:
        op.create_table(
            'access_log',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('path', sa.String(length=255)),
            sa.Column('method', sa.String(length=10)),
        )
        existing.add('access_log')

    # --- drugs -> drug ---
    if 'drug' not in existing and 'drugs' in existing:
        op.rename_table('drugs', 'drug')
        existing.add('drug')
    if 'drug' not in existing:
        op.create_table(
            'drug',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('name', sa.String(length=128), nullable=False, unique=True),
        )
        existing.add('drug')

    # --- compatibility alterations (SQLite-friendly) ---
    if 'compatibility' in existing:
        cols = {c['name']: c for c in insp.get_columns('compatibility')}
        with op.batch_alter_table('compatibility') as batch_op:
            if 'a' not in cols:
                batch_op.add_column(sa.Column('a', sa.String(length=64)))
            if 'b' not in cols:
                batch_op.add_column(sa.Column('b', sa.String(length=64)))

            if 'status' in cols:
                batch_op.alter_column(
                    'status',
                    type_=sa.String(length=10),
                    existing_type=sa.String(length=32),
                    existing_nullable=True
                )

            for old_col in ('note','co_drug_id','drug_id'):
                if old_col in cols:
                    batch_op.drop_column(old_col)

def downgrade():
    # no-op (safe)
    pass
