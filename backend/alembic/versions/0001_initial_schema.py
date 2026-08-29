"""0001_initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-30 02:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create email_records
    op.create_table(
        'email_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('message_id', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=False, server_default='(No Subject)'),
        sa.Column('sender', sa.String(length=255), nullable=False),
        sa.Column('sender_domain', sa.String(length=255), nullable=True),
        sa.Column('recipient', sa.String(length=255), nullable=True),
        sa.Column('date', sa.DateTime(), nullable=True),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('raw_content_path', sa.String(length=500), nullable=True),
        sa.Column('raw_headers', sa.JSON(), nullable=True),
        sa.Column('sha256_hash', sa.String(length=64), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=True, server_default='eml_upload'),
        sa.Column('ingested_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='processed'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('email_records', schema=None) as batch_op:
        batch_op.create_index('ix_email_records_id', ['id'], unique=False)
        batch_op.create_index('ix_email_records_message_id', ['message_id'], unique=False)
        batch_op.create_index('ix_email_records_subject', ['subject'], unique=False)
        batch_op.create_index('ix_email_records_sender', ['sender'], unique=False)
        batch_op.create_index('ix_email_records_sender_domain', ['sender_domain'], unique=False)
        batch_op.create_index('ix_email_records_recipient', ['recipient'], unique=False)
        batch_op.create_index('ix_email_records_sha256_hash', ['sha256_hash'], unique=False)

    # 2. Create analysis_results
    op.create_table(
        'analysis_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email_id', sa.String(length=36), nullable=False),
        sa.Column('overall_threat_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('threat_level', sa.String(length=20), nullable=False, server_default='LOW'),
        sa.Column('primary_classification', sa.String(length=50), nullable=False, server_default='legitimate'),
        sa.Column('classification_confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('model_contributions', sa.JSON(), nullable=True),
        sa.Column('auth_spf', sa.JSON(), nullable=True),
        sa.Column('auth_dkim', sa.JSON(), nullable=True),
        sa.Column('auth_dmarc', sa.JSON(), nullable=True),
        sa.Column('header_anomalies', sa.JSON(), nullable=True),
        sa.Column('relay_hops_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('relay_path', sa.JSON(), nullable=True),
        sa.Column('earliest_reliable_hop', sa.JSON(), nullable=True),
        sa.Column('content_analysis', sa.JSON(), nullable=True),
        sa.Column('domain_intel', sa.JSON(), nullable=True),
        sa.Column('origin_assessment', sa.JSON(), nullable=True),
        sa.Column('attribution_assessment', sa.JSON(), nullable=True),
        sa.Column('threat_intel_matches', sa.JSON(), nullable=True),
        sa.Column('recommendations', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['email_id'], ['email_records.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email_id')
    )
    with op.batch_alter_table('analysis_results', schema=None) as batch_op:
        batch_op.create_index('ix_analysis_results_id', ['id'], unique=False)

    # 3. Create evidence_vault
    op.create_table(
        'evidence_vault',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email_id', sa.String(length=36), nullable=False),
        sa.Column('sha256_hash', sa.String(length=64), nullable=False),
        sa.Column('stored_path', sa.String(length=500), nullable=False),
        sa.Column('chain_of_custody_id', sa.String(length=50), nullable=False),
        sa.Column('chain_entries', sa.JSON(), nullable=False),
        sa.Column('last_entry_hash', sa.String(length=64), nullable=False),
        sa.Column('is_sealed', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['email_id'], ['email_records.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email_id')
    )
    with op.batch_alter_table('evidence_vault', schema=None) as batch_op:
        batch_op.create_index('ix_evidence_vault_id', ['id'], unique=False)
        batch_op.create_index('ix_evidence_vault_chain_of_custody_id', ['chain_of_custody_id'], unique=False)

    # 4. Create campaigns
    op.create_table(
        'campaigns',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('threat_level', sa.String(length=20), nullable=True, server_default='HIGH'),
        sa.Column('actor_sophistication', sa.String(length=50), nullable=True, server_default='medium'),
        sa.Column('infrastructure_cluster', sa.JSON(), nullable=True),
        sa.Column('first_seen', sa.DateTime(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('total_emails', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('iocs', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('campaigns', schema=None) as batch_op:
        batch_op.create_index('ix_campaigns_id', ['id'], unique=False)

    # 5. Create alerts
    op.create_table(
        'alerts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('threat_score', sa.Float(), nullable=False),
        sa.Column('is_acknowledged', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['email_id'], ['email_records.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('alerts', schema=None) as batch_op:
        batch_op.create_index('ix_alerts_id', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('alerts')
    op.drop_table('campaigns')
    op.drop_table('evidence_vault')
    op.drop_table('analysis_results')
    op.drop_table('email_records')
