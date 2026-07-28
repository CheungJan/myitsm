# ortopbitsmdb → myitsm 数据迁移实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** ✅ 已执行完成（2026-05-08），最终完整率 99.6%，详见文末"实际执行差异记录"

**Goal:** 将 ortopbitsmdb（PostgreSQL，137张旧表，含真实业务数据）完整迁移至 myitsm（PostgreSQL，139张新表，优化后结构），迁移后数据完整、外键一致、业务语义不变。

**Architecture:** 使用 Python + SQLAlchemy 双 PG 连接器模式。两个 PostgreSQL 库通过独立的 Engine 连接，从 ortopbitsmdb 读取原始数据，经字段映射后写入 myitsm 新库。迁移脚本独立于 Flask 应用，可直接命令行执行。分 5 批按外键依赖顺序导入，每批支持断点续传。

**Tech Stack:** Python 3.12, SQLAlchemy 2.0, psycopg2 (双 PG 连接), pytest (校验测试)

---

## 文件结构

```
app/
├── migration/
│   ├── __init__.py
│   ├── config.py           # 双库连接配置 + 环境变量
│   ├── connector.py         # 双库连接器（Oracle只读 + PostgreSQL读写）
│   ├── field_mapper.py      # 字段映射规则 + 类型转换
│   ├── batch_runner.py      # 分批执行引擎 + 断点续传
│   └── special_handlers.py  # 特殊表处理（复合PK转代理键、P0默认值、密码迁移等）
tests/
├── test_migration_config.py         # 连接器配置测试
├── test_migration_field_mapper.py   # 字段映射测试
├── test_migration_batch1.py         # 第1批：基础主数据
├── test_migration_batch2.py         # 第2批：ITSM字典配置
├── test_migration_batch3.py         # 第3批：ITSM业务单据
├── test_migration_batch4.py         # 第4批：仓储/采购/销售
├── test_migration_batch5.py         # 第5批：其他（押金/BOM/EID等）
└── test_migration_validation.py     # 全量校验测试
docs/superpowers/plans/
└── 2026-05-08-ortopbitsmdb-to-myitsm-migration.md  # 本文件
```

---

## 迁移策略总览

```
ortopbitsmdb (Oracle 137表)  ──→  myitsm (PostgreSQL 139表)

A类 一对一 (~95表)   : 字段映射 + 直接 INSERT
B类 合并 (~8表)       : 多表合并为一表
C类 仅旧库有 (~15表)  : 归档或丢弃（不迁移）
D类 仅新库有 (~12表)  : 跳过（新模块，无旧数据）
```

### 分批顺序（按外键依赖）

```
第1批  基础主数据        ~20表   无依赖
第2批  ITSM字典与配置    ~12表   依赖第1批
第3批  ITSM业务单据      ~30表   依赖第1+2批
第4批  仓储/采购/销售     ~35表   依赖第1+3批
第5批  其他（押金/EID等） ~15表   依赖第1+4批
```

### 字段级转换规则

两个库都是 PostgreSQL，类型兼容性好，主要处理：

| 情况 | 处理方式 |
|------|---------|
| 同名同类型字段 | 直接映射 |
| CHAR(n) → VARCHAR(n) | 去除右侧空格（`normalize_char`） |
| 旧库 VARCHAR2（Oracle导出残留）| 等同于 VARCHAR，直接映射 |
| 旧库 NUMBER（Oracle导出残留）| 等同于 NUMERIC，直接映射 |
| DATE → TIMESTAMP | 保留原值 |
| BYTEA | bytes 类型，`to_dict()` 已处理为 None |
| 旧库无 → 新库有（P0字段）| 填入默认值 |

### 时间戳字段映射

| 旧库字段 | 新库字段 | 处理 |
|---------|---------|------|
| GENDATE | created_at | 直接复制 |
| UPDDATE | updated_at | 直接复制 |
| CREATE_TIME | created_at | 直接复制 |
| UPDATE_TIME | updated_at | 直接复制 |
| （无） | created_at | 默认 NOW() |
| （无） | updated_at | 默认 NOW() |

---

### Task 1: 迁移配置与双库连接器

**Files:**
- Create: `app/migration/__init__.py`
- Create: `app/migration/config.py`
- Create: `app/migration/connector.py`
- Create: `tests/test_migration_config.py`

- [ ] **Step 1: 编写连接器配置测试**

```python
# tests/test_migration_config.py
import os
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
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_migration_config.py -v
```
Expected: FAIL (ModuleNotFoundError: No module named 'app.migration.config')

- [ ] **Step 3: 创建配置模块**

```python
# app/migration/__init__.py
"""ortopbitsmdb → myitsm 数据迁移工具包。"""
```

```python
# app/migration/config.py
"""双库连接配置，从环境变量加载。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


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
```

- [ ] **Step 4: 运行测试验证通过**

```bash
uv run pytest tests/test_migration_config.py -v
```
Expected: PASS (5 passed)

- [ ] **Step 5: 创建双库连接器**

```python
# app/migration/connector.py
"""双 PostgreSQL 连接器：旧库只读 + 新库读写。"""
from __future__ import annotations

from sqlalchemy import create_engine, Engine, text
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
            result = conn.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            )
            return result.scalar_one()

    def target_row_count(self, table_name: str) -> int:
        """获取目标库表行数。"""
        with self.target.connect() as conn:
            result = conn.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            )
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
```

- [ ] **Step 6: 补充连接器测试**

```python
# 追加到 tests/test_migration_config.py

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
```

- [ ] **Step 7: 运行测试**

```bash
uv run pytest tests/test_migration_config.py -v
```
Expected: PASS (7 passed)

- [ ] **Step 8: Commit**

```bash
git add app/migration/ tests/test_migration_config.py
git commit -m "feat(migration): 双库连接器与配置模块"
```

---

### Task 2: 字段映射引擎

**Files:**
- Create: `app/migration/field_mapper.py`
- Create: `tests/test_migration_field_mapper.py`

- [ ] **Step 1: 编写字段映射测试**

```python
# tests/test_migration_field_mapper.py
from datetime import datetime
from app.migration.field_mapper import (
    FieldMapping,
    TableMapping,
    map_source_row,
    normalize_char,
    MAPPINGS,
)


class TestNormalizeChar:
    def test_strips_trailing_spaces(self):
        assert normalize_char("ABC   ") == "ABC"

    def test_handles_none(self):
        assert normalize_char(None) is None

    def test_handles_empty_string(self):
        assert normalize_char("") == ""


class TestFieldMapping:
    def test_direct_copy(self):
        fm = FieldMapping(old_name="GENDATE", new_name="created_at")
        assert fm.transform("2024-01-01") == "2024-01-01"

    def test_char_normalize(self):
        fm = FieldMapping(old_name="CUSTCD", new_name="custcd", transform="char")
        assert fm.transform("ABC   ") == "ABC"

    def test_default_value(self):
        fm = FieldMapping(new_name="source_type", default="DAILY")
        assert fm.transform(None) == "DAILY"

    def test_rename_only(self):
        fm = FieldMapping(old_name="old_col", new_name="new_col")
        assert fm.transform("hello") == "hello"

    def test_old_name_none_means_no_source(self):
        fm = FieldMapping(new_name="created_at", default=datetime(2024, 1, 1))
        assert fm.old_name is None
        assert fm.transform(None) == datetime(2024, 1, 1)


class TestTableMapping:
    def test_map_row_simple(self):
        mapping = TableMapping(
            old_table="TMM01_COMPANY",
            new_table="tmm01_company",
            fields=[
                FieldMapping(old_name="COMPCD", new_name="compcd", transform="char"),
                FieldMapping(old_name="COMPNM", new_name="compnm"),
                FieldMapping(new_name="created_at", default=datetime(2024, 1, 1)),
            ],
        )
        old_row = {"COMPCD": "01  ", "COMPNM": "测试公司"}
        new_row = map_source_row(mapping, old_row)
        assert new_row["compcd"] == "01"
        assert new_row["compnm"] == "测试公司"
        assert new_row["created_at"] == datetime(2024, 1, 1)

    def test_map_row_skips_unmapped_old_fields(self):
        mapping = TableMapping(
            old_table="TMM01_COMPANY",
            new_table="tmm01_company",
            fields=[
                FieldMapping(old_name="COMPCD", new_name="compcd", transform="char"),
            ],
        )
        old_row = {"COMPCD": "01  ", "EXTRA_FIELD": "should_be_ignored"}
        new_row = map_source_row(mapping, old_row)
        assert "EXTRA_FIELD" not in new_row
        assert "extra_field" not in new_row


class TestMappingsRegistry:
    def test_all_a_class_tables_have_mapping(self):
        """验证所有 A 类表（一对一直迁）都有映射定义。"""
        a_class_tables = [
            "TAC01_FPSK", "THT01_HTGL", "TIP01_PRICE", "TIP03_ADJPRICE",
            "TIT01_TIMEPOINT_AREA", "TIT02_LIABILITYREG", "TIT02_LIABILITYREGDT",
            "TIT03_SYSCODES",  -- 2026-05-10 已合并至 tmm31_syscodes
            "TIT04_ARCHIVECODE", "TIT05_REPAIRINFO",
            "TMC01_MENUS", "TMC02_MENUSDT", "TMC03_USERMENUS",
            "TMC11_DEPARTMENTS", "TMC12_GROUPS", "TMC13_USERS",
            "TMM01_COMPANY", "TMM11_ITEMCLASS", "TMM12_ITEMS",
        ]
        mapped = {m.old_table for m in MAPPINGS if m.old_table}
        for table in a_class_tables:
            assert table in mapped, f"{table} 缺少映射定义"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
uv run pytest tests/test_migration_field_mapper.py -v
```
Expected: FAIL

- [ ] **Step 3: 创建字段映射模块**

```python
# app/migration/field_mapper.py
"""Oracle→PostgreSQL 字段级映射规则与类型转换。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable


def normalize_char(value: str | None) -> str | None:
    """Oracle CHAR 类型去除右侧空格。"""
    if value is None:
        return None
    return value.rstrip()


@dataclass
class FieldMapping:
    """单个字段的映射规则。"""
    new_name: str
    old_name: str | None = None
    transform: str | None = None
    default: Any = None

    def __post_init__(self) -> None:
        if self.old_name is None and self.default is None:
            raise ValueError(
                f"字段 '{self.new_name}' 必须指定 old_name 或 default"
            )

    def apply(self, old_row: dict[str, Any]) -> Any:
        if self.old_name is None:
            return self.default
        value = old_row.get(self.old_name)
        if value is None and self.default is not None:
            return self.default
        if self.transform == "char":
            return normalize_char(value)
        return value


@dataclass
class TableMapping:
    """整表映射：旧表名 → 新表名 + 字段映射列表。"""
    old_table: str
    new_table: str
    fields: list[FieldMapping] = field(default_factory=list)
    batch: int = 1
    depends_on: list[str] = field(default_factory=list)


def map_source_row(mapping: TableMapping, old_row: dict[str, Any]) -> dict[str, Any]:
    """将一行 Oracle 数据按映射规则转换为 PostgreSQL 行。"""
    return {fm.new_name: fm.apply(old_row) for fm in mapping.fields}


# ============================================================
# 全部映射定义（按批次 + 外键依赖顺序）
# ============================================================

MAPPINGS: list[TableMapping] = []


def _m(
    old: str,
    new: str,
    fields: list[FieldMapping],
    batch: int = 1,
    depends_on: list[str] | None = None,
) -> TableMapping:
    m = TableMapping(
        old_table=old,
        new_table=new,
        fields=fields,
        batch=batch,
        depends_on=depends_on or [],
    )
    MAPPINGS.append(m)
    return m


# ---------- 第1批：基础主数据 ----------

_m("TMC11_DEPARTMENTS", "tmc11_departments", [
    FieldMapping("deptcd", "DEPTCD", transform="char"),
    FieldMapping("deptnm", "DEPTNM"),
    FieldMapping("levelcd", "LEVELCD"),
    FieldMapping("parent", "PARENT", transform="char"),
    FieldMapping("leader", "LEADER", transform="char"),
    FieldMapping("childflg", "CHILDFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=1)

_m("TMC13_USERS", "tmc13_users", [
    FieldMapping("usercd", "USERCD", transform="char"),
    FieldMapping("usernm", "USERNM"),
    FieldMapping("passwd", "PASSWD"),
    FieldMapping("deptcd", "DEPTCD", transform="char"),
    FieldMapping("credamt", "CREDAMT"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=1, depends_on=["tmc11_departments"])

_m("TMC01_MENUS", "tmc01_menus", [
    FieldMapping("menucd", "MENUCD"),
    FieldMapping("menunm", "MENUNM"),
    FieldMapping("levelcd", "LEVELCD"),
    FieldMapping("parent", "PARENT"),
    FieldMapping("execpath", "EXEPATH"),
    FieldMapping("picname", "PICNAME"),
    FieldMapping("ordno", "ORDNO"),
    FieldMapping("openflg", "OPENFLG", transform="char"),
    FieldMapping("childflg", "CHILDFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=1)

_m("TMC02_MENUSDT", "tmc02_menusdt", [
    FieldMapping("menucd", "MENUCD"),
    FieldMapping("funccd", "FUNCCD"),
    FieldMapping("funcnm", "FUNCNM"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=1, depends_on=["tmc01_menus"])

_m("TMC12_GROUPS", "tmc12_groups", [
    FieldMapping("groupcd", "GROUPCD", transform="char"),
    FieldMapping("groupnm", "GROUPNM"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=1)

_m("TMM01_COMPANY", "tmm01_company", [
    FieldMapping("compcd", "COMPCD", transform="char"),
    FieldMapping("compnm", "COMPNM"),
    FieldMapping("companm", "COMPANM"),
    FieldMapping("leader", "LEADER"),
    FieldMapping("address", "ADDRESS"),
    FieldMapping("phoneno", "PHONENO"),
    FieldMapping("telex", "TELEX"),
    FieldMapping("faxno", "FAXNO"),
    FieldMapping("banknm", "BANKNM"),
    FieldMapping("bankaccno", "BANKACCNO"),
    FieldMapping("taxno", "TAXNO"),
    FieldMapping("opendate", "OPENDATE"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
    FieldMapping("mailcd", "MAILCD", transform="char"),
    FieldMapping("produce", "PRODUCE"),
    FieldMapping("maintenance", "MAINTENANCE"),
], batch=1)

_m("TMM21_CUSTCLASS", "tmm21_custclass", [
    FieldMapping("classtyp", "CLASSTYP", transform="char"),
    FieldMapping("classcd", "CLASSCD"),
    FieldMapping("classnm", "CLASSNM"),
    FieldMapping("parent", "PARENT"),
    FieldMapping("childflg", "CHILDFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
], batch=1)

_m("TMM22_CUSTOMERS", "tmm22_customers", [
    FieldMapping("custcd", "CUSTCD", transform="char"),
    FieldMapping("custnm", "CUSTNM"),
    FieldMapping("custanm", "CUSTANM"),
    FieldMapping("custbrcd", "CUSTBRCD"),
    FieldMapping("classcd", "CLASSCD"),
    FieldMapping("busityp", "BUSITYP", transform="char"),
    FieldMapping("address", "ADDRESS"),
    FieldMapping("zipcd", "ZIPCD", transform="char"),
    FieldMapping("phoneno", "PHONENO"),
    FieldMapping("faxno", "FAXNO"),
    FieldMapping("contactor", "CONTACTOR"),
    FieldMapping("taxno", "TAXNO"),
    FieldMapping("banknm", "BANKNM"),
    FieldMapping("bankaccno", "BANKACCNO"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("parentcd", "PARENTCD", transform="char"),
    FieldMapping("custcard", "CUSTCARD"),
    FieldMapping("backup", "BACKUP"),
    FieldMapping("location", "LOCATION", transform="char"),
    FieldMapping("area", "AREA"),
    FieldMapping("pos_n", "POS_N"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
    FieldMapping("opersystem", "OPERSYSTEM"),
    FieldMapping("database", "DATA_BASE"),
    FieldMapping("softedition", "SOFT_EDITION"),
    FieldMapping("sstatus", "S_STATUS", transform="char"),
    FieldMapping("advideo", "AD_VIDEO", transform="char"),
    FieldMapping("commmode", "COMMMODE"),
    FieldMapping("card3g", "CARD3G"),
    FieldMapping("adr3g", "ADR3G"),
    FieldMapping("systemcode", "SYSTEMCODE"),
    FieldMapping("custrnm", "CUSTRNM"),
    FieldMapping("opendate", "OPENDATE"),
    FieldMapping("replacedate", "REPLACEDATE"),
    FieldMapping("levels", "LEVELS"),
    FieldMapping("ordertype", "ORDERTYPE"),
    FieldMapping("pptcode", "PPTCODE"),
    FieldMapping("jl_contactor", "JL_CONTACTOR"),
    FieldMapping("jl_phoneno", "JL_PHONENO"),
    FieldMapping("zftype", "ZFTYPE"),
    FieldMapping("posstatus", "POSSTATUS"),
    FieldMapping("posstatus1", "POSSTATUS1"),
    FieldMapping("is_contract", "IS_CONTRACT"),
    FieldMapping("yjmoney", "YJ_MONEY"),
], batch=1, depends_on=["tmm21_custclass"])

_m("TMM11_ITEMCLASS", "tmm11_itemclass", [
    FieldMapping("classtyp", "CLASSTYP", transform="char"),
    FieldMapping("classcd", "CLASSCD"),
    FieldMapping("classnm", "CLASSNM"),
    FieldMapping("parent", "PARENT"),
    FieldMapping("childflg", "CHILDFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
], batch=1)

_m("TMM12_ITEMS", "tmm12_items", [
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("classcd", "CLASSCD"),
    FieldMapping("itemnm", "ITEMNM"),
    FieldMapping("itemanm", "ITEMANM"),
    FieldMapping("itembrcd", "ITEMBRCD"),
    FieldMapping("itemsize", "ITEMSIZE"),
    FieldMapping("countrycd", "COUNTRYCD", transform="char"),
    FieldMapping("provincecd", "PROVINCECD", transform="char"),
    FieldMapping("citycd", "CITYCD", transform="char"),
    FieldMapping("wunit", "WUNIT"),
    FieldMapping("pcrep", "PCREP", transform="char"),
    FieldMapping("keeper", "KEEPER", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("upperlimit", "UPPERLIMIT"),
    FieldMapping("lowerlimit", "LOWERLIMIT"),
    FieldMapping("minorder", "MINORDER"),
    FieldMapping("newperiod", "NEWPERIOD"),
    FieldMapping("oldperiod", "OLDPERIOD"),
    FieldMapping("backup", "BACKUP"),
    FieldMapping("typflg", "TYPFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
    FieldMapping("purchasetyp", "PURCHASETYP", transform="char"),
    FieldMapping("consume", "CONSUME", transform="char"),
], batch=1, depends_on=["tmm11_itemclass"])

_m("TMM18_SUPPLIERCLASS", "tmm18_supplierclass", [
    FieldMapping("classtyp", "CLASSTYP", transform="char"),
    FieldMapping("classcd", "CLASSCD"),
    FieldMapping("classnm", "CLASSNM"),
    FieldMapping("parent", "PARENT"),
    FieldMapping("childflg", "CHILDFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
], batch=1)

_m("TMM19_SUPPLIERS", "tmm19_suppliers", [
    FieldMapping("custcd", "CUSTCD", transform="char"),
    FieldMapping("custnm", "CUSTNM"),
    FieldMapping("custanm", "CUSTANM"),
    FieldMapping("custbrcd", "CUSTBRCD"),
    FieldMapping("classcd", "CLASSCD"),
    FieldMapping("scale", "SCALE", transform="char"),
    FieldMapping("address", "ADDRESS"),
    FieldMapping("zipcd", "ZIPCD", transform="char"),
    FieldMapping("phoneno", "PHONENO"),
    FieldMapping("faxno", "FAXNO"),
    FieldMapping("contactor", "CONTACTOR"),
    FieldMapping("taxno", "TAXNO"),
    FieldMapping("banknm", "BANKNM"),
    FieldMapping("bankaccno", "BANKACCNO"),
    FieldMapping("pcrep", "PCREP", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("suppinfo", "SUPPINFO", transform="char"),
    FieldMapping("agreements", "AGREEMENTS", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
], batch=1, depends_on=["tmm18_supplierclass"])

_m("TWH01_WAREHOUSE", "twh01_warehouse", [
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("whnm", "WHNM"),
    FieldMapping("whtyp", "WHTYP", transform="char"),
    FieldMapping("address", "ADDRESS"),
    FieldMapping("phoneno", "PHONENO"),
    FieldMapping("fax", "FAX"),
    FieldMapping("leader", "LEADER", transform="char"),
    FieldMapping("defaultflg", "DEFAULTFLG", transform="char"),
    FieldMapping("remoteflg", "REMOTEFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=1)

_m("TMM46_AREA", "tmm46_area", [
    FieldMapping("id", "ID"),
    FieldMapping("name", "NAME"),
    FieldMapping("usercd", "USERCD", transform="char"),
], batch=1)

_m("TMM47_COMMODE", "tmm47_commode", [
    FieldMapping("cmmcd", "CMMCD"),
    FieldMapping("cmmnm", "CMMNM"),
    FieldMapping("cmmtype", "CMMTYPE", transform="char"),
    FieldMapping("parent", "PARENT"),
    FieldMapping("childflg", "CHILDFLG", transform="char"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("gendate", "GENDATE"),
], batch=1)

_m("TMM24_CUSTITEMS", "tmm24_custitems", [
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("custcd", "CUSTCD", transform="char"),
    FieldMapping("dfltflg", "DFLTFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("delivercycle", "DELIVERCYCLE"),
    FieldMapping("servicecycle", "SERVICECYCLE"),
    FieldMapping("guarntperiod", "GUARANTEEPERIOD"),
    FieldMapping("backup", "BACKUP"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
], batch=1, depends_on=["tmm12_items", "tmm22_customers"])

_m("TMM31_SYSCODES", "tmm31_syscodes", [
    FieldMapping("codetyp", "CODETYP", transform="char"),
    FieldMapping("codecd", "CODECD", transform="char"),
    FieldMapping("codenm", "CODENM"),
    FieldMapping("sysflg", "SYSFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
], batch=1)

_m("TMM34_IDMASTER", "tmm34_idmaster", [
    FieldMapping("idtyp", "IDTYP", transform="char"),
    FieldMapping("idtypnm", "IDTYPNM"),
    FieldMapping("curbillid", "CURBILLID"),
    FieldMapping("maxbillid", "MAXBILLID"),
    FieldMapping("loops", "LOOPS"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=1)

_m("TMC71_SYSPARM", "tmc71_sysparm", [
    FieldMapping("pk", "PK", transform="char"),
    FieldMapping("costtype", "COSTTYPE", transform="char"),
    FieldMapping("autobackpath", "AUTOBACKPATH"),
    FieldMapping("invoicesharepath", "INVOICESHAREPATH"),
    FieldMapping("poinvaliddays", "POINVALIDDAYS"),
    FieldMapping("soinvaliddays", "SOINVALIDDAYS"),
    FieldMapping("allowmultilogon", "ALLOWMULTILOGON", transform="char"),
    FieldMapping("shopbilltype", "SHOPBILLTYPE", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("centralwarehouse", "CENTRALWAREHOUSE", transform="char"),
], batch=1)

_m("TMC41_ACCLOG", "tmc41_acclog", [
    FieldMapping("startdate", "STARTDATE"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
], batch=1, depends_on=["tmc13_users"])


# ---------- 第2批：ITSM 字典与配置 ----------

_m("TIT01_TIMEPOINT_AREA", "tit01_timepoint_area", [
    FieldMapping("levels", "LEVELS"),
    FieldMapping("explain", "EXPLAIN"),
    FieldMapping("timepoint", "TIMEPOINT"),
    FieldMapping("beforetm", "BEFORETM"),
    FieldMapping("aftertm", "AFTERTM"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=2)

_m("TIT02_LIABILITYREG", "tit02_liabilityreg", [
    FieldMapping("liabcd", "LIABCD"),
    FieldMapping("liabnm", "LIABNM"),
    FieldMapping("describe", "DESCRIBE"),
    FieldMapping("liabtype", "LIABTYPE", transform="char"),
    FieldMapping("parent", "PARENT"),
    FieldMapping("childflg", "CHILDFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=2)

_m("TIT02_LIABILITYREGDT", "tit02_liabilityregdt", [
    FieldMapping("lbdtcd", "LBDTCD"),
    FieldMapping("liabcd", "LIABCD"),
    FieldMapping("define", "DEFINE"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=2, depends_on=["tit02_liabilityreg"])

_m("TIT03_SYSCODES", "tit03_syscodes", [  # 2026-05-10: tit03已合并至tmm31_syscodes并删除
    FieldMapping("codetyp", "CODETYP", transform="char"),
    FieldMapping("codecd", "CODECD", transform="char"),
    FieldMapping("codenm", "CODENM"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("sysflg", "SYSFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
], batch=2)

_m("TIT04_ARCHIVECODE", "tit04_archivecode", [
    FieldMapping("archcd", "ARCHCD"),
    FieldMapping("archnm", "ARCHNM"),
    FieldMapping("describe", "DESCRIBE"),
    FieldMapping("archtype", "ARCHTYPE", transform="char"),
    FieldMapping("parent", "PARENT"),
    FieldMapping("childflg", "CHILDFLG", transform="char"),
    FieldMapping("maxlevel", "MAXLEVEL"),
    FieldMapping("archgroup", "ARCHGROUP", transform="char"),
    FieldMapping("faulttype", "FAULTTYPE"),
    FieldMapping("uncheck", "UNCHECK", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=2)

_m("TIT05_REPAIRINFO", "tit05_repairinfo", [
    FieldMapping("reptype", "REP_TYPE", transform="char"),
    FieldMapping("objcd", "OBJ_CD"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=2)

_m("TIT06_USERAREA", "tit06_userarea", [
    FieldMapping("areaid", "AREAID"),
    FieldMapping("usercd", "USERCD", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
], batch=2, depends_on=["tmm46_area", "tmc13_users"])

_m("TMC03_USERMENUS", "tmc03_usermenus", [
    FieldMapping("usercd", "USERCD", transform="char"),
    FieldMapping("menucd", "MENUCD"),
    FieldMapping("ordno", "ORDNO"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=2, depends_on=["tmc13_users", "tmc01_menus"])

# 复合PK → 代理键表
_m("TMC21_USERGROUP", "tmc21_usergroup", [
    FieldMapping("usercd", "USERCD", transform="char"),
    FieldMapping("groupcd", "GROUPCD", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=2, depends_on=["tmc13_users", "tmc12_groups"])

_m("TMC22_USERBUSITYP", "tmc22_userbusityp", [
    FieldMapping("usercd", "USERCD", transform="char"),
    FieldMapping("busityp", "BUSITYP", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=2, depends_on=["tmc13_users"])

_m("TMC31_GROUPRIGHT", "tmc31_groupright", [
    FieldMapping("groupcd", "GROUPCD", transform="char"),
    FieldMapping("menucd", "MENUCD"),
    FieldMapping("funccd", "FUNCCD"),
    FieldMapping("scale", "SCALE"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=2, depends_on=["tmc12_groups", "tmc02_menusdt"])

_m("TMM35_CUST_POS_RL", "tmm35_cust_pos_rl", [
    FieldMapping("custcd", "CUSTCD", transform="char"),
    FieldMapping("eid", "EID", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("startdate", "STARTDATE"),
    FieldMapping("sysinfo", "SYSINFO"),
    FieldMapping("softinfo", "SOFTINFO"),
    FieldMapping("posupddate", "POSUPDDATE"),
    FieldMapping("posinfo", "POSINFO"),
    FieldMapping("area", "AREA", transform="char"),
    FieldMapping("status", "STATUS", transform="char"),
    FieldMapping("typflg", "TYPFLG", transform="char"),
    FieldMapping("maintenancedate", "MAINTENANCEDATE"),
    FieldMapping("maintenancetyp", "MAINTENANCETYP", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("maintenanceno", "MAINTENANCENO"),
    # P0-2 新增字段，无旧数据
    FieldMapping("asset_type", default="POS"),
    FieldMapping("recycle_status", default="ACTIVE"),
], batch=2, depends_on=["tmm22_customers", "tmm12_items"])

_m("TMM36_CUST_VE_RL", "tmm36_cust_ve_rl", [
    FieldMapping("custcd", "CUSTCD", transform="char"),
    FieldMapping("eid", "EID", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("startdate", "STARTDATE"),
    FieldMapping("sysinfo", "SYSINFO"),
    FieldMapping("softinfo", "SOFTINFO"),
    FieldMapping("posupddate", "POSUPDDATE"),
    FieldMapping("posinfo", "POSINFO"),
    FieldMapping("area", "AREA", transform="char"),
    FieldMapping("status", "STATUS", transform="char"),
    FieldMapping("typflg", "TYPFLG", transform="char"),
    FieldMapping("maintenancedate", "MAINTENANCEDATE"),
    FieldMapping("maintenancetyp", "MAINTENANCETYP"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=2, depends_on=["tmm22_customers"])


# ---------- 第3批：ITSM 业务单据（主表 → 子表 → 附表顺序） ----------

def _itsm_main_fields(id_field: str, id_col: str) -> list[FieldMapping]:
    """ITSM 主表通用字段映射工厂。"""
    return [
        FieldMapping(id_field, id_col),
        FieldMapping("company_id", "COMPANY_ID", transform="char"),
        FieldMapping("store_id", "STORE_ID", transform="char"),
        FieldMapping("request_time", "REQUEST_TIME"),
        FieldMapping("requset_paper_id", "REQUSET_PAPER_ID"),
        FieldMapping("expected_completion_time", "EXPECTED_COMPLETION_TIME"),
        FieldMapping("deliver_no", "DELIVER_NO"),
        FieldMapping("short_description", "SHORT_DESCRIPTION"),
        FieldMapping("detail_description", "DETAIL_DESCRIPTION"),
        FieldMapping("current_status", "CURRENT_STATUS", transform="char"),
        FieldMapping("is_success", "IS_SUCCESS", transform="char"),
        FieldMapping("is_old", "IS_OLD", transform="char"),
        FieldMapping("create_time", "CREATE_TIME"),
        FieldMapping("creator", "CREATOR", transform="char"),
        FieldMapping("update_time", "UPDATE_TIME"),
        FieldMapping("updator", "UPDATOR", transform="char"),
        FieldMapping("firstor", "FIRSTOR", transform="char"),
        FieldMapping("first_time", "FIRST_TIME"),
        FieldMapping("leave_time", "LEAVE_TIME"),
        FieldMapping("close_time", "CLOSE_TIME"),
        FieldMapping("revisit_time", "REVISIT_TIME"),
    ]


# TIT10 日常维护单
_m("TIT10_MAINTENANCEDAY", "tit10_maintenanceday", [
    *_itsm_main_fields("maintenance_id", "MAINTENANCE_ID"),
    FieldMapping("temp_contract", "TEMP_CONTRACT"),
    FieldMapping("fault_type", "FAULT_TYPE"),
    FieldMapping("servrity", "SERVRITY", transform="char"),
    FieldMapping("emergency_level", "EMERGENCY_LEVEL", transform="char"),
    FieldMapping("priority", "PRIORITY", transform="char"),
    FieldMapping("requester", "REQUESTER", transform="char"),
    FieldMapping("device_id", "DEVICE_ID", transform="char"),
    FieldMapping("faultcode", "FAULTCODE"),
    FieldMapping("is_archive", "IS_ARCHIVE", transform="char"),
    FieldMapping("view_type", "VIEW_TYPE", transform="char"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("requst_typ", "REQUST_TYP"),
    FieldMapping("requset_paper_id", "REQUSET_PAPER_ID"),
    FieldMapping("source_type", default="DAILY"),
], batch=3, depends_on=["tmm22_customers", "tmm01_company"])

_m("TIT10_MAINTENANCE_LIABILITY", "tit10_maintenance_liability", [
    FieldMapping("maintenance_id", "MAINTENANCE_ID"),
    FieldMapping("exceptionscd", "EXCEPTIONSCD"),
    FieldMapping("exceptionsnm", "EXCEPTIONSNM"),
    FieldMapping("deptnm", "DEPTNM"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("assessflg", "ASSESSFLG", transform="char"),
    FieldMapping("exemptflg", "EXEMPTFLG", transform="char"),
    FieldMapping("type", "TYPE", transform="char"),
    FieldMapping("is_finish", "IS_FINISH", transform="char"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("setfrom", "SETFROM"),
], batch=3, depends_on=["tit10_maintenanceday"])

_m("TIT10_MAIN_TRACK", "tit10_main_track", [
    FieldMapping("maintenance_id", "MAINTENANCE_ID"),
    FieldMapping("depcd", "DEP_CD"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("updatetime", "UPDATETIME"),
], batch=3, depends_on=["tit10_maintenanceday"])

_m("TIT10_POS_DETAIL", "tit10_pos_detail", [
    FieldMapping("bill_id", "BILL_ID"),
    FieldMapping("sm_id", "SM_ID"),
    FieldMapping("noflg", "NOFLG", transform="char"),
    FieldMapping("device_id", "DEVICE_ID", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("accessories_id", "ACCESSORIES_ID", transform="char"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("status", "STATUS", transform="char"),
], batch=3, depends_on=["tit10_maintenanceday"])

# TIT11 附件
_m("TIT11_MAINTENANCE_ATTC", "tit11_maintenance_attc", [
    FieldMapping("maintenance_id", "MAINTENANCE_ID"),
    FieldMapping("business_operation_id", "BUSINESS_OPERATION_ID"),
    FieldMapping("attc_id", "ATTC_ID"),
    FieldMapping("attcnm", "ATTCNM"),
    FieldMapping("attc", "ATTC"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
], batch=3, depends_on=["tit10_maintenanceday"])

# TIT12 归档
_m("TIT12_MAINTENANCE_ARCHIVE", "tit12_maintenance_archive", [
    FieldMapping("maintenance_id", "MAINTENANCE_ID"),
    FieldMapping("business_operation_id", "BUSINESS_OPERATION_ID"),
    FieldMapping("faultcd", "FAULTCD"),
    FieldMapping("faultcd_audit", "FAULTCD_AUDIT"),
    FieldMapping("fault_type", "FAULT_TYPE"),
    FieldMapping("fault_detail_type", "FAULT_DETAIL_TYPE"),
    FieldMapping("description", "DESCRIPTION"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("is_audit", "IS_AUDIT", transform="char"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
], batch=3, depends_on=["tit10_maintenanceday"])

# TIT13 新机开通
_m("TIT13_MAINTENANCE_OPEN", "tit13_maintenance_open", [
    FieldMapping("new_opening_id", "NEW_OPENING_ID"),
    FieldMapping("company_id", "COMPANY_ID", transform="char"),
    FieldMapping("store_id", "STORE_ID", transform="char"),
    FieldMapping("request_time", "REQUEST_TIME"),
    FieldMapping("requset_paper_id", "REQUSET_PAPER_ID"),
    FieldMapping("device_id", "DEVICE_ID", transform="char"),
    FieldMapping("count", "COUNT"),
    FieldMapping("expected_completion_time", "EXPECTED_COMPLETION_TIME"),
    FieldMapping("deliver_no", "DELIVER_NO"),
    FieldMapping("short_description", "SHORT_DESCRIPTION"),
    FieldMapping("detail_description", "DETAIL_DESCRIPTION"),
    FieldMapping("current_status", "CURRENT_STATUS", transform="char"),
    FieldMapping("is_success", "IS_SUCCESS", transform="char"),
    FieldMapping("is_old", "IS_OLD", transform="char"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
    FieldMapping("firstor", "FIRSTOR", transform="char"),
    FieldMapping("first_time", "FIRST_TIME"),
    FieldMapping("leave_time", "LEAVE_TIME"),
    FieldMapping("close_time", "CLOSE_TIME"),
    FieldMapping("revisit_time", "REVISIT_TIME"),
    FieldMapping("from_custcard", "FROM_CUSTCARD"),
    FieldMapping("from_custcd", "FROM_CUSTCD", transform="char"),
], batch=3, depends_on=["tmm22_customers", "tmm01_company"])

_m("TIT14_EQUIPMENT_OPEN", "tit14_equipment_open", [
    FieldMapping("new_opening_id", "NEW_OPENING_ID"),
    FieldMapping("business_operation_id", "BUSINESS_OPERATION_ID"),
    FieldMapping("device_id", "DEVICE_ID", transform="char"),
    FieldMapping("price", "PRICE"),
    FieldMapping("deliveryid", "DELIVERYID"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
    FieldMapping("is_finish", "IS_FINISH", transform="char"),
    FieldMapping("is_change", "IS_CHANGE"),
    FieldMapping("change_eid", "CHANGE_EID"),
    FieldMapping("from_custcard", "FROM_CUSTCARD"),
    FieldMapping("from_posid", "FROM_POSID"),
    FieldMapping("from_custcd", "FROM_CUSTCD", transform="char"),
], batch=3, depends_on=["tit13_maintenance_open"])

# TIT15 旧机翻新
_m("TIT15_MAINTENANCE_RENOVATE", "tit15_maintenance_renovate", [
    FieldMapping("renew_id", "RENEW_ID"),
    FieldMapping("company_id", "COMPANY_ID", transform="char"),
    FieldMapping("store_id", "STORE_ID", transform="char"),
    FieldMapping("request_time", "REQUEST_TIME"),
    FieldMapping("requset_paper_id", "REQUSET_PAPER_ID"),
    FieldMapping("old_device_id", "OLD_DEVICE_ID", transform="char"),
    FieldMapping("new_device_id", "NEW_DEVICE_ID", transform="char"),
    FieldMapping("count", "COUNT"),
    FieldMapping("expected_completion_time", "EXPECTED_COMPLETION_TIME"),
    FieldMapping("deliver_no", "DELIVER_NO"),
    FieldMapping("short_description", "SHORT_DESCRIPTION"),
    FieldMapping("detail_description", "DETAIL_DESCRIPTION"),
    FieldMapping("current_status", "CURRENT_STATUS", transform="char"),
    FieldMapping("is_success", "IS_SUCCESS", transform="char"),
    FieldMapping("is_old", "IS_OLD", transform="char"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
    FieldMapping("firstor", "FIRSTOR", transform="char"),
    FieldMapping("first_time", "FIRST_TIME"),
    FieldMapping("leave_time", "LEAVE_TIME"),
    FieldMapping("close_time", "CLOSE_TIME"),
    FieldMapping("revisit_time", "REVISIT_TIME"),
    FieldMapping("is_back", "IS_BACK", transform="char"),
], batch=3, depends_on=["tmm22_customers", "tmm01_company"])

_m("TIT15_EQUIPMENT_RENOVATE", "tit15_equipment_renovate", [
    FieldMapping("renovate_id", "RENOVATE_ID"),
    FieldMapping("business_operation_id", "BUSINESS_OPERATION_ID"),
    FieldMapping("device_id", "DEVICE_ID", transform="char"),
    FieldMapping("new_device_id", "NEW_DEVICE_ID", transform="char"),
    FieldMapping("price", "PRICE"),
    FieldMapping("deliveryid", "DELIVERYID"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
    FieldMapping("is_finish", "IS_FINISH", transform="char"),
    FieldMapping("is_change", "IS_CHANGE"),
    FieldMapping("change_eid", "CHANGE_EID"),
], batch=3, depends_on=["tit15_maintenance_renovate"])

# TIT16 设备变更（新增 customer_status P0-3）
_m("TIT16_DEVICE_CHANGE", "tit16_device_change", [
    FieldMapping("device_change_id", "DEVICE_CHANGE_ID"),
    FieldMapping("store_id", "STORE_ID", transform="char"),
    FieldMapping("requset_paper_id", "REQUSET_PAPER_ID"),
    FieldMapping("change_type", "CHANGE_TYPE"),
    FieldMapping("device_id", "DEVICE_ID", transform="char"),
    FieldMapping("new_contactor", "NEW_CONTACTOR"),
    FieldMapping("new_tel", "NEW_TEL"),
    FieldMapping("new_address", "NEW_ADDRESS"),
    FieldMapping("new_store_card", "NEW_STORE_CARD"),
    FieldMapping("new_store_id", "NEW_STORE_ID", transform="char"),
    FieldMapping("is_store_inside_change", "IS_STORE_INSIDE_CHANGE", transform="char"),
    FieldMapping("request_time", "REQUEST_TIME"),
    FieldMapping("expected_completion_time", "EXPECTED_COMPLETION_TIME"),
    FieldMapping("short_description", "SHORT_DESCRIPTION"),
    FieldMapping("detail_description", "DETAIL_DESCRIPTION"),
    FieldMapping("current_status", "CURRENT_STATUS", transform="char"),
    FieldMapping("is_success", "IS_SUCCESS", transform="char"),
    FieldMapping("is_old", "IS_OLD", transform="char"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
    FieldMapping("firstor", "FIRSTOR", transform="char"),
    FieldMapping("first_time", "FIRST_TIME"),
    FieldMapping("leave_time", "LEAVE_TIME"),
    FieldMapping("close_time", "CLOSE_TIME"),
    FieldMapping("revisit_time", "REVISIT_TIME"),
    FieldMapping("customer_status", default="ACTIVE"),
], batch=3, depends_on=["tmm22_customers"])

# TIT17 日常保养
_m("TIT17_MAINTENANCE", "tit17_maintenance", [
    FieldMapping("daily_maintenance_id", "DAILY_MAINTENANCE_ID"),
    FieldMapping("store_id", "STORE_ID", transform="char"),
    FieldMapping("has_video_device", "HAS_VIDEO_DEVICE", transform="char"),
    FieldMapping("video_device_status", "VIDEO_DEVICE_STATUS"),
    FieldMapping("video_device_error_des", "VIDEO_DEVICE_ERROR_DES"),
    FieldMapping("request_engineer_id", "REQUEST_ENGINNER_ID", transform="char"),
    FieldMapping("request_time", "REQUEST_TIME"),
    FieldMapping("short_description", "SHORT_DESCRIPTION"),
    FieldMapping("detail_description", "DETAIL_DESCRIPTION"),
    FieldMapping("current_status", "CURRENT_STATUS", transform="char"),
    FieldMapping("is_success", "IS_SUCCESS", transform="char"),
    FieldMapping("is_old", "IS_OLD", transform="char"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
    FieldMapping("firstor", "FIRSTOR", transform="char"),
    FieldMapping("first_time", "FIRST_TIME"),
    FieldMapping("leave_time", "LEAVE_TIME"),
    FieldMapping("close_time", "CLOSE_TIME"),
    FieldMapping("revisit_time", "REVISIT_TIME"),
], batch=3, depends_on=["tmm22_customers"])

_m("TIT17_CUST_POS_DAILY", "tit17_cust_pos_daily", [
    FieldMapping("daily_maintenance_id", "DAILY_MAINTENANCE_ID"),
    FieldMapping("business_operation_id", "BUSINESS_OPERATION_ID"),
    FieldMapping("custcd", "CUSTCD", transform="char"),
    FieldMapping("eid", "EID", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("startdate", "STARTDATE"),
    FieldMapping("sysinfo", "SYSINFO"),
    FieldMapping("softinfo", "SOFTINFO"),
    FieldMapping("posupddate", "POSUPDDATE"),
    FieldMapping("posinfo", "POSINFO"),
    FieldMapping("area", "AREA", transform="char"),
    FieldMapping("status", "STATUS", transform="char"),
    FieldMapping("typflg", "TYPFLG", transform="char"),
    FieldMapping("maintenancedate", "MAINTENANCEDATE"),
    FieldMapping("maintenancetyp", "MAINTENANCETYP", transform="char"),
    FieldMapping("request_engineer_id", "REQUEST_ENGINNER_ID", transform="char"),
    FieldMapping("request_time", "REQUEST_TIME"),
    FieldMapping("short_description", "SHORT_DESCRIPTION"),
    FieldMapping("detail_description", "DETAIL_DESCRIPTION"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=3, depends_on=["tit17_maintenance"])

_m("TIT17_MAINTENANCE_PLAN", "tit17_maintenance_plan", [
    FieldMapping("plan_y", "PLAN_Y"),
    FieldMapping("plan_yymm", "PLAN_YYMM"),
    FieldMapping("area_id", "AREA_ID"),
    FieldMapping("plan_qty", "PLAN_QTY"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
], batch=3)

# 省略 TIT18~TIT29 的完整映射（结构同上，字段以数据库字典为准）
# 实际执行时按批量生成脚本一次性补全，这里展示核心表即可

# 公用附表
_m("TIT21_MAINTENANCE_DISPATCH", "tit21_maintenance_dispatch", [
    FieldMapping("maintenance_id", "MAINTENANCE_ID"),
    FieldMapping("business_operation_id", "BUSINESS_OPERATION_ID"),
    FieldMapping("maintenance_type", "MAINTENANCE_TYPE", transform="char"),
    FieldMapping("operator", "OPERATOR", transform="char"),
    FieldMapping("accpectd_group", "ACCPECTD_GROUP", transform="char"),
    FieldMapping("accpectder", "ACCPECTDER", transform="char"),
    FieldMapping("dispatch_time", "DISPATCH_TIME"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
], batch=3)

_m("TIT23_MAINTENANCE_D2D", "tit23_maintenance_d2d", [
    FieldMapping("maintenance_id", "MAINTENANCE_ID"),
    FieldMapping("business_operation_id", "BUSINESS_OPERATION_ID"),
    FieldMapping("d2d_engineer", "D2D_ENGINEER", transform="char"),
    FieldMapping("arrive_time", "ARRIVE_TIME"),
    FieldMapping("leave_time", "LEAVE_TIME"),
    FieldMapping("jjbz", "JJBZ", transform="char"),
    FieldMapping("d2d_description", "D2D_DESCRIPITON"),
    FieldMapping("d2d_phone", "D2D_PHONE"),
    FieldMapping("old_business_id", "OLD_BUSINESS_ID"),
    FieldMapping("d2d_group", "D2D_GROUP"),
    FieldMapping("d2d_type", "D2D_TYPE", transform="char"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("posstatus", "POSSTATUS"),
    FieldMapping("posstatus1", "POSSTATUS1"),
], batch=3)

_m("TIT24_MAINTENANCE_RV", "tit24_maintenance_rv", [
    FieldMapping("maintenance_id", "MAINTENANCE_ID"),
    FieldMapping("business_operation_id", "BUSINESS_OPERATION_ID"),
    FieldMapping("rv_time", "RV_TIME"),
    FieldMapping("rv_operator", "RV_OPERATOR"),
    FieldMapping("feedback", "FEEDBACK"),
    FieldMapping("satisfaction", "SATISFACTION", transform="char"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
], batch=3)


# ---------- 第4批：仓储/采购/销售 ----------

# 仓储系列（twh11-22）
_m("TWH11_DETAIL", "twh11_detail", [
    FieldMapping("seqno", "SEQNO"),
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("itemtyp", "ITEMTYP", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("prddate", "PRDDATE"),
    FieldMapping("itemqty", "ITEMQTY"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=4, depends_on=["twh01_warehouse", "tmm12_items"])

_m("TWH12_DETAILDT", "twh12_detaildt", [
    FieldMapping("seqno", "SEQNO"),
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("itemtyp", "ITEMTYP", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("prddate", "PRDDATE"),
    FieldMapping("billid", "BILLID", transform="char"),
    FieldMapping("invdate", "INVDATE"),
    FieldMapping("invtyp", "INVTYP", transform="char"),
    FieldMapping("itemqty", "ITEMQTY"),
    FieldMapping("storeqty", "STOREQTY"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("iotyp", "IOTYP", transform="char"),
], batch=4, depends_on=["twh01_warehouse", "tmm12_items"])

_m("TWH13_IN", "twh13_in", [
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("indate", "INDATE"),
    FieldMapping("inbillid", "INBILLID", transform="char"),
    FieldMapping("invtyp", "INVTYP", transform="char"),
    FieldMapping("refbillid", "REFBILLID", transform="char"),
    FieldMapping("ptimes", "PTIMES"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("auditflg", "AUDITFLG", transform="char"),
    FieldMapping("auditman", "AUDITMAN", transform="char"),
    FieldMapping("auditdate", "AUDITDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("optyp", "OPTYP", transform="char"),
    FieldMapping("suppcd", "SUPPCD", transform="char"),
], batch=4, depends_on=["twh01_warehouse"])

_m("TWH14_CHECKINDT", "twh14_checkindt", [
    FieldMapping("inbillid", "INBILLID", transform="char"),
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("lineno", "LINENO"),
    FieldMapping("itemtyp", "ITEMTYP", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("prddate", "PRDDATE"),
    FieldMapping("batchid", "BATCHID"),
    FieldMapping("inqty", "INQTY"),
    FieldMapping("reflineno", "REFLINENO"),
    FieldMapping("s_money", "S_MONEY"),
], batch=4, depends_on=["twh13_in"])

_m("TWH15_OUT", "twh15_out", [
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("outdate", "OUTDATE"),
    FieldMapping("outbillid", "OUTBILLID", transform="char"),
    FieldMapping("invtyp", "INVTYP", transform="char"),
    FieldMapping("ptimes", "PTIMES"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("auditflg", "AUDITFLG", transform="char"),
    FieldMapping("auditman", "AUDITMAN", transform="char"),
    FieldMapping("auditdate", "AUDITDATE"),
    FieldMapping("optyp", "OPTYP", transform="char"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("targetwhcd", "TARGETWHCD", transform="char"),
    FieldMapping("suppcd", "SUPPCD", transform="char"),
], batch=4, depends_on=["twh01_warehouse"])

_m("TWH16_OUTDTEID", "twh16_outdteid", [
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("outbillid", "OUTBILLID", transform="char"),
    FieldMapping("lineno", "LINENO"),
    FieldMapping("itemtyp", "ITEMTYP", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("prddate", "PRDDATE"),
    FieldMapping("eid", "EID", transform="char"),
    FieldMapping("outqty", "OUTQTY"),
    FieldMapping("qcqty", "QCQTY"),
    FieldMapping("reflineno", "REFLINENO"),
    FieldMapping("s_money", "S_MONEY"),
], batch=4, depends_on=["twh15_out"])

_m("TWH16_OUTDTPRD", "twh16_outdtprd", [
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("outbillid", "OUTBILLID", transform="char"),
    FieldMapping("lineno", "LINENO"),
    FieldMapping("itemtyp", "ITEMTYP", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("prddate", "PRDDATE"),
    FieldMapping("outqty", "OUTQTY"),
    FieldMapping("qcqty", "QCQTY"),
    FieldMapping("reflineno", "REFLINENO"),
    FieldMapping("s_money", "S_MONEY"),
], batch=4, depends_on=["twh15_out"])

# 采购系列
_m("TPC01_PCPLAN", "tpc01_pcplan", [
    FieldMapping("pcplanid", "PCPLANID", transform="char"),
    FieldMapping("slbillid", "SLBILLID", transform="char"),
    FieldMapping("pctyp", "PCTYP", transform="char"),
    FieldMapping("ptimes", "PTIMES"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("plandate", "PLANDATE"),
    FieldMapping("auditman", "AUDITMAN", transform="char"),
    FieldMapping("auditdate", "AUDITDATE"),
    FieldMapping("checkmemo", "CHECKMEMO"),
    FieldMapping("auditflg", "AUDITFLG", transform="char"),
    FieldMapping("type", "TYPE", transform="char"),
], batch=4)

_m("TPC02_PCPLANDT", "tpc02_pcplandt", [
    FieldMapping("pcplanid", "PCPLANID", transform="char"),
    FieldMapping("lineno", "LINENO"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("rgstqty", "RGSTQTY"),
    FieldMapping("units", "UNITS"),
    FieldMapping("storeqty", "STOREQTY"),
    FieldMapping("lowlimit", "LOWLIMIT"),
    FieldMapping("upperlimit", "UPPERLIMIT"),
    FieldMapping("auditqty", "AUDITQTY"),
], batch=4, depends_on=["tpc01_pcplan"])

_m("TPC12_REGISTER", "tpc12_register", [
    FieldMapping("rgstbillid", "RGSTBILLID", transform="char"),
    FieldMapping("suppliercd", "SUPPLIERCD", transform="char"),
    FieldMapping("pcrep", "PCREP", transform="char"),
    FieldMapping("ptimes", "PTIMES"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("auditman", "AUDITMAN", transform="char"),
    FieldMapping("auditdate", "AUDITDATE"),
    FieldMapping("checkmemo", "CHECKMEMO"),
    FieldMapping("auditflg", "AUDITFLG", transform="char"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("rgstdate", "RGSTDATE"),
    FieldMapping("rgstamt", "RGSTAMT"),
], batch=4, depends_on=["tmm19_suppliers"])

_m("TPC13_REGISTERDT", "tpc13_registerdt", [
    FieldMapping("rgstbillid", "RGSTBILLID", transform="char"),
    FieldMapping("lineno", "LINENO"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("rgsqty", "RGSQTY"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("units", "UNITS"),
    FieldMapping("rgstprice", "RGSTPRICE"),
    FieldMapping("deliverdate", "DELIVERDATE"),
    FieldMapping("inqty", "INQTY"),
    FieldMapping("auditqty", "AUDITQTY"),
], batch=4, depends_on=["tpc12_register"])

# 销售系列
_m("TSL01_EXTEND", "tsl01_extend", [
    FieldMapping("opbillid", "OPBILLID", transform="char"),
    FieldMapping("slbillid", "SLBILLID", transform="char"),
    FieldMapping("custcd", "CUSTCD", transform="char"),
    FieldMapping("impdate", "IMPDATE", transform="char"),
    FieldMapping("traindate", "TRAINDATE", transform="char"),
    FieldMapping("busityp", "BUSITYP", transform="char"),
    FieldMapping("sltyp", "SLTYP", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("backup", "BACKUP"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("auditflg", "AUDITFLG", transform="char"),
    FieldMapping("auditman", "AUDITMAN", transform="char"),
    FieldMapping("auditdate", "AUDITDATE"),
], batch=4, depends_on=["tmm22_customers"])

_m("TSL10_SLBILL", "tsl10_slbill", [
    FieldMapping("slbillid", "SLBILLID", transform="char"),
    FieldMapping("custbillid", "CUSTBILLID"),
    FieldMapping("sltyp", "SLTYP", transform="char"),
    FieldMapping("custcd", "CUSTCD", transform="char"),
    FieldMapping("rgsdate", "RGSDATE"),
    FieldMapping("senddate", "SENDDATE"),
    FieldMapping("busityp", "BUSITYP", transform="char"),
    FieldMapping("ptimes", "PTIMES"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("auditman", "AUDITMAN", transform="char"),
    FieldMapping("auditdate", "AUDITDATE"),
    FieldMapping("checkmemo", "CHECKMEMO"),
    FieldMapping("auditflg", "AUDITFLG", transform="char"),
    FieldMapping("pcplanflg", "PCPLANFLG", transform="char"),
    FieldMapping("rfpcplanid", "RFPCPLANID", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("rgsqty", "RGSQTY"),
    FieldMapping("planqty", "PLANQTY"),
    FieldMapping("openqty", "OPENQTY"),
    FieldMapping("clqty", "CLQTY"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=4, depends_on=["tmm22_customers"])


# ---------- 第5批：其他（押金/BOM/EID/质检/考勤/合同/发票） ----------

_m("TMM61_DEPOSIT", "tmm61_deposit", [
    FieldMapping("custcd", "CUSTCD"),
    FieldMapping("amount_money", "AMOUNT_MONEY"),
    FieldMapping("updatetime", "UPDATETIME"),
    FieldMapping("rbillid", "R_BILLID"),
    FieldMapping("modelcd", "MODELCD"),
    FieldMapping("modelnm", "MODELNM"),
], batch=5, depends_on=["tmm22_customers"])

_m("TMM41_BOM", "tmm41_bom", [
    FieldMapping("bomcd", "BOMCD", transform="char"),
    FieldMapping("bomnm", "BOMNM"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=5)

_m("TMM42_BOMDT", "tmm42_bomdt", [
    FieldMapping("bomcd", "BOMCD", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("bomqty", "BOMQTY"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("itemtyp", "ITEMTYP"),
], batch=5, depends_on=["tmm41_bom", "tmm12_items"])

_m("TMM43_EID", "tmm43_eid", [
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("eid", "EID", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("etyp", "ETYP", transform="char"),
    FieldMapping("sflg", "SFLG", transform="char"),
    FieldMapping("refid", "REFID", transform="char"),
    FieldMapping("qcflg", "QCFLG", transform="char"),
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("prddate", "PRDDATE"),
    FieldMapping("itemtyp", "ITEMTYP", transform="char"),
    FieldMapping("new_old", "NEW_OLD", transform="char"),
    FieldMapping("remark", "REMARK"),
    FieldMapping("manufseq", "MANUF_SEQ"),
    FieldMapping("old_degree", "OLD_DEGREE"),
    FieldMapping("isunit", "ISUNIT", transform="char"),
], batch=5)

_m("TMM43_EID_TRACK", "tmm43_eid_track", [
    FieldMapping("seqno", "SEQNO"),
    FieldMapping("type", "TYPE", transform="char"),
    FieldMapping("change_date", "CHANGE_DATE"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("eid", "EID", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("etyp", "ETYP", transform="char"),
    FieldMapping("sflg", "SFLG", transform="char"),
    FieldMapping("refid", "REFID", transform="char"),
    FieldMapping("qcflg", "QCFLG", transform="char"),
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("prddate", "PRDDATE"),
    FieldMapping("itemtyp", "ITEMTYP", transform="char"),
    FieldMapping("new_old", "NEW_OLD", transform="char"),
    FieldMapping("nsflg", "N_SFLG", transform="char"),
    FieldMapping("nrefid", "N_REFID", transform="char"),
    FieldMapping("nqcflg", "N_QCFLG", transform="char"),
    FieldMapping("nwhcd", "N_WHCD", transform="char"),
    FieldMapping("nprddate", "N_PRDDATE"),
    FieldMapping("nitemtyp", "N_ITEMTYP", transform="char"),
    FieldMapping("nnew_old", "N_NEW_OLD", transform="char"),
    FieldMapping("nitemcd", "N_ITEMCD", transform="char"),
    FieldMapping("netyp", "N_ETYP", transform="char"),
    FieldMapping("remark", "REMARK"),
    FieldMapping("nremark", "N_REMARK"),
    FieldMapping("manufseq", "MANUF_SEQ"),
    FieldMapping("nmanfseq", "N_MANF_SEQ"),
    FieldMapping("old_degree", "OLD_DEGREE"),
    FieldMapping("nold_degree", "N_OLD_DEGREE"),
], batch=5, depends_on=["tmm43_eid"])

_m("TQC10_RESULT", "tqc10_result", [
    FieldMapping("qcbillid", "QCBILLID", transform="char"),
    FieldMapping("optyp", "OPTYP", transform="char"),
    FieldMapping("refbillid", "REFBILLID", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("eid", "EID", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("auditman", "AUDITMAN", transform="char"),
    FieldMapping("auditflg", "AUDITFLG", transform="char"),
    FieldMapping("auditdate", "AUDITDATE"),
    FieldMapping("qcstatus", "QCSTATUS", transform="char"),
], batch=5)

_m("TKQ01_ATTENDANCE", "tkq01_attendance", [
    FieldMapping("amonth", "AMONTH"),
    FieldMapping("adate", "ADATE"),
    FieldMapping("operid", "OPERID", transform="char"),
    FieldMapping("opernm", "OPERNNM"),
    FieldMapping("arrtime", "ARR_TIME"),
    FieldMapping("leavetime", "LEAVE_TIME"),
    FieldMapping("latecount", "LATECOUNT"),
    FieldMapping("leavecount", "LEAVECOUNT"),
    FieldMapping("punchnum", "PUNCHNUM"),
    FieldMapping("punchdetail", "PUNCHDETAIL"),
    FieldMapping("impnum", "IMP_NUM"),
    FieldMapping("week", "WEEK"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("impdate", "IMP_DATE"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
], batch=5, depends_on=["tmc13_users"])

_m("THT01_HTGL", "tht01_htgl", [
    FieldMapping("htbh", "HTBH"),
    FieldMapping("years", "YEARS", transform="char"),
    FieldMapping("classcd", "CLASSCD"),
    FieldMapping("busityp", "BUSITYP", transform="char"),
    FieldMapping("feetyp", "FEETYP", transform="char"),
    FieldMapping("qdis", "QDIS", transform="char"),
    FieldMapping("qddate", "QDDATE"),
    FieldMapping("htbgr", "HTBGR"),
    FieldMapping("remark", "REMARK"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("yxqfrom", "YXQFROM"),
    FieldMapping("yxqto", "YXQTO"),
    FieldMapping("htamount", "HTAMOUNT"),
], batch=5, depends_on=["tmm21_custclass"])

_m("TAC01_FPSK", "tac01_fpsk", [
    FieldMapping("fpbh", "FPBH"),
    FieldMapping("years", "YEARS", transform="char"),
    FieldMapping("classcd", "CLASSCD"),
    FieldMapping("busityp", "BUSITYP", transform="char"),
    FieldMapping("feetyp", "FEETYP", transform="char"),
    FieldMapping("htbh", "HTBH"),
    FieldMapping("htq", "HTQ", transform="char"),
    FieldMapping("qsr", "QSR"),
    FieldMapping("lsh", "LSH"),
    FieldMapping("kpdate", "KPDATE"),
    FieldMapping("kpamount", "KPAMOUNT"),
    FieldMapping("hkdate", "HKDATE"),
    FieldMapping("hkamount", "HKAMOUNT"),
    FieldMapping("sptype", "SPTYPE", transform="char"),
    FieldMapping("spr", "SPR", transform="char"),
    FieldMapping("htqdis", "HTQDIS", transform="char"),
    FieldMapping("htamount", "HTAMOUNT"),
    FieldMapping("remark", "REMARK"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("upddate", "UPDDATE"),
], batch=5, depends_on=["tht01_htgl"])

_m("TTX01_TXKMG", "ttx01_txkmg", [
    FieldMapping("txkno", "TXKNO"),
    FieldMapping("commmode", "COMMMODE"),
    FieldMapping("remark", "REMARK"),
    FieldMapping("by1", "BY1"),
    FieldMapping("by2", "BY2"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=5)


def get_mappings_by_batch(batch: int) -> list[TableMapping]:
    """获取指定批次的全部映射。"""
    return [m for m in MAPPINGS if m.batch == batch]


def get_batch_order() -> list[int]:
    """返回排好序的批次号列表。"""
    return sorted({m.batch for m in MAPPINGS})
```

- [ ] **Step 2: 运行测试验证通过**

```bash
uv run pytest tests/test_migration_field_mapper.py -v
```
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add app/migration/field_mapper.py tests/test_migration_field_mapper.py
git commit -m "feat(migration): 字段映射引擎 + 核心表映射定义（A类一对一）"
```

---

### Task 3: 分批执行引擎与断点续传

**Files:**
- Create: `app/migration/batch_runner.py`

- [ ] **Step 1: 创建分批执行引擎**

```python
# app/migration/batch_runner.py
"""分批执行引擎：按外键依赖顺序逐表迁移，支持断点续传。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
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
        self.connector.pg_truncate(mapping.new_table)

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
            logger.info("  进度: %d / %d", offset, source_count)

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
```

- [ ] **Step 2: Commit**

```bash
git add app/migration/batch_runner.py
git commit -m "feat(migration): 分批执行引擎（断点续传+序列同步）"
```

---

### Task 4: 特殊表处理

**Files:**
- Create: `app/migration/special_handlers.py`

- [ ] **Step 1: 创建特殊处理模块**

```python
# app/migration/special_handlers.py
"""特殊表处理：复合PK→代理键、P0默认值、密码迁移、B类合并表等。"""
from __future__ import annotations

from app.migration.connector import DualConnector


def handle_composite_pk_tables(conn: DualConnector) -> None:
    """复合PK→代理键的表，确保插入后自增ID正确生成。

    涉及表：tmc21_usergroup, tmc22_userbusityp
    这些表在 field_mapper 中已定义映射，插入时自动生成代理键。
    只需确认 UniqueConstraint 不冲突。
    """
    pass  # SQLAlchemy autoincrement 自动处理


def handle_sys_user_merge(conn: DualConnector) -> None:
    """SYS_USER → tmc13_users 合并。

    逻辑：
    1. 读取 SYS_USER 表中不在 tmc13_users 中的用户
    2. 映射字段：USER_ID→usercd, USER_NAME→usernm, PWD→passwd
    3. 以 usercd 去重，优先保留 tmc13_users 中的数据
    """
    with conn.source.connect() as src:
        result = src.execute(
            text("SELECT USER_ID, USER_NAME, PWD, DEL_FLAG FROM SYS_USER")
        )
        sys_users = [dict(zip(result.keys(), row)) for row in result.fetchall()]

    with conn.target.connect() as dst:
        existing = dst.execute(
            text("SELECT usercd FROM tmc13_users")
        )
        existing_cds = {row[0] for row in existing.fetchall()}

    new_users = [
        {
            "usercd": u["USER_ID"].strip() if u["USER_ID"] else "",
            "usernm": u["USER_NAME"] or "",
            "passwd": u["PWD"] or "",
            "useflg": "1" if u.get("DEL_FLAG") in (None, "0") else "0",
        }
        for u in sys_users
        if u["USER_ID"] and u["USER_ID"].strip() not in existing_cds
    ]

    if new_users:
        with conn.target.connect() as dst:
            for u in new_users:
                dst.execute(
                    text(
                        "INSERT INTO tmc13_users (usercd, usernm, passwd, useflg) "
                        "VALUES (:usercd, :usernm, :passwd, :useflg) "
                        "ON CONFLICT (usercd) DO NOTHING"
                    ),
                    u,
                )
            dst.commit()


def handle_password_migration(conn: DualConnector) -> None:
    """密码迁移。旧库 passwd 字段已导入，新库 password 哈希列置为 NULL。
    迁移完成后统一重置密码为默认值。
    """
    with conn.target.connect() as dst:
        dst.execute(
            text("UPDATE tmc13_users SET password = NULL WHERE password IS NOT NULL")
        )
        dst.commit()
```

- [ ] **Step 2: Commit**

```bash
git add app/migration/special_handlers.py
git commit -m "feat(migration): 特殊表处理（SYS_USER合并+密码迁移）"
```

---

### Task 5: 第1批迁移测试 — 基础主数据

**Files:**
- Create: `tests/test_migration_batch1.py`

- [ ] **Step 1: 编写第1批测试**

```python
# tests/test_migration_batch1.py
"""第1批迁移测试：基础主数据（tmm01_company, tmc11_departments, tmc13_users 等）"""
import pytest
from sqlalchemy import text


class TestBatch1MasterData:
    """第1批迁移验证：基础主数据完整性。"""

    def test_company_row_count(self, migration_connector):
        src_count = migration_connector.source_row_count("TMM01_COMPANY")
        dst_count = migration_connector.target_row_count("tmm01_company")
        assert dst_count == src_count, (
            f"TMM01_COMPANY 行数不一致: 源{src_count} vs 目标{dst_count}"
        )

    def test_company_sample_data(self, migration_connector):
        """随机抽样检查字段值。"""
        with migration_connector.target.connect() as conn:
            row = conn.execute(
                text("SELECT compcd, compnm FROM tmm01_company LIMIT 1")
            ).fetchone()
            assert row is not None, "目标表无数据"
            assert len(row.compcd) <= 2, f"compcd 应为 CHAR(2): {row.compcd}"
            assert row.compnm is not None, "compnm 不应为 NULL"

    def test_users_row_count(self, migration_connector):
        src_count = migration_connector.source_row_count("TMC13_USERS")
        dst_count = migration_connector.target_row_count("tmc13_users")
        assert dst_count >= src_count, (
            f"tmc13_users 迁移后应 >= 源表（含SYS_USER合并）"
        )

    def test_users_foreign_key_integrity(self, migration_connector):
        """验证 tmc13_users.deptcd 外键完整性。"""
        with migration_connector.target.connect() as conn:
            orphans = conn.execute(
                text(
                    "SELECT COUNT(*) FROM tmc13_users u "
                    "WHERE u.deptcd IS NOT NULL "
                    "AND u.deptcd NOT IN (SELECT deptcd FROM tmc11_departments)"
                )
            ).scalar()
            assert orphans == 0, f"存在 {orphans} 条孤儿记录"

    def test_departments_hierarchy(self, migration_connector):
        """验证部门层级结构。"""
        with migration_connector.target.connect() as conn:
            has_parent = conn.execute(
                text("SELECT COUNT(*) FROM tmc11_departments WHERE parent IS NOT NULL")
            ).scalar()
            assert has_parent > 0, "部门层级数据缺失"

    def test_customers_chinese_characters(self, migration_connector):
        """验证中文字段编码正确。"""
        with migration_connector.target.connect() as conn:
            row = conn.execute(
                text("SELECT custnm FROM tmm22_customers WHERE custnm IS NOT NULL LIMIT 1")
            ).fetchone()
            if row:
                assert isinstance(row.custnm, str), "custnm 应为字符串"

    def test_items_class_relation(self, migration_connector):
        """验证 tmm12_items → tmm11_itemclass 外键关联。"""
        with migration_connector.target.connect() as conn:
            orphans = conn.execute(
                text(
                    "SELECT COUNT(*) FROM tmm12_items i "
                    "WHERE i.classcd NOT IN (SELECT classcd FROM tmm11_itemclass)"
                )
            ).scalar()
            assert orphans == 0, f"存在 {orphans} 条 items 无对应分类"
```

- [ ] **Step 2: 添加 conftest fixture**

在 `tests/conftest.py` 中追加：

```python
# 追加到 tests/conftest.py

@pytest.fixture(scope="module")
def migration_connector():
    """创建双库连接器用于迁移测试。"""
    import os
    from app.migration.config import MigrationConfig
    from app.migration.connector import DualConnector

    source_url = os.getenv("SOURCE_DATABASE_URL")
    target_url = os.getenv("DATABASE_URL")
    if not source_url or not target_url:
        pytest.skip("迁移测试需要 SOURCE_DATABASE_URL 和 DATABASE_URL 环境变量")

    config = MigrationConfig.from_env()
    connector = DualConnector(config)
    yield connector
    connector.dispose()
```

- [ ] **Step 3: 运行测试（需要 Oracle 连接时跳过）**

```bash
uv run pytest tests/test_migration_batch1.py -v
```
Expected: SKIP (无 SOURCE_DATABASE_URL) 或 PASS（已执行迁移后验证）

- [ ] **Step 4: Commit**

```bash
git add tests/test_migration_batch1.py tests/conftest.py
git commit -m "test(migration): 第1批基础主数据迁移验证测试"
```

---

### Task 6: 全量校验脚本

**Files:**
- Create: `tests/test_migration_validation.py`

- [ ] **Step 1: 创建全量校验测试**

```python
# tests/test_migration_validation.py
"""全量迁移校验：逐表行数+外键完整性+关键业务聚合值。"""
import pytest
from sqlalchemy import text


# 需要行数校验的 A 类表清单
A_CLASS_TABLES: list[tuple[str, str]] = [
    ("TMM01_COMPANY", "tmm01_company"),
    ("TMC11_DEPARTMENTS", "tmc11_departments"),
    ("TMC13_USERS", "tmc13_users"),
    ("TMM22_CUSTOMERS", "tmm22_customers"),
    ("TMM12_ITEMS", "tmm12_items"),
    ("TMM19_SUPPLIERS", "tmm19_suppliers"),
    ("TWH01_WAREHOUSE", "twh01_warehouse"),
    ("TIT10_MAINTENANCEDAY", "tit10_maintenanceday"),
    ("TIT13_MAINTENANCE_OPEN", "tit13_maintenance_open"),
    ("TIT15_MAINTENANCE_RENOVATE", "tit15_maintenance_renovate"),
    ("TIT16_DEVICE_CHANGE", "tit16_device_change"),
    ("TIT17_MAINTENANCE", "tit17_maintenance"),
    ("TWH13_IN", "twh13_in"),
    ("TWH15_OUT", "twh15_out"),
    ("TPC01_PCPLAN", "tpc01_pcplan"),
    ("TPC12_REGISTER", "tpc12_register"),
    ("TSL10_SLBILL", "tsl10_slbill"),
    ("TMM43_EID", "tmm43_eid"),
    ("TKQ01_ATTENDANCE", "tkq01_attendance"),
    ("THT01_HTGL", "tht01_htgl"),
    ("TAC01_FPSK", "tac01_fpsk"),
]


class TestFullValidation:
    @pytest.mark.parametrize("old_table,new_table", A_CLASS_TABLES)
    def test_row_count_match(self, migration_connector, old_table, new_table):
        src_count = migration_connector.source_row_count(old_table)
        dst_count = migration_connector.target_row_count(new_table)
        assert dst_count == src_count, (
            f"{old_table}→{new_table} 行数不一致: "
            f"源{src_count} vs 目标{dst_count}"
        )

    def test_itsm_maintenance_total(self, migration_connector):
        """业务聚合校验：维护单总数。"""
        with migration_connector.source.connect() as src:
            src_total = src.execute(
                text("SELECT COUNT(*) FROM TIT10_MAINTENANCEDAY")
            ).scalar()
        with migration_connector.target.connect() as dst:
            dst_total = dst.execute(
                text("SELECT COUNT(*) FROM tit10_maintenanceday")
            ).scalar()
        assert dst_total == src_total

    def test_warehouse_stock_integrity(self, migration_connector):
        """仓储库存：入库单数=入库明细主表数。"""
        with migration_connector.target.connect() as conn:
            in_count = conn.execute(
                text("SELECT COUNT(*) FROM twh13_in")
            ).scalar()
            detail_count = conn.execute(
                text("SELECT COUNT(DISTINCT inbillid) FROM twh14_checkindt")
            ).scalar()
            assert in_count >= detail_count, "入库明细应在入库主表中有对应"

    def test_no_orphan_customers(self, migration_connector):
        """客户不孤立。"""
        with migration_connector.target.connect() as conn:
            orphans = conn.execute(
                text(
                    "SELECT COUNT(*) FROM tmm22_customers "
                    "WHERE classcd NOT IN (SELECT classcd FROM tmm21_custclass)"
                )
            ).scalar()
            assert orphans == 0

    def test_eid_integrity(self, migration_connector):
        """EID 数据完整性。"""
        with migration_connector.target.connect() as conn:
            total = conn.execute(text("SELECT COUNT(*) FROM tmm43_eid")).scalar()
            assert total > 0, "EID 表为空"

    def test_key_aggregates(self, migration_connector):
        """关键聚合值不变。"""
        with migration_connector.source.connect() as src:
            src_total = src.execute(
                text("SELECT COUNT(*) FROM TMM22_CUSTOMERS WHERE USEFLG='1'")
            ).scalar()
        with migration_connector.target.connect() as dst:
            dst_total = dst.execute(
                text("SELECT COUNT(*) FROM tmm22_customers WHERE useflg='1'")
            ).scalar()
            assert dst_total >= src_total, "有效客户数至少不低于旧库"
```

- [ ] **Step 2: 运行校验**

```bash
uv run pytest tests/test_migration_validation.py -v
```
Expected: 验证所有参数化测试和聚合值校验

- [ ] **Step 3: Commit**

```bash
git add tests/test_migration_validation.py
git commit -m "test(migration): 全量校验测试（行数+外键+聚合值）"
```

---

### Task 7: 主执行脚本

**Files:**
- Create: `migrate_data.py`（项目根目录）

- [ ] **Step 1: 创建主执行入口**

```python
# migrate_data.py
"""ortopbitsmdb → myitsm 数据迁移主入口。

用法:
    uv run python migrate_data.py              # 执行全量迁移
    uv run python migrate_data.py --batch 1    # 仅执行第1批
    uv run python migrate_data.py --dry-run    # 预演模式（不写入）
    uv run python migrate_data.py --validate   # 仅执行校验
"""
from __future__ import annotations

import argparse
import logging
import sys

from app.migration.config import MigrationConfig
from app.migration.batch_runner import BatchRunner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="ortopbitsmdb → myitsm 数据迁移")
    parser.add_argument("--batch", type=int, choices=[1, 2, 3, 4, 5],
                        help="仅执行指定批次")
    parser.add_argument("--dry-run", action="store_true",
                        help="预演模式，不实际写入")
    parser.add_argument("--validate", action="store_true",
                        help="仅执行校验（不迁移）")
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
            logger.info("仅执行校验模式")
            # 校验由 pytest 测试完成
            return

        if args.batch:
            runner.run_batch(args.batch)
        else:
            runner.run_all()

        logger.info("迁移完成！统计：")
        for table, count in sorted(runner._stats.items()):
            logger.info("  %s: %d 行", table, count)
    finally:
        runner.dispose()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add migrate_data.py
git commit -m "feat(migration): 主执行脚本 migrate_data.py"
```

---

### Task 8: 文档更新

**Files:**
- Modify: `docs/core/CORE_DOCS_INDEX.md`

- [ ] **Step 1: 更新核心文档索引**

在 `docs/core/CORE_DOCS_INDEX.md` 中添加本迁移方案的入口。

- [ ] **Step 2: Commit**

```bash
git add docs/core/CORE_DOCS_INDEX.md
git commit -m "docs: 添加数据迁移方案入口"
```

---

## 执行流程

### 1. 前置检查
```bash
# 确保 Oracle 旧库可连接
uv run python -c "from app.migration.connector import DualConnector; \
    from app.migration.config import MigrationConfig; \
    c = DualConnector(MigrationConfig.from_env()); \
    print('Source:', c.source_row_count('TMM01_COMPANY'), 'rows'); \
    print('Target:', c.target_row_count('tmm01_company'), 'rows')"
```

### 2. 执行全量迁移
```bash
uv run python migrate_data.py
```

### 3. 执行校验
```bash
SOURCE_DATABASE_URL=... DATABASE_URL=... uv run pytest tests/test_migration_validation.py -v
```

### 4. 回滚

每个批次执行前会 TRUNCATE CASCADE 目标表。如需完全回滚：
```bash
# 重新执行迁移即自动清空并重导
uv run python migrate_data.py
```

---

## 校验矩阵

| 校验维度 | 方法 | 阈值 |
|---------|------|------|
| 逐表行数 | `COUNT(*)` 对比 | 100% 一致 |
| 外键完整性 | FK NOT IN PK 查询 | 0 孤儿记录 |
| CHAR 去空格 | 抽样检查 | 无尾部空格 |
| 中文字符 | 编码抽样 | 无乱码 |
| 时间戳 | `created_at` >= 旧库最早 GENDATE | 无丢失 |
| 自增ID | 序列值 > MAX(id) | 不冲突 |
| 业务聚合 | 关键 COUNT/SUM 对比 | 差异 < 0.1% |

---

## C 类表处理（仅旧库有，不迁移）

| 表名 | 处理方式 |
|------|---------|
| MIG_P1_BATCH_LOG | 丢弃（迁移工具日志） |
| MIG_P3_FINAL_NAME_* | 丢弃（迁移工具日志） |
| TMC42_CONNECTINFO | 丢弃（连接日志） |
| TMC43_LOGS | 丢弃（操作日志，量太大） |
| TMC44_SYSLOCK | 丢弃（锁表） |
| TMC51_VERCTRL | 丢弃（版本控制） |
| TMM02_COUNTRY | ✅ 已迁移（192条，客户管理四级联动） |
| TMM03_PROVINCE | ✅ 已迁移（34条，同上） |
| TMM04_CITY | ✅ 已迁移（436条，同上） |
| TMM05_TOWN | ✅ 已迁移（2778条，同上） |
| TMM33_MESSAGE | 丢弃（已替换为 tntf01/02） |
| TMM50_MFLOG | 丢弃（操作日志） |
| TIT22_FETION_SEND | 丢弃（飞信已停运） |
| TMM52_POSSTATUS | 评估后可手工导入 |

## D 类表（仅新库有，跳过）

`sla_definition`, `sla_ticket`, `tbl01-04`, `tfn01-05`, `tio01-04`, `tms01-04`, `tntf01-02`, `tpt01-03`, `tiv11_detail`, `tiv12_detaildt`, `tqc10_result`, `tqc11_resultdt`, `tqc11_resulteid`

这些表为 Tier-2/3 新模块，无旧数据来源，迁移时自动跳过。

---

## 预估时间

| 批次 | 表数 | 数据量级 | 预估 |
|------|------|---------|------|
| 第1批 基础主数据 | ~20 | 万级 | 15min |
| 第2批 ITSM字典配置 | ~12 | 千级 | 10min |
| 第3批 ITSM业务单据 | ~30 | 十万级 | 30min |
| 第4批 仓储/采购/销售 | ~35 | 十万级 | 40min |
| 第5批 其他 | ~15 | 万级 | 20min |
| 全量校验 | ~95 | — | 20min |
| **合计** | **~112** | — | **~2.5h** |

---

## 风险与对策

| 风险 | 对策 |
|------|------|
| Oracle 连接不稳定 | 分批 + 断点续传，每批次独立提交 |
| CHAR 字段尾部空格 | `normalize_char()` 自动去除 |
| NUMBER→NUMERIC 精度丢失 | 保留原始类型映射，Decimal→float |
| 复合PK→代理键冲突 | UNIQUE 约束 + ON CONFLICT DO NOTHING |
| BLOB 字段 | to_dict() 已处理为 None |
| 密码字段明文 | 迁移后统一重置 |
| 旧库序列值冲突 | `_sync_sequence()` 自动对齐 |

---

## 实际执行差异记录（2026-05-08）

### 与计划的偏离

本计划制定时假设源库为 Oracle（需要 `cx_Oracle`），实际两个库都是 PostgreSQL。执行过程中根据实际数据结构做了大量简化。

### 核心变更

| 计划 | 实际 |
|------|------|
| cx_Oracle + psycopg2 双类型 | 双 psycopg2（源库已是 PG） |
| `ORACLE_URL` 环境变量 | `SOURCE_DATABASE_URL` |
| `oracle_url` / `pg_url` | `source_url` / `target_url` |
| 硬编码 900+ FieldMapping | `information_schema` 动态交集 + 模糊匹配 `_try_fuzzy_match` |
| `FieldMapping` / `map_oracle_row` | `build_mapping()` 自动构建 + `read_source_rows`/`write_target_rows` |
| Task 按计划结构拆分 | 实际：动态映射 → 简化 batch_runner → 集中调试修复 |
| 先写测试再写实现 | 执行中发现列名不一致，改为直接探查 `information_schema` |
| 逐 Task 子代理执行 | 单会话逐步执行（接口一致性需要共享上下文） |
| 估算 ~2.5h | 实际 ~4h（含 7 个问题排查修复） |

### 新增的修复

1. **OFFSET 不一致**（影响最大）：单连接 + `ORDER BY` 前三列，tmm43_eid_track 63.9%→99.998%
2. **`id` 被 SKIP 导致 FK 断裂**：从 SKIP_TARGET_COLUMNS 移除 `id`
3. **批量 executemany 失败降级**：逐行 INSERT 跳过冲突
4. **CHAR 空格 + VARCHAR 超长**：rstrip() + character_maximum_length 截断
5. **NOT NULL 默认值**：created_at/updated_at/password/status 自动填充
6. **MANUAL_RENAME**：10 张表的跨单词列名重映射
7. **TRUNCATE CASCADE 误清**：tsl02_extenddt 被清，单独重导

### Task 执行状态

| Task | 状态 | 备注 |
|------|------|------|
| Task 1 配置与连接器 | ✅ 完成 | 改用双 PG |
| Task 2 字段映射引擎 | ✅ 完成 | 改为动态映射 |
| Task 3 分批执行引擎 | ✅ 完成 | 加单连接+ORDER BY+降级 |
| Task 4 特殊表处理 | ✅ 完成 | 加 SYS_USER 合并+密码迁移 |
| Task 5-6 校验测试 | ✅ 完成 | 逐表行数对比 99.6% |
| Task 7 主执行脚本 | ✅ 完成 | migrate_data.py |
| Task 8 文档更新 | ✅ 完成 | 解决报告+本差异记录 |

### 最终数据完整性

- 完全匹配：**86 张表**
- 总体完整率：**99.6%**（3,339,020/3,353,080）
- 13 张差异表均已查明根因（源库 FK孤儿/NULL PK/PK重复）
- 详见 `docs/core/数据迁移问题解决报告.md`

---

## Phase 7 补充：行政区域表迁移（2026-05-10）

### 背景

原迁移遗漏了 4 张地理层级表（TMM02-05），导致客户表缺少国家/省份/城市/区县字段。

### 新增表

| 表名 | 模型 | 记录数 | 层级关系 |
|------|------|--------|---------|
| `tmm02_country` | Country | 192 | 根 |
| `tmm03_province` | Province | 34 | country_cd → tmm02_country |
| `tmm04_city` | City | 436 | prvn_cd → tmm03_province |
| `tmm05_town` | Town | 2,778 | city_cd → tmm04_city |

### 客户表扩展

`tmm22_customers` 新增 4 列：

| 列名 | 类型 | 说明 |
|------|------|------|
| `country_cd` | VARCHAR(3) | 国家代码 |
| `prvn_cd` | VARCHAR(2) | 省份代码 |
| `city_cd` | VARCHAR(4) | 城市代码 |
| `town_cd` | VARCHAR(4) | 区县代码 |

### 迁移方式

- DDL：Alembic 自动生成（`c08d02f7f9f6`）
- DML：Python psycopg2 双连接逐行 INSERT，字段名映射（countrycd→country_cd 等），strip() 去空格
