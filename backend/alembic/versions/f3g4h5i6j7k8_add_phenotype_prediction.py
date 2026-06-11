"""Add PhenotypePrediction

Revision ID: f3g4h5i6j7k8
Revises: e2f3g4h5i6j7
Create Date: 2026-06-11 10:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f3g4h5i6j7k8'
down_revision = 'e2f3g4h5i6j7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'phenotype_predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('sample_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('samples.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('analysis_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('drug', sa.String(length=200), nullable=False),
        sa.Column('drug_class', sa.String(length=200), nullable=True),
        sa.Column('predicted_sir', sa.String(length=50), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=6, scale=3), nullable=True),
        sa.Column('confidence_tier', sa.String(length=50), nullable=True),
        sa.Column('breakpoint_source', sa.String(length=100), nullable=True),
        sa.Column('breakpoint_version', sa.String(length=100), nullable=True),
        sa.Column('is_not_testable', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('has_conflict', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('supporting_genes', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('supporting_mutations', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('explanation', sa.String(), nullable=True),
    )
    op.create_index('idx_phenotype_preds_sample', 'phenotype_predictions', ['sample_id'])
    op.create_index('idx_phenotype_preds_job', 'phenotype_predictions', ['job_id'])
    op.create_index('idx_phenotype_preds_drug', 'phenotype_predictions', ['drug'])


def downgrade():
    op.drop_index('idx_phenotype_preds_drug', table_name='phenotype_predictions')
    op.drop_index('idx_phenotype_preds_job', table_name='phenotype_predictions')
    op.drop_index('idx_phenotype_preds_sample', table_name='phenotype_predictions')
    op.drop_table('phenotype_predictions')
