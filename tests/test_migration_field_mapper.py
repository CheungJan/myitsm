import os
import pytest
from app.migration.field_mapper import (
    SKIP_TARGET_COLUMNS,
    _try_fuzzy_match,
    _find_rename_map,
)


class TestSkipColumns:
    def test_created_at_is_skipped(self):
        assert "created_at" in SKIP_TARGET_COLUMNS

    def test_updated_at_is_skipped(self):
        assert "updated_at" in SKIP_TARGET_COLUMNS

    def test_id_is_skipped(self):
        assert "id" in SKIP_TARGET_COLUMNS

    def test_source_type_is_skipped(self):
        assert "source_type" in SKIP_TARGET_COLUMNS


class TestFuzzyMatch:
    def test_exact_match_found(self):
        src_cols = {"usercd", "usernm", "deptcd", "gendate"}
        assert _try_fuzzy_match("gendate", src_cols) == "gendate"

    def test_underscore_to_no_underscore(self):
        src_cols = {"usercd", "usernm", "deptcd", "gendate"}
        assert _try_fuzzy_match("user_cd", src_cols) == "usercd"
        assert _try_fuzzy_match("user_nm", src_cols) == "usernm"
        assert _try_fuzzy_match("dept_cd", src_cols) == "deptcd"

    def test_no_match_returns_none(self):
        src_cols = {"usercd", "usernm"}
        assert _try_fuzzy_match("phone", src_cols) is None

    def test_exact_match_when_both_exist(self):
        src_cols = {"user_cd", "usercd"}
        # 精确匹配优先
        assert _try_fuzzy_match("user_cd", src_cols) == "user_cd"


class TestFindRenameMap:
    def test_basic_rename(self):
        src_cols = {"usercd", "usernm", "deptcd", "gendate", "upddate", "useflg"}
        tgt_cols = {"user_cd", "user_nm", "dept_cd", "created_at", "updated_at", "useflg"}
        result = _find_rename_map(src_cols, tgt_cols)
        assert result["user_cd"] == "usercd"
        assert result["user_nm"] == "usernm"
        assert result["dept_cd"] == "deptcd"
        assert "useflg" not in result  # 同名，不需要重命名
        assert "created_at" not in result  # 在 SKIP 中

    def test_no_renames_when_all_same(self):
        src_cols = {"col_a", "col_b", "created_at"}
        tgt_cols = {"col_a", "col_b", "created_at", "updated_at"}
        result = _find_rename_map(src_cols, tgt_cols)
        assert result == {}


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql"),
    reason="需要 PostgreSQL 连接",
)
class TestBuildMappingWithPG:
    def test_build_mapping_for_tmc11(self):
        from sqlalchemy import create_engine
        from app.migration.field_mapper import build_mapping
        src = create_engine(os.environ["SOURCE_DATABASE_URL"])
        tgt = create_engine(os.environ["DATABASE_URL"])
        mapping = build_mapping(src, tgt, "tmc11_departments", "tmc11_departments")
        assert "gendate" in mapping.common_columns
        assert "useflg" in mapping.common_columns
        assert "created_at" not in mapping.common_columns
        src.dispose()
        tgt.dispose()
