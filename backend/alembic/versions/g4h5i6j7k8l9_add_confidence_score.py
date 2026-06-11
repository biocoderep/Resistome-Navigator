"""Add ConfidenceScore

Revision ID: g4h5i6j7k8l9
Revises: f3g4h5i6j7k8
Create Date: 2026-06-11 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'g4h5i6j7k8l9'
down_revision = 'f3g4h5i6j7k8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'confidence_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('sample_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('samples.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('analysis_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('context', sa.String(length=50), nullable=False),
        sa.Column('target_name', sa.String(length=200), nullable=False),
        sa.Column('overall_score', sa.Numeric(precision=6, scale=3), nullable=False),
        sa.Column('tier', sa.String(length=50), nullable=False),
        sa.Column('cap_applied', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('components', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('weighted', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    )
    op.create_index('idx_confidence_scores_sample', 'confidence_scores', ['sample_id'])
    op.create_index('idx_confidence_scores_job', 'confidence_scores', ['job_id'])
    op.create_index('idx_confidence_scores_target', 'confidence_scores', ['target_name'])


def downgrade():
    op.drop_index('idx_confidence_scores_target', table_name='confidence_scores')
    op.drop_index('idx_confidence_scores_job', table_name='confidence_scores')
    op.drop_index('idx_confidence_scores_sample', table_name='confidence_scores')
    op.drop_table('confidence_scores')
