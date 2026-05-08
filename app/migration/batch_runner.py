"""分批执行引擎：按外键依赖顺序逐表迁移，支持断点续传。"""
from __future__ import annotations

import logging
from sqlalchemy import text

from app.migration.config import MigrationConfig
from app.migration.connector import DualConnector
from app.migration.field_mapper import (
    MAPPINGS,
    TableMapping,
    get_mappings_by_batch,
    map_source_row,
)

logger = logging.getLogger(__name__)


class BatchRunner:
    """按批次执行全量迁移。"""

    def __init__(self, config: MigrationConfig) -> None:
        self.config = config
        self.connector = DualConnector(config)
        self._completed: set[str] = set()
        self._stats: dict[str, int] = {}

    def run_all(self) -> dict[str, int]:
        """执行全部 5 批迁移，返回统计。"""
        for batch in [1, 2, 3, 4, 5]:
            logger.info("=== 开始第 %d 批迁移 ===", batch)
            self.run_batch(batch)
        return self._stats

    def run_batch(self, batch: int) -> None:
        """执行单批迁移。"""
        mappings = sorted(
            get_mappings_by_batch(batch),
            key=lambda m: len(m.depends_on),
        )
        for mapping in mappings:
            if mapping.old_table in self._completed:
                continue
            self._migrate_table(mapping)
            self._completed.add(mapping.old_table)

    def _migrate_table(self, mapping: TableMapping) -> None:
        """迁移单张表。"""
        logger.info("迁移 %s → %s ...", mapping.old_table, mapping.new_table)

        # 1. 检查源表是否有数据
        source_count = self.connector.source_row_count(mapping.old_table)
        if source_count == 0:
            logger.info("  源表无数据，跳过")
            self._stats[mapping.new_table] = 0
            return

        # 2. 清空目标表（TRUNCATE CASCADE）
        self.connector.target_truncate(mapping.new_table)

        # 3. 分批读取并写入
        offset = 0
        total_inserted = 0
        while offset < source_count:
            rows = self._read_source_batch(mapping, offset, self.config.batch_size)
            if not rows:
                break
            inserted = self._write_target_batch(mapping, rows)
            total_inserted += inserted
            offset += self.config.batch_size
            logger.info("  进度: %d / %d", min(offset, source_count), source_count)

        # 4. 更新序列（自增ID）
        self._sync_sequence(mapping.new_table)

        self._stats[mapping.new_table] = total_inserted
        logger.info(
            "  %s 完成: %d 行 (源: %d 行)",
            mapping.new_table,
            total_inserted,
            source_count,
        )

    def _read_source_batch(
        self, mapping: TableMapping, offset: int, limit: int
    ) -> list[dict[str, object]]:
        """从源库分批读取原始行。"""
        col_list = [
            fm.old_name
            for fm in mapping.fields
            if fm.old_name is not None
        ]
        if not col_list:
            return []
        columns = ", ".join(c for c in col_list)
        sql = (
            f"SELECT {columns} FROM {mapping.old_table} "
            f"OFFSET {offset} LIMIT {limit}"
        )
        with self.connector.source.connect() as conn:
            result = conn.execute(text(sql))
            return [dict(zip(col_list, row)) for row in result.fetchall()]

    def _write_target_batch(
        self, mapping: TableMapping, rows: list[dict[str, object]]
    ) -> int:
        """向目标库批量写入映射后的行。"""
        if not rows or self.config.dry_run:
            return 0
        new_rows = [map_source_row(mapping, row) for row in rows]
        columns = list(new_rows[0].keys())
        col_names = ", ".join(columns)
        placeholders = ", ".join([f":{c}" for c in columns])
        sql = (
            f"INSERT INTO {mapping.new_table} ({col_names}) "
            f"VALUES ({placeholders})"
        )
        with self.connector.target.connect() as conn:
            result = conn.execute(text(sql), new_rows)
            conn.commit()
            return result.rowcount

    def _sync_sequence(self, table_name: str) -> None:
        """将序列值同步到当前最大ID之后。"""
        if self.config.dry_run:
            return
        try:
            sql = text(
                "SELECT setval(pg_get_serial_sequence(:tbl, 'id'), "
                "COALESCE((SELECT MAX(id) FROM {tbl}), 0) + 1, false)"
                .format(tbl=table_name)
            )
            with self.connector.target.connect() as conn:
                conn.execute(sql, {"tbl": table_name})
                conn.commit()
        except Exception:
            pass

    def dispose(self) -> None:
        self.connector.dispose()
