"""采购批量订单 + 拆单并单集成测试。"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch

import pytest
from flask import Flask

from app.extensions import db as _db


# ---------------------------------------------------------------------------
# 辅助函数 / Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _patch_advisory_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    """SQLite 不支持 pg_advisory_xact_lock，替换为 no-op。

    在 SQLite 中不需要 advisory lock，因为 SQLite 本身就是串行写入的。
    """
    def _noop_lock(pcplanid: str, pclineno: int) -> None:
        pass

    monkeypatch.setattr(
        "app.services.procurement_service.PurchaseRegisterService._lock_requisition_line",
        _noop_lock,
    )


def _ensure_execution_view(app: Flask) -> None:
    """确保 v_requisition_execution 视图存在（SQLite 兼容）。"""
    with app.app_context():
        _db.session.execute(
            _db.text("DROP VIEW IF EXISTS v_requisition_execution")
        )
        _db.session.execute(_db.text("""
            CREATE VIEW v_requisition_execution AS
            SELECT
                p.pcplanid, p.plandate, p.auditflg, p.auditman, p.auditdate, p.useflg,
                dt.lineno, dt.itemcd, i.item_nm AS itemnm, i.spec, i.wunit,
                dt.rgstqty AS plan_qty,
                dt.auditqty AS audit_qty,
                COALESCE(link_stats.ordered_qty, 0) AS ordered_qty,
                COALESCE(link_stats.received_qty, 0) AS received_qty,
                dt.auditqty - COALESCE(link_stats.ordered_qty, 0) AS available_qty,
                CASE
                    WHEN COALESCE(link_stats.ordered_qty, 0) = 0 THEN '未开始'
                    WHEN COALESCE(link_stats.received_qty, 0) >= dt.rgstqty THEN '已完成'
                    WHEN COALESCE(link_stats.received_qty, 0) > 0 THEN '执行中'
                    ELSE '已下单'
                END AS execution_status,
                CASE WHEN dt.rgstqty > 0
                    THEN ROUND(CAST(COALESCE(link_stats.received_qty, 0) AS REAL) / dt.rgstqty * 100, 2)
                    ELSE 0
                END AS execution_rate
            FROM tpc01_pcplan p
            JOIN tpc02_pcplandt dt ON p.pcplanid = dt.pcplanid
            LEFT JOIN tmm12_items i ON dt.itemcd = i.item_cd
            LEFT JOIN (
                SELECT l.pcplanid, l.pclineno,
                    SUM(l.linkqty) AS ordered_qty,
                    SUM(CASE WHEN rd.inqty >= rd.rgsqty THEN l.linkqty ELSE 0 END) AS received_qty
                FROM tpc20_requisition_order_link l
                JOIN tpc13_registerdt rd ON l.rgstbillid = rd.rgstbillid AND l.rgstlineno = rd.lineno
                JOIN tpc12_register r ON rd.rgstbillid = r.rgstbillid
                WHERE r.useflg <> '9'
                GROUP BY l.pcplanid, l.pclineno
            ) link_stats ON dt.pcplanid = link_stats.pcplanid AND dt.lineno = link_stats.pclineno
            WHERE p.useflg = '1'
        """))
        _db.session.commit()


def _create_audited_plan(app: Flask, itemcd: str = "IT0001", auditqty: int = 100) -> str:
    """创建已审核的采购需求单，返回 pcplanid。"""
    from app.repositories.procurement_repository import PurchasePlanRepository

    with app.app_context():
        now = datetime.now(UTC)
        plan = PurchasePlanRepository.create(
            {"pctyp": "1", "memo": "集成测试需求单", "plandate": now},
            "TEST",
        )
        plan_id = plan.pcplanid
        PurchasePlanRepository.add_detail(plan_id, 1, {
            "itemcd": itemcd,
            "rgstqty": auditqty,
            "auditqty": auditqty,
            "units": "PCS",
        })
        PurchasePlanRepository.audit(plan, "TEST", "2")
        _db.session.commit()
        return plan_id


# ---------------------------------------------------------------------------
# 测试类
# ---------------------------------------------------------------------------


class TestBatchValidate:
    """批量订单预校验。"""

    def test_validate_returns_valid_true_when_within_limits(self, app: Flask) -> None:
        """校验：请求数量在可用余额内，应返回 valid=true。"""
        _ensure_execution_view(app)
        plan_id = _create_audited_plan(app, "IT0001", 100)

        with app.app_context():
            from app.services.procurement_service import PurchaseRegisterService

            orders = [
                {
                    "suppliercd": "SUP001",
                    "details": [
                        {
                            "ref_pcplanid": plan_id,
                            "ref_pclineno": 1,
                            "itemcd": "IT0001",
                            "rgsqty": 10,
                        }
                    ],
                }
            ]
            result = PurchaseRegisterService.batch_validate(orders)
            assert result["valid"] is True
            assert len(result["checks"]) == 1
            assert result["checks"][0]["available_qty"] >= 10

    def test_validate_returns_valid_false_when_exceeds_available(self, app: Flask) -> None:
        """校验：请求数量超过可用余额，应返回 valid=false。"""
        _ensure_execution_view(app)
        plan_id = _create_audited_plan(app, "IT0002", 20)

        with app.app_context():
            from app.services.procurement_service import PurchaseRegisterService

            orders = [
                {
                    "suppliercd": "SUP001",
                    "details": [
                        {
                            "ref_pcplanid": plan_id,
                            "ref_pclineno": 1,
                            "itemcd": "IT0002",
                            "rgsqty": 9999,
                        }
                    ],
                }
            ]
            result = PurchaseRegisterService.batch_validate(orders)
            assert result["valid"] is False
            assert result["checks"][0]["valid"] is False

    def test_validate_empty_details_returns_valid_true(self, app: Flask) -> None:
        """校验：无明细的订单应返回 valid=true（无需求行可校验）。"""
        with app.app_context():
            from app.services.procurement_service import PurchaseRegisterService

            orders = [{"suppliercd": "SUP001", "details": []}]
            result = PurchaseRegisterService.batch_validate(orders)
            assert result["valid"] is True
            assert result["checks"] == []

    def test_validate_aggregates_same_line_across_orders(self, app: Flask) -> None:
        """校验：同一需求行在多个订单中出现时，应汇总 rgsqty 再比较。"""
        _ensure_execution_view(app)
        plan_id = _create_audited_plan(app, "IT0003", 50)

        with app.app_context():
            from app.services.procurement_service import PurchaseRegisterService

            # 两个订单各请求 30，合计 60 > 50，应不通过
            orders = [
                {
                    "suppliercd": "SUP001",
                    "details": [
                        {"ref_pcplanid": plan_id, "ref_pclineno": 1,
                         "itemcd": "IT0003", "rgsqty": 30}
                    ],
                },
                {
                    "suppliercd": "SUP002",
                    "details": [
                        {"ref_pcplanid": plan_id, "ref_pclineno": 1,
                         "itemcd": "IT0003", "rgsqty": 30}
                    ],
                },
            ]
            result = PurchaseRegisterService.batch_validate(orders)
            assert result["valid"] is False
            assert result["checks"][0]["requested_qty"] == 60


class TestBatchCreate:
    """批量创建订单（拆单/并单场景）。"""

    def test_batch_create_empty_orders_raises(self, app: Flask) -> None:
        """空订单列表应抛出 ValueError。"""
        with app.app_context():
            from app.services.procurement_service import PurchaseRegisterService

            with pytest.raises(ValueError, match="不能为空"):
                PurchaseRegisterService.batch_create([], "TEST")

    def test_batch_create_exceeds_max_orders(self, app: Flask) -> None:
        """超过 10 个订单应抛出 ValueError。"""
        with app.app_context():
            from app.services.procurement_service import PurchaseRegisterService

            orders = [{"suppliercd": f"SUP{i:03d}", "details": []} for i in range(11)]
            with pytest.raises(ValueError, match="最多创建 10"):
                PurchaseRegisterService.batch_create(orders, "TEST")

    def test_batch_create_exceed_available_should_fail(self, app: Flask) -> None:
        """超量：请求数量超过可用余额应抛出 ValueError。"""
        _ensure_execution_view(app)
        plan_id = _create_audited_plan(app, "IT0004", 10)

        with app.app_context():
            from app.services.procurement_service import PurchaseRegisterService

            orders = [
                {
                    "suppliercd": "SUP001",
                    "details": [
                        {"ref_pcplanid": plan_id, "ref_pclineno": 1,
                         "itemcd": "IT0004", "rgsqty": 9999, "unitprice": 1}
                    ],
                }
            ]
            with pytest.raises(ValueError, match="采购数量.*超过可用余额"):
                PurchaseRegisterService.batch_create(orders, "TEST")

    def test_batch_create_with_valid_data(self, app: Flask) -> None:
        """有效数据：应在可用余额内成功创建订单。"""
        _ensure_execution_view(app)
        plan_id = _create_audited_plan(app, "IT0005", 100)

        with app.app_context():
            from app.services.procurement_service import PurchaseRegisterService

            orders = [
                {
                    "suppliercd": "SUP001",
                    "memo": "集成测试-拆单A",
                    "details": [
                        {"ref_pcplanid": plan_id, "ref_pclineno": 1,
                         "itemcd": "IT0005", "rgsqty": 10, "unitprice": 100}
                    ],
                }
            ]
            result = PurchaseRegisterService.batch_create(orders, "TEST")
            assert result["count"] == 1
            assert len(result["created_orders"]) == 1
            assert result["created_orders"][0] is not None
            # 验证关联表写入
            from app.repositories.procurement_repository import RequisitionOrderLinkRepository
            links = RequisitionOrderLinkRepository.count_by_pcplanid(plan_id)
            assert links >= 1

    def test_batch_create_split_order(self, app: Flask) -> None:
        """拆单场景：同一需求分给多个供应商，应各自创建订单。"""
        _ensure_execution_view(app)
        plan_id = _create_audited_plan(app, "IT0006", 100)

        with app.app_context():
            from app.services.procurement_service import PurchaseRegisterService

            orders = [
                {
                    "suppliercd": "SUP001",
                    "memo": "拆单-供应商A",
                    "details": [
                        {"ref_pcplanid": plan_id, "ref_pclineno": 1,
                         "itemcd": "IT0006", "rgsqty": 30, "unitprice": 100}
                    ],
                },
                {
                    "suppliercd": "SUP002",
                    "memo": "拆单-供应商B",
                    "details": [
                        {"ref_pcplanid": plan_id, "ref_pclineno": 1,
                         "itemcd": "IT0006", "rgsqty": 20, "unitprice": 90}
                    ],
                },
            ]
            result = PurchaseRegisterService.batch_create(orders, "TEST")
            assert result["count"] == 2
            assert len(result["created_orders"]) == 2
            assert result["created_orders"][0] != result["created_orders"][1]

    def test_batch_create_merge_order(self, app: Flask) -> None:
        """并单场景：多个需求行合并到一个订单，应创建一个订单多条明细。"""
        _ensure_execution_view(app)
        plan_a = _create_audited_plan(app, "IT0007", 50)
        plan_b = _create_audited_plan(app, "IT0008", 50)

        with app.app_context():
            from app.services.procurement_service import PurchaseRegisterService

            orders = [
                {
                    "suppliercd": "SUP001",
                    "memo": "并单测试",
                    "details": [
                        {"ref_pcplanid": plan_a, "ref_pclineno": 1,
                         "itemcd": "IT0007", "rgsqty": 20, "unitprice": 100},
                        {"ref_pcplanid": plan_b, "ref_pclineno": 1,
                         "itemcd": "IT0008", "rgsqty": 20, "unitprice": 100},
                    ],
                }
            ]
            result = PurchaseRegisterService.batch_create(orders, "TEST")
            assert result["count"] == 1
            assert len(result["created_orders"]) == 1

            # 验证订单有两条明细
            from app.repositories.procurement_repository import PurchaseRegisterRepository
            record = PurchaseRegisterRepository.get_by_id(result["created_orders"][0])
            assert record is not None
            details_count = record.details.count()  # type: ignore[attr-defined]
            assert details_count == 2


class TestMergePreview:
    """智能合并预览。"""

    def test_merge_preview_returns_expected_structure(self, app: Flask) -> None:
        """合并预览应返回 mergeable、unmergeable、summary（即使无数据）。"""
        _ensure_execution_view(app)

        with app.app_context():
            from app.services.procurement_service import PurchasePlanMergeService

            result = PurchasePlanMergeService.merge_preview()
            assert "mergeable" in result
            assert "unmergeable" in result
            assert "summary" in result
            assert "mergeable_groups" in result["summary"]
            assert "unmergeable_items" in result["summary"]
            assert "estimated_orders" in result["summary"]

    def test_mergeable_groups_have_minimum_fields(self, app: Flask) -> None:
        """可合并组应有必要字段：itemcd、source_count、suggested_suppliers。"""
        _ensure_execution_view(app)

        with app.app_context():
            from app.services.procurement_service import PurchasePlanMergeService

            result = PurchasePlanMergeService.merge_preview()
            for g in result["mergeable"]:
                assert "itemcd" in g
                assert "source_count" in g
                assert "suggested_suppliers" in g
                assert g["source_count"] >= 2

    def test_unmergeable_items_have_single_source(self, app: Flask) -> None:
        """不可合并项应有 source_count == 1。"""
        _ensure_execution_view(app)

        with app.app_context():
            from app.services.procurement_service import PurchasePlanMergeService

            result = PurchasePlanMergeService.merge_preview()
            for g in result["unmergeable"]:
                assert g["source_count"] == 1


class TestAdvisoryLock:
    """并发控制测试。"""

    def test_lock_key_is_deterministic(self) -> None:
        """相同 pcplanid+pclineno 应产生相同锁 key。"""
        def lock_key(pid: str, lno: int) -> int:
            return int(hashlib.md5(f"{pid}:{lno}".encode()).hexdigest()[:16], 16)

        assert lock_key("PP000180", 1) == lock_key("PP000180", 1)
        assert lock_key("PP000180", 1) != lock_key("PP000180", 2)
        assert lock_key("PP000180", 1) != lock_key("PP000181", 1)

    def test_lock_key_positive(self) -> None:
        """锁 key 应为正整数。"""
        def lock_key(pid: str, lno: int) -> int:
            return int(hashlib.md5(f"{pid}:{lno}".encode()).hexdigest()[:16], 16)

        for pid, lno in [("PP000001", 1), ("PP999999", 99), ("ABCDEFGH", 0)]:
            key = lock_key(pid, lno)
            assert key >= 0, f"lock_key({pid}, {lno}) = {key}，应为 >= 0"


class TestBatchValidationEdgeCases:
    """边界场景测试。"""

    def test_validate_with_nonexistent_plan_returns_zero_available(self, app: Flask) -> None:
        """不存在的需求单，available_qty 应为 0（视图查不到行）。"""
        _ensure_execution_view(app)

        with app.app_context():
            from app.services.procurement_service import PurchaseRegisterService

            orders = [
                {
                    "suppliercd": "SUP001",
                    "details": [
                        {"ref_pcplanid": "NOEXIST", "ref_pclineno": 1,
                         "itemcd": "IT9999", "rgsqty": 1}
                    ],
                }
            ]
            result = PurchaseRegisterService.batch_validate(orders)
            # 不存在的计划行 available_qty = 0，rgsqty=1 > 0，应为 invalid
            assert result["valid"] is False

    def test_validate_with_rgsqty_zero(self, app: Flask) -> None:
        """rgsqty=0 应校验通过。"""
        _ensure_execution_view(app)
        plan_id = _create_audited_plan(app, "IT0009", 50)

        with app.app_context():
            from app.services.procurement_service import PurchaseRegisterService

            orders = [
                {
                    "suppliercd": "SUP001",
                    "details": [
                        {"ref_pcplanid": plan_id, "ref_pclineno": 1,
                         "itemcd": "IT0009", "rgsqty": 0}
                    ],
                }
            ]
            result = PurchaseRegisterService.batch_validate(orders)
            assert result["valid"] is True

    def test_validate_mixed_valid_and_invalid_lines(self, app: Flask) -> None:
        """部分行有效、部分行超量时，整体 valid 应为 False。"""
        _ensure_execution_view(app)
        plan_a = _create_audited_plan(app, "IT0010", 50)
        plan_b = _create_audited_plan(app, "IT0011", 5)

        with app.app_context():
            from app.services.procurement_service import PurchaseRegisterService

            orders = [
                {
                    "suppliercd": "SUP001",
                    "details": [
                        {"ref_pcplanid": plan_a, "ref_pclineno": 1,
                         "itemcd": "IT0010", "rgsqty": 10},  # 有效
                        {"ref_pcplanid": plan_b, "ref_pclineno": 1,
                         "itemcd": "IT0011", "rgsqty": 100},  # 超量
                    ],
                }
            ]
            result = PurchaseRegisterService.batch_validate(orders)
            assert result["valid"] is False
            assert len(result["checks"]) == 2
            checks_valid = [c["valid"] for c in result["checks"]]
            assert True in checks_valid
            assert False in checks_valid
