"""Add ResistanceMutation

Revision ID: e2f3g4h5i6j7
Revises: d1e2f3g4h5i6
Create Date: 2026-06-11 10:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e2f3g4h5i6j7'
down_revision = 'd1e2f3g4h5i6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'resistance_mutations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('sample_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('samples.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('analysis_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('gene_name', sa.String(length=200), nullable=False),
        sa.Column('mutation', sa.String(length=100), nullable=False),
        sa.Column('mechanism', sa.String(length=200), nullable=True),
        sa.Column('effect', sa.String(length=200), nullable=True),
        sa.Column('identity_percent', sa.Numeric(precision=6, scale=3), nullable=True),
        sa.Column('coverage_percent', sa.Numeric(precision=6, scale=3), nullable=True),
        sa.Column('database_source', sa.String(length=100), nullable=True),
    )
    op.create_index('idx_resistance_mutations_sample', 'resistance_mutations', ['sample_id'])
    op.create_index('idx_resistance_mutations_job', 'resistance_mutations', ['job_id'])
    op.create_index('idx_resistance_mutations_gene', 'resistance_mutations', ['gene_name'])


def downgrade():
    op.drop_index('idx_resistance_mutations_gene', table_name='resistance_mutations')
    op.drop_index('idx_resistance_mutations_job', table_name='resistance_mutations')
    op.drop_index('idx_resistance_mutations_sample', table_name='resistance_mutations')
    op.drop_table('resistance_mutations')
