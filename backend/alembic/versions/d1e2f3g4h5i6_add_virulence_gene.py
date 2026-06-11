"""Add VirulenceGene

Revision ID: d1e2f3g4h5i6
Revises: cb89ab372f91
Create Date: 2026-06-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd1e2f3g4h5i6'
down_revision = 'cb89ab372f91'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'virulence_genes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('sample_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('samples.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('analysis_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('gene_name', sa.String(length=200), nullable=False),
        sa.Column('virulence_factor', sa.String(length=200), nullable=True),
        sa.Column('mechanism', sa.String(length=200), nullable=True),
        sa.Column('contig_id', sa.String(length=200), nullable=True),
        sa.Column('start_position', sa.Integer(), nullable=True),
        sa.Column('end_position', sa.Integer(), nullable=True),
        sa.Column('identity_percent', sa.Numeric(precision=6, scale=3), nullable=True),
        sa.Column('coverage_percent', sa.Numeric(precision=6, scale=3), nullable=True),
        sa.Column('database_source', sa.String(length=100), nullable=True),
    )
    op.create_index('idx_virulence_genes_sample', 'virulence_genes', ['sample_id'])
    op.create_index('idx_virulence_genes_job', 'virulence_genes', ['job_id'])
    op.create_index('idx_virulence_genes_name', 'virulence_genes', ['gene_name'])


def downgrade():
    op.drop_index('idx_virulence_genes_name', table_name='virulence_genes')
    op.drop_index('idx_virulence_genes_job', table_name='virulence_genes')
    op.drop_index('idx_virulence_genes_sample', table_name='virulence_genes')
    op.drop_table('virulence_genes')
