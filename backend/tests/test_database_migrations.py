import os
import sys
import tempfile
from pathlib import Path
import pytest
from sqlalchemy import create_engine, inspect
from alembic.config import Config
from alembic import command

BACKEND_DIR = Path(__file__).resolve().parent.parent

def test_alembic_upgrade_downgrade_lifecycle():
    """
    D5 / GAP-009: Verifies full Alembic migration lifecycle on a fresh isolated database:
    1. upgrade head creates all 5 tables.
    2. downgrade base removes all tables.
    3. upgrade head idempotently restores the schema.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db_path = Path(tmp_dir) / "migration_test.db"
        test_db_url = f"sqlite:///{test_db_path.as_posix()}"

        alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)

        # 1. Execute Upgrade to Head
        command.upgrade(alembic_cfg, "head")

        engine = create_engine(test_db_url)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        expected_tables = {"email_records", "analysis_results", "evidence_vault", "campaigns", "alerts", "alembic_version"}
        assert expected_tables.issubset(tables), f"Missing tables after upgrade head: {expected_tables - tables}"

        # Verify key columns on email_records and evidence_vault
        email_cols = {col["name"] for col in inspector.get_columns("email_records")}
        assert "sha256_hash" in email_cols
        assert "message_id" in email_cols
        assert "source" in email_cols

        evidence_cols = {col["name"] for col in inspector.get_columns("evidence_vault")}
        assert "chain_of_custody_id" in evidence_cols
        assert "chain_entries" in evidence_cols
        assert "last_entry_hash" in evidence_cols

        # 2. Execute Downgrade to Base
        command.downgrade(alembic_cfg, "base")
        inspector_post_downgrade = inspect(engine)
        tables_post_downgrade = set(inspector_post_downgrade.get_table_names()) - {"alembic_version"}
        assert len(tables_post_downgrade) == 0, f"Expected 0 tables after downgrade base, got {tables_post_downgrade}"

        # 3. Re-upgrade to Head (Idempotency Proof)
        command.upgrade(alembic_cfg, "head")
        inspector_reup = inspect(engine)
        reup_tables = set(inspector_reup.get_table_names())
        assert expected_tables.issubset(reup_tables)

        engine.dispose()
