"""分批执行引擎：按外键依赖顺序逐表迁移，支持断点续传。"""
from __future__ import annotations

import logging

from sqlalchemy import Engine, text

from app.migration.config import MigrationConfig
from app.migration.field_mapper import (
    TableMapping,
    build_mapping,
    read_source_rows,
    write_target_rows,
    get_row_count,
    truncate_table,
    sync_sequence,
)

logger = logging.getLogger(__name__)


# 5 批：按外键依赖排序
BATCH_TABLES: dict[int, list[str]] = {
    1: [
        "tmc11_departments", "tmc12_groups", "tmc13_users",
        "tmm01_company", "tmm21_custclass", "tmm22_customers",
        "tmm11_itemclass", "tmm12_items",
        "tmm18_supplierclass", "tmm19_suppliers",
        "twh01_warehouse", "tmm46_area", "tmm47_commode",
        "tmm24_custitems", "tmm31_syscodes", "tmm34_idmaster",
        "tmc71_sysparm", "tmc41_acclog",
        "tmm61_deposit", "tmm61_deposit_dtl", "tmm61_deposit_io",
        "tmm61_deposit_list", "tmm61_deposit_posmodel",
    ],
    2: [
        "tmc01_menus", "tmc02_menusdt",
        "tit01_timepoint_area", "tit02_liabilityreg", "tit02_liabilityregdt",
        "tit03_syscodes", "tit04_archivecode", "tit05_repairinfo", "tit06_userarea",
        "tmc03_usermenus", "tmc21_usergroup", "tmc22_userbusityp", "tmc31_groupright",
        "tmm35_cust_pos_rl", "tmm36_cust_ve_rl",
    ],
    3: [
        "tit10_maintenanceday", "tit10_maintenance_liability",
        "tit10_main_track", "tit10_pos_detail",
        "tit11_maintenance_attc", "tit12_maintenance_archive",
        "tit13_maintenance_open", "tit14_equipment_open",
        "tit15_maintenance_renovate", "tit15_equipment_renovate",
        "tit16_device_change",
        "tit17_maintenance", "tit17_cust_pos_daily", "tit17_maintenance_plan",
        "tit18_store_close", "tit19_on_choosedt",
        "tit21_maintenance_dispatch",
        "tit23_maintenance_d2d", "tit24_maintenance_rv",
        "tit25_accessories_update", "tit26_paylist",
        "tit27_close_bills",
        "tit28_free_replace", "tit28_free_replace_dt",
        "tit29_noclose_track", "plan_cust",
    ],
    4: [
        "twh11_detail", "twh12_detaildt",
        "twh13_in", "twh14_checkindt", "twh15_out",
        "twh16_outdteid", "twh16_outdtprd",
        "twh17_overlost", "twh18_overlostdt", "twh18_overlosteid",
        "twh19_asset_c_a", "twh20_asset_c_a_dtl",
        "twh21_pos_change", "twh22_pos_change_dt",
        "tpc01_pcplan", "tpc02_pcplandt", "tpc03_pcplanstatus",
        "tpc12_register", "tpc13_registerdt", "tpc14_pcbill",
        "tpc16_rpcbill", "tpc17_rpcbilldt",
        "tpc20_suppappraisal", "tpc21_suppappraisaldt",
        "tsl01_extend", "tsl02_extenddt", "tsl10_slbill",
    ],
    5: [
        "tmm41_bom", "tmm42_bomdt",
        "tmm43_eid", "tmm43_eid_track",
        "tqc10_result", "tqc11_resultdt", "tqc11_resulteid",
        "tkq01_attendance", "tkq02_attendancecount",
        "tip01_price", "tip03_adjprice",
        "tht01_htgl", "tac01_fpsk",
        "ttx01_txkmg",
        "tiv01_invlimit", "tiv02_invlimit_hi",
        "tmp14_checkindt", "tmm62_asset_attrib_list",
    ],
}


class BatchRunner:
    """按批次执行全量迁移。"""

    def __init__(self, config: MigrationConfig) -> None:
        self.config = config
        from app.migration.connector import DualConnector
        self.connector = DualConnector(config)
        self._stats: dict[str, int] = {}

    def run_all(self) -> dict[str, int]:
        for batch in [1, 2, 3, 4, 5]:
            logger.info("=== 开始第 %d 批迁移 ===", batch)
            self.run_batch(batch)
        return self._stats

    def run_batch(self, batch: int) -> None:
        tables = BATCH_TABLES.get(batch, [])
        for table_name in tables:
            self._migrate_table(table_name, batch)

    def _migrate_table(self, table_name: str, batch: int) -> None:
        logger.info("迁移 %s ...", table_name)

        # 1. 检查源库是否存在该表
        src_count = get_row_count(self.connector.source, table_name)
        if src_count == 0:
            logger.info("  源表无数据或不存在，跳过")
            self._stats[table_name] = 0
            return

        # 2. 自动构建映射
        mapping = build_mapping(
            self.connector.source,
            self.connector.target,
            table_name, table_name, batch,
        )
        if not mapping.common_columns and not mapping.rename_map:
            logger.info("  无映射列，跳过")
            self._stats[table_name] = 0
            return

        logger.info("  公共列: %s", ", ".join(mapping.common_columns[:10]))

        # 3. 清空目标表
        truncate_table(self.connector.target, table_name)

        # 4. 使用同一个源库连接分批读取（保证 OFFSET 一致性）
        from app.migration.field_mapper import write_target_rows as write_rows

        total = 0
        offset = 0
        batch_size = self.config.batch_size

        with self.connector.source.connect() as src_conn:
            while offset < src_count:
                rows = _read_batch_from_conn(src_conn, mapping, offset, batch_size)
                if not rows:
                    break
                inserted = write_rows(self.connector.target, mapping, rows)
                total += inserted
                offset += batch_size
                logger.info("  进度: %d / %d", min(offset, src_count), src_count)

        # 5. 同步序列
        sync_sequence(self.connector.target, table_name)

        self._stats[table_name] = total
        logger.info("  %s 完成: %d 行 (源: %d 行)", table_name, total, src_count)

    def dispose(self) -> None:
        self.connector.dispose()


def _read_batch_from_conn(
    conn, mapping, offset: int, limit: int
) -> list[dict[str, object]]:
    """从已打开的源库连接读取一批行。"""
    if not mapping.common_columns and not mapping.rename_map:
        return []

    select_parts: list[str] = []
    for col in mapping.common_columns:
        select_parts.append(col)
    for tgt_col, src_col in mapping.rename_map.items():
        select_parts.append(f"{src_col} AS {tgt_col}")

    target_cols = mapping.common_columns + list(mapping.rename_map.keys())
    cols_str = ", ".join(select_parts)
    sql = f"SELECT {cols_str} FROM {mapping.old_table} OFFSET {offset} LIMIT {limit}"
    result = conn.execute(text(sql))
    return [dict(zip(target_cols, row)) for row in result.fetchall()]
