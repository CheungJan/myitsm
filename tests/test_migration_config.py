import pytest
from app.migration.config import MigrationConfig


class TestMigrationConfig:
    def test_loads_from_environment(self, monkeypatch):
        monkeypatch.setenv("SOURCE_DATABASE_URL", "postgresql://user:pass@host:5432/ortopbitsmdb")
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/myitsm")
        config = MigrationConfig.from_env()
        assert config.source_url == "postgresql://user:pass@host:5432/ortopbitsmdb"
        assert config.target_url == "postgresql://user:pass@localhost:5432/myitsm"

    def test_missing_source_url_raises(self, monkeypatch):
        monkeypatch.delenv("SOURCE_DATABASE_URL", raising=False)
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/myitsm")
        with pytest.raises(ValueError, match="SOURCE_DATABASE_URL"):
            MigrationConfig.from_env()

    def test_missing_target_url_raises(self, monkeypatch):
        monkeypatch.setenv("SOURCE_DATABASE_URL", "postgresql://host/ortopbitsmdb")
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(ValueError, match="DATABASE_URL"):
            MigrationConfig.from_env()

    def test_batch_size_default(self, monkeypatch):
        monkeypatch.setenv("SOURCE_DATABASE_URL", "postgresql://host/ortopbitsmdb")
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/myitsm")
        config = MigrationConfig.from_env()
        assert config.batch_size == 5000

    def test_batch_size_custom(self, monkeypatch):
        monkeypatch.setenv("SOURCE_DATABASE_URL", "postgresql://host/ortopbitsmdb")
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/myitsm")
        monkeypatch.setenv("MIGRATION_BATCH_SIZE", "1000")
        config = MigrationConfig.from_env()
        assert config.batch_size == 1000


class TestDualConnector:
    def test_engines_created_on_demand(self, monkeypatch):
        monkeypatch.setenv("SOURCE_DATABASE_URL", "sqlite:///:memory:")
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
        from app.migration.connector import DualConnector
        from app.migration.config import MigrationConfig
        config = MigrationConfig.from_env()
        connector = DualConnector(config)
        assert connector._source_engine is None
        _ = connector.source
        assert connector._source_engine is not None
        connector.dispose()

    def test_row_count_returns_int(self, monkeypatch):
        from sqlalchemy import text
        monkeypatch.setenv("SOURCE_DATABASE_URL", "sqlite:///:memory:")
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
        from app.migration.connector import DualConnector
        from app.migration.config import MigrationConfig
        config = MigrationConfig.from_env()
        connector = DualConnector(config)
        with connector.source.connect() as conn:
            conn.execute(text("CREATE TABLE test_table (id INTEGER)"))
            conn.execute(text("INSERT INTO test_table VALUES (1), (2), (3)"))
            conn.commit()
        count = connector.source_row_count("test_table")
        assert count == 3
        connector.dispose()
