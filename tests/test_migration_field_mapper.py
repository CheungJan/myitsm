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
        assert fm.apply({"GENDATE": "2024-01-01"}) == "2024-01-01"

    def test_char_normalize(self):
        fm = FieldMapping(old_name="CUSTCD", new_name="custcd", transform="char")
        assert fm.apply({"CUSTCD": "ABC   "}) == "ABC"

    def test_default_value(self):
        fm = FieldMapping(new_name="source_type", default="DAILY")
        assert fm.apply({}) == "DAILY"

    def test_rename_only(self):
        fm = FieldMapping(old_name="old_col", new_name="new_col")
        assert fm.apply({"old_col": "hello"}) == "hello"

    def test_old_name_none_means_no_source(self):
        fm = FieldMapping(new_name="created_at", default=datetime(2024, 1, 1))
        assert fm.old_name is None
        assert fm.apply({}) == datetime(2024, 1, 1)

    def test_raises_when_no_old_name_and_no_default(self):
        with pytest.raises(ValueError, match="必须指定 old_name 或 default"):
            FieldMapping(new_name="orphan_field")


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
            "TIT03_SYSCODES", "TIT04_ARCHIVECODE", "TIT05_REPAIRINFO",
            "TMC01_MENUS", "TMC02_MENUSDT", "TMC03_USERMENUS",
            "TMC11_DEPARTMENTS", "TMC12_GROUPS", "TMC13_USERS",
            "TMM01_COMPANY", "TMM11_ITEMCLASS", "TMM12_ITEMS",
            "TMM18_SUPPLIERCLASS", "TMM19_SUPPLIERS", "TMM21_CUSTCLASS",
            "TMM22_CUSTOMERS", "TMM31_SYSCODES", "TMM34_IDMASTER",
            "TMC71_SYSPARM", "TMC41_ACCLOG",
        ]
        mapped = {m.old_table for m in MAPPINGS if m.old_table}
        for table in a_class_tables:
            assert table in mapped, f"{table} 缺少映射定义"

    def test_batch_order_is_sequential(self):
        batches = sorted({m.batch for m in MAPPINGS})
        assert batches == [1, 2, 3, 4, 5]


import pytest
