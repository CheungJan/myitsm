"""双 PostgreSQL 连接器：旧库只读 + 新库读写。"""
from __future__ import annotations

from sqlalchemy import Engine, create_engine, text

from app.migration.config import MigrationConfig


class DualConnector:
    """管理 ortopbitsmdb（源）和 myitsm（目标）两个 PG 库连接。"""

    def __init__(self, config: MigrationConfig) -> None:
        self.config = config
        self._source_engine: Engine | None = None
        self._target_engine: Engine | None = None

    @property
    def source(self) -> Engine:
        """旧库 ortopbitsmdb（只读）。"""
        if self._source_engine is None:
            self._source_engine = create_engine(
                self.config.source_url,
                echo=False,
                pool_size=1,
            )
        return self._source_engine

    @property
    def target(self) -> Engine:
        """新库 myitsm（读写）。"""
        if self._target_engine is None:
            self._target_engine = create_engine(
                self.config.target_url,
                echo=False,
                pool_size=5,
            )
        return self._target_engine

    def source_row_count(self, table_name: str) -> int:
        """获取源库表行数。"""
        with self.source.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar_one()

    def target_row_count(self, table_name: str) -> int:
        """获取目标库表行数。"""
        with self.target.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar_one()

    def target_truncate(self, table_name: str) -> None:
        """清空目标表（CASCADE）。"""
        if self.config.dry_run:
            return
        with self.target.connect() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
            conn.commit()

    def dispose(self) -> None:
        """释放所有连接。"""
        if self._source_engine:
            self._source_engine.dispose()
        if self._target_engine:
            self._target_engine.dispose()
