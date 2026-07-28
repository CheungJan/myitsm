"""ortopbitsmdb → myitsm 数据迁移主入口。

用法:
    uv run python migrate_data.py              # 执行全量迁移
    uv run python migrate_data.py --batch 1    # 仅执行第1批
    uv run python migrate_data.py --dry-run    # 预演模式（不写入）
    uv run python migrate_data.py --validate   # 仅执行校验（不迁移）
"""
from __future__ import annotations

import argparse
import logging
import sys

from app.migration.config import MigrationConfig
from app.migration.batch_runner import BatchRunner
from app.migration.special_handlers import handle_sys_user_merge, handle_password_migration

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="ortopbitsmdb → myitsm 数据迁移")
    parser.add_argument(
        "--batch", type=int, choices=[1, 2, 3, 4, 5], help="仅执行指定批次"
    )
    parser.add_argument("--dry-run", action="store_true", help="预演模式，不实际写入")
    parser.add_argument("--validate", action="store_true", help="仅执行校验（不迁移）")
    args = parser.parse_args()

    config = MigrationConfig.from_env()
    if args.dry_run:
        config.dry_run = True

    logger.info("迁移配置: source=%s", config.source_url.split("@")[-1])
    logger.info("迁移配置: target=%s", config.target_url.split("@")[-1])
    logger.info("批次大小: %d", config.batch_size)
    if config.dry_run:
        logger.info("*** 预演模式：不会实际写入数据 ***")

    runner = BatchRunner(config)
    try:
        if args.validate:
            logger.info("仅执行校验模式（校验由 pytest 测试完成）")
            return

        if args.batch:
            runner.run_batch(args.batch)
        else:
            runner.run_all()

        # 特殊表处理
        logger.info("执行特殊表处理: SYS_USER 合并...")
        handle_sys_user_merge(runner.connector)
        logger.info("执行特殊表处理: 密码迁移...")
        handle_password_migration(runner.connector)

        logger.info("迁移完成！统计：")
        for table, count in sorted(runner._stats.items()):
            logger.info("  %s: %d 行", table, count)
    finally:
        runner.dispose()


if __name__ == "__main__":
    main()
