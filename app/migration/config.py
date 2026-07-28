"""双库连接配置，从环境变量加载。"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class MigrationConfig:
    source_url: str
    target_url: str
    batch_size: int = 5000
    dry_run: bool = False

    @classmethod
    def from_env(cls) -> MigrationConfig:
        source_url = os.getenv("SOURCE_DATABASE_URL")
        if not source_url:
            raise ValueError("SOURCE_DATABASE_URL 环境变量未设置（旧库 ortopbitsmdb）")
        target_url = os.getenv("DATABASE_URL")
        if not target_url:
            raise ValueError("DATABASE_URL 环境变量未设置（新库 myitsm）")
        batch_size = int(os.getenv("MIGRATION_BATCH_SIZE", "5000"))
        dry_run = os.getenv("MIGRATION_DRY_RUN", "0") == "1"
        return cls(
            source_url=source_url,
            target_url=target_url,
            batch_size=batch_size,
            dry_run=dry_run,
        )
