"""Add genome validation tables

Revision ID: add_genome_validation
Revises: 80cff0f3dfab
Create Date: 2026-06-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_genome_validation'
down_revision: Union[str, Sequence[str], None] = '80cff0f3dfab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create assemblies table
    op.create_table(
        'assemblies',
        sa.Column('sample_id', sa.UUID(), nullable=False),
        sa.Column('assembler', sa.String(length=100), nullable=True),
        sa.Column('assembly_version', sa.String(length=50), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='UPLOADED', nullable=False),
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['sample_id'], ['samples.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_assemblies_sample', 'assemblies', ['sample_id'], unique=False)

    # Create assembly_metrics table
    op.create_table(
        'assembly_metrics',
        sa.Column('assembly_id', sa.UUID(), nullable=False),
        sa.Column('total_length_bp', sa.Integer(), nullable=False),
        sa.Column('contig_count', sa.Integer(), nullable=False),
        sa.Column('mean_contig_bp', sa.Float(), nullable=False),
        sa.Column('median_contig_bp', sa.Float(), nullable=False),
        sa.Column('max_contig_bp', sa.Integer(), nullable=False),
        sa.Column('min_contig_bp', sa.Integer(), nullable=False),
        sa.Column('n50_bp', sa.Integer(), nullable=False),
        sa.Column('n90_bp', sa.Integer(), nullable=False),
        sa.Column('l50', sa.Integer(), nullable=False),
        sa.Column('gc_percent', sa.Float(), nullable=False),
        sa.Column('n_percent', sa.Float(), nullable=False),
        sa.Column('assembly_span_bp', sa.Integer(), nullable=False),
        sa.Column('quality_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('quality_classification', sa.String(length=20), nullable=True),
        sa.Column('confidence_cap', sa.String(length=20), server_default='FULL', nullable=False),
        sa.Column('contamination_risk', sa.String(length=20), nullable=True),
        sa.Column('contamination_signals', sa.JSON(), nullable=True),
        sa.Column('gc_outlier_contigs', sa.JSON(), nullable=True),
        sa.Column('gc_variance', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('gc_std_dev', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('duplicate_pairs', sa.Integer(), server_default='0', nullable=False),
        sa.Column('mean_shannon_entropy', sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column('kmer_coverage_estimate', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('taxonomy_status', sa.String(length=30), nullable=True),
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assembly_id'], ['assemblies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_assembly_metrics_assembly', 'assembly_metrics', ['assembly_id'], unique=False)

    # Create validation_reports table
    op.create_table(
        'validation_reports',
        sa.Column('assembly_id', sa.UUID(), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=True),
        sa.Column('validation_status', sa.String(length=10), nullable=False),
        sa.Column('quality_score', sa.Float(), nullable=False),
        sa.Column('quality_class', sa.String(length=20), nullable=False),
        sa.Column('proceed_to_amr', sa.Boolean(), nullable=False),
        sa.Column('confidence_cap', sa.String(length=20), nullable=False),
        sa.Column('full_report', sa.JSON(), nullable=True),
        sa.Column('errors', sa.JSON(), nullable=True),
        sa.Column('warnings', sa.JSON(), nullable=True),
        sa.Column('override_status', sa.String(length=20), nullable=True),
        sa.Column('override_by', sa.String(length=100), nullable=True),
        sa.Column('override_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assembly_id'], ['assemblies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_validation_reports_assembly', 'validation_reports', ['assembly_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_validation_reports_assembly', table_name='validation_reports')
    op.drop_table('validation_reports')
    op.drop_index('idx_assembly_metrics_assembly', table_name='assembly_metrics')
    op.drop_table('assembly_metrics')
    op.drop_index('idx_assemblies_sample', table_name='assemblies')
    op.drop_table('assemblies')
