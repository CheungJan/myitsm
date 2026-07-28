"""重新迁移有问题的表。"""
from __future__ import annotations

import logging

from app.migration.config import MigrationConfig
from app.migration.batch_runner import BatchRunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 问题表清单
PROBLEM_TABLES = [
    "tmm19_suppliers",
    "tmm46_area",
    "tmm34_idmaster",
    "tmc71_sysparm",
    "tpc14_pcbill",
    "tpc16_rpcbill",
    "tpc17_rpcbilldt",
    "tpc20_suppappraisal",
    "tpc21_suppappraisaldt",
    "tqc11_resultdt",
]


def main() -> None:
    config = MigrationConfig.from_env()
    logger.info("重新迁移 %d 个问题表", len(PROBLEM_TABLES))

    from app.migration.connector import DualConnector
    connector = DualConnector(config)
    from app.migration.field_mapper import (
        build_mapping, read_source_rows, write_target_rows,
        get_row_count, truncate_table, sync_sequence,
    )

    for tbl in PROBLEM_TABLES:
        logger.info("=== 重新迁移 %s ===", tbl)
        src_count = get_row_count(connector.source, tbl)
        if src_count == 0:
            logger.info("  源表无数据，跳过")
            continue

        mapping = build_mapping(connector.source, connector.target, tbl, tbl)
        logger.info("  同名列: %s", mapping.common_columns)
        logger.info("  重命名: %s", mapping.rename_map)

        if not mapping.common_columns and not mapping.rename_map:
            logger.info("  无映射列，跳过")
            continue

        truncate_table(connector.target, tbl)

        offset = 0
        total = 0
        while offset < src_count:
            rows = read_source_rows(connector.source, mapping, offset, config.batch_size)
            if not rows:
                break
            inserted = write_target_rows(connector.target, mapping, rows)
            total += inserted
            offset += config.batch_size
            logger.info("  进度: %d / %d (已写 %d)", min(offset, src_count), src_count, total)

        sync_sequence(connector.target, tbl)
        logger.info("  %s 完成: %d / %d 行", tbl, total, src_count)

    connector.dispose()


if __name__ == "__main__":
    main()
