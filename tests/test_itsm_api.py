"""ITSM 核心 API 测试。"""

from __future__ import annotations

import json
from typing import Any

from flask import Flask
from flask.testing import FlaskClient


def _auth_header(app: Flask) -> dict[str, str]:
    """生成 JWT 认证头。"""
    import jwt

    payload = {"sub": "T00001", "exp": 9999999999}
    token: str = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
    return {"Authorization": f"Bearer {token}", "X-User-Cd": "T00001"}


def _post(client: FlaskClient, url: str, data: dict[str, Any], headers: dict[str, str]) -> Any:
    return client.post(url, data=json.dumps(data), content_type="application/json", headers=headers)


# ---------------------------------------------------------------------------
# 日常维护单
# ---------------------------------------------------------------------------


class TestMaintenanceDaily:
    """日常维护单 CRUD + 状态流转测试。"""

    def test_create_and_get(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/maintenance-daily",
            {
                "store_id": "S0000001",
                "fault_type": "01",
                "short_description": "POS机无法开机",
            },
            headers,
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["code"] == 201
        mid = body["data"]["maintenance_id"]

        resp2 = client.get(f"/api/v1/itsm/maintenance-daily/{mid}", headers=headers)
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["store_id"] == "S0000001"

    def test_list(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = client.get("/api/v1/itsm/maintenance-daily?page=1&per_page=10", headers=headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert "items" in body["data"]
        assert "total" in body["data"]

    def test_transition_valid(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/maintenance-daily",
            {"store_id": "S0000002", "short_description": "测试状态流转"},
            headers,
        )
        mid = resp.get_json()["data"]["maintenance_id"]

        resp2 = _post(
            client,
            f"/api/v1/itsm/maintenance-daily/{mid}/transition",
            {"to_status": "2"},
            headers,
        )
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["success"] is True

    def test_transition_invalid(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/maintenance-daily",
            {"store_id": "S0000003"},
            headers,
        )
        mid = resp.get_json()["data"]["maintenance_id"]

        resp2 = _post(
            client,
            f"/api/v1/itsm/maintenance-daily/{mid}/transition",
            {"to_status": "5"},
            headers,
        )
        assert resp2.status_code == 400

    def test_update(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/maintenance-daily",
            {"store_id": "S0000004"},
            headers,
        )
        mid = resp.get_json()["data"]["maintenance_id"]

        resp2 = client.put(
            f"/api/v1/itsm/maintenance-daily/{mid}",
            data=json.dumps({"memo": "更新测试"}),
            content_type="application/json",
            headers=headers,
        )
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["memo"] == "更新测试"


# ---------------------------------------------------------------------------
# 公用附表
# ---------------------------------------------------------------------------


class TestD2D:
    """上门服务记录测试。"""

    def test_create_and_list(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/d2d",
            {
                "maintenance_id": "MD000001",
                "d2d_engineer": "E00001",
                "d2d_type": "1",
                "d2d_descripiton": "到店检修",
            },
            headers,
        )
        assert resp.status_code == 201

        resp2 = client.get("/api/v1/itsm/d2d/MD000001", headers=headers)
        assert resp2.status_code == 200
        items = resp2.get_json()["data"]
        assert len(items) >= 1


class TestCloseBill:
    """关单记录测试。"""

    def test_create_and_list(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/close-bill",
            {"maintenance_id": "MD000002", "close_type": "01", "description": "正常关单"},
            headers,
        )
        assert resp.status_code == 201

        resp2 = client.get("/api/v1/itsm/close-bill/MD000002", headers=headers)
        assert resp2.status_code == 200
        items = resp2.get_json()["data"]
        assert len(items) >= 1


class TestDispatch:
    """分派记录测试。"""

    def test_create_and_list(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/dispatch",
            {
                "maintenance_id": "MD000003",
                "maintenance_type": "MD",
                "accpectder": "E00002",
            },
            headers,
        )
        assert resp.status_code == 201

        resp2 = client.get("/api/v1/itsm/dispatch/MD000003", headers=headers)
        assert resp2.status_code == 200


# ---------------------------------------------------------------------------
# 设备变更单
# ---------------------------------------------------------------------------


class TestDeviceChange:
    """设备变更单 CRUD + CK 磁卡号历史优化测试。"""

    def test_create_ck(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/device-change",
            {
                "store_id": "S0000010",
                "change_type": "CK",
                "new_store_card": "NEWCARD001",
                "short_description": "磁卡号变更",
            },
            headers,
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["data"]["change_type"] == "CK"

    def test_list_with_type_filter(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = client.get(
            "/api/v1/itsm/device-change?change_type=CK",
            headers=headers,
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 回收任务（TIT20，P0-1/优化4.2）
# ---------------------------------------------------------------------------


class TestRecycleTask:
    """回收任务 CRUD + 状态流转 + 明细测试。"""

    def test_create_and_get(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/recycle-task",
            {
                "cust_cd": "S0000020",
                "recycle_type": "01",
                "asset_count": 3,
                "target_warehouse": "WH001",
                "remark": "预计划触发回收",
            },
            headers,
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["code"] == 201
        rid = body["data"]["recycle_id"]

        resp2 = client.get(f"/api/v1/itsm/recycle-task/{rid}", headers=headers)
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["cust_cd"] == "S0000020"

    def test_list(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = client.get("/api/v1/itsm/recycle-task", headers=headers)
        assert resp.status_code == 200

    def test_transition(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/recycle-task",
            {"cust_cd": "S0000021", "recycle_type": "02"},
            headers,
        )
        rid = resp.get_json()["data"]["recycle_id"]

        resp2 = _post(
            client,
            f"/api/v1/itsm/recycle-task/{rid}/transition",
            {"to_status": "2"},
            headers,
        )
        assert resp2.status_code == 200
        assert resp2.get_json()["data"]["from_status"] == "1"
        assert resp2.get_json()["data"]["to_status"] == "2"

    def test_add_detail(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        resp = _post(
            client,
            "/api/v1/itsm/recycle-task",
            {"cust_cd": "S0000022", "recycle_type": "01"},
            headers,
        )
        rid = resp.get_json()["data"]["recycle_id"]

        resp2 = _post(
            client,
            f"/api/v1/itsm/recycle-task/{rid}/details",
            {"asset_id": "POS001", "asset_type": "OLD", "expected_status": "PENDING"},
            headers,
        )
        assert resp2.status_code == 201

        resp3 = client.get(f"/api/v1/itsm/recycle-task/{rid}/details", headers=headers)
        assert resp3.status_code == 200
        items = resp3.get_json()["data"]
        assert len(items) >= 1
        assert items[0]["asset_id"] == "POS001"


# ---------------------------------------------------------------------------
# A4：D2D 4 模式端到端 + 跨单据类型 MD/MO/MR/BY/BG
# ---------------------------------------------------------------------------


class TestD2DFourModesE2E:
    """A4 端到端：到店/离店/催单/记录 4 模式 × MD/MO/MR/BY/BG 5 种单据类型。

    覆盖：
    - 4 模式分组校验（到店新分组、离店用最后分组、催单阻断到店未离店）
    - 离店主表联动（current_status = d2d_result）
    - 跨单据类型主表查询（_find_main_record 按 PK 字段适配）
    - default-engineer 接口可访问
    """

    def _create_md(self, client: FlaskClient, headers: dict[str, str]) -> str:
        resp = _post(
            client,
            "/api/v1/itsm/maintenance-daily",
            {"store_id": "S0000040", "fault_type": "01", "short_description": "A4 MD"},
            headers,
        )
        assert resp.status_code == 201
        return resp.get_json()["data"]["maintenance_id"]

    def _create_mo(self, client: FlaskClient, headers: dict[str, str]) -> str:
        resp = _post(
            client,
            "/api/v1/itsm/maintenance-open",
            {"store_id": "S0000041", "short_description": "A4 MO"},
            headers,
        )
        assert resp.status_code == 201
        return resp.get_json()["data"]["new_opening_id"]

    def _create_mr(self, client: FlaskClient, headers: dict[str, str]) -> str:
        resp = _post(
            client,
            "/api/v1/itsm/maintenance-renovate",
            {"store_id": "S0000042", "short_description": "A4 MR"},
            headers,
        )
        assert resp.status_code == 201
        return resp.get_json()["data"]["renew_id"]

    def _create_bg(self, client: FlaskClient, headers: dict[str, str]) -> str:
        resp = _post(
            client,
            "/api/v1/itsm/device-change",
            {"store_id": "S0000043", "change_type": "CK", "new_store_card": "CARD-A4"},
            headers,
        )
        assert resp.status_code == 201
        return resp.get_json()["data"]["device_change_id"]

    def _create_by(self, app: Flask) -> str:
        """BY 保养单无 create API，直接模型插入。"""
        from app.extensions import db as _db
        from app.models.itsm import Maintenance
        from datetime import datetime, UTC

        with app.app_context():
            rec = Maintenance(
                daily_maintenance_id="BY00A401",
                store_id="S0000044",
                current_status="1",
                create_time=datetime.now(UTC),
                creator="T00001",
                update_time=datetime.now(UTC),
                updator="T00001",
            )
            _db.session.add(rec)
            _db.session.commit()
            return rec.daily_maintenance_id

    def _four_modes(self, client: FlaskClient, headers: dict[str, str], mid: str) -> None:
        """对指定单据执行 4 模式端到端。"""
        # 1. 到店
        r1 = _post(
            client,
            f"/api/v1/itsm/d2d/arrive-store/{mid}",
            {"d2d_engineer": "E00001", "d2d_descripiton": "到店检修"},
            headers,
        )
        assert r1.status_code == 201, r1.get_json()
        assert r1.get_json()["data"]["d2d_type"] == "1"
        assert r1.get_json()["data"]["d2d_group"] == 1

        # 2. 离店（d2d_result=5 已解决，填 phenomenon + handling + gzdm）
        r2 = _post(
            client,
            f"/api/v1/itsm/d2d/leave-store/{mid}",
            {
                "d2d_engineer": "E00001",
                "d2d_result": "5",
                "d2d_phenomenon": "设备无法开机",
                "d2d_handling": "更换电源模块",
                "gzdm": "01010101",
            },
            headers,
        )
        assert r2.status_code == 201, r2.get_json()
        assert r2.get_json()["data"]["d2d_type"] == "2"
        assert r2.get_json()["data"]["d2d_group"] == 1

        # 3. 催单（最后是离店，允许催单）
        r3 = _post(
            client,
            f"/api/v1/itsm/d2d/urge/{mid}",
            {"d2d_engineer": "E00001", "d2d_descripiton": "客户催促"},
            headers,
        )
        assert r3.status_code == 201, r3.get_json()
        assert r3.get_json()["data"]["d2d_type"] == "3"

        # 4. 记录
        r4 = _post(
            client,
            f"/api/v1/itsm/d2d/record/{mid}",
            {"d2d_engineer": "E00001", "d2d_descripiton": "客户反馈正常"},
            headers,
        )
        assert r4.status_code == 201, r4.get_json()
        assert r4.get_json()["data"]["d2d_type"] == "4"

        # 5. 列表应含 4 条，且每条 business_operation_id 非空
        lst = client.get(f"/api/v1/itsm/d2d/{mid}", headers=headers)
        assert lst.status_code == 200
        items = lst.get_json()["data"]
        assert len(items) >= 4
        types = {it["d2d_type"] for it in items}
        assert {"1", "2", "3", "4"}.issubset(types)
        for it in items:
            assert it["business_operation_id"] is not None

    def test_md_e2e(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        mid = self._create_md(client, headers)
        self._four_modes(client, headers, mid)
        # 离店后主表 current_status 应为 d2d_result='5'，faultcode 应含 gzdm
        resp = client.get(f"/api/v1/itsm/maintenance-daily/{mid}", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["current_status"] == "5"
        assert "01010101" in (data.get("faultcode") or "")

    def test_mo_e2e(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        mid = self._create_mo(client, headers)
        self._four_modes(client, headers, mid)
        resp = client.get(f"/api/v1/itsm/maintenance-open/{mid}", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["current_status"] == "5"

    def test_mr_e2e(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        mid = self._create_mr(client, headers)
        self._four_modes(client, headers, mid)
        resp = client.get(f"/api/v1/itsm/maintenance-renovate/{mid}", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["current_status"] == "5"

    def test_bg_e2e(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        mid = self._create_bg(client, headers)
        self._four_modes(client, headers, mid)
        resp = client.get(f"/api/v1/itsm/device-change/{mid}", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["current_status"] == "5"

    def test_by_e2e(self, app: Flask, client: FlaskClient) -> None:
        headers = _auth_header(app)
        mid = self._create_by(app)
        self._four_modes(client, headers, mid)
        resp = client.get(f"/api/v1/itsm/maintenance/{mid}", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["current_status"] == "5"

    def test_group_check_arrive_after_arrive(self, app: Flask, client: FlaskClient) -> None:
        """分组校验：连续两次到店应被拒绝。"""
        headers = _auth_header(app)
        mid = self._create_md(client, headers)
        r1 = _post(client, f"/api/v1/itsm/d2d/arrive-store/{mid}",
                   {"d2d_engineer": "E00001"}, headers)
        assert r1.status_code == 201
        r2 = _post(client, f"/api/v1/itsm/d2d/arrive-store/{mid}",
                   {"d2d_engineer": "E00001"}, headers)
        assert r2.status_code == 400

    def test_group_check_leave_without_arrive(self, app: Flask, client: FlaskClient) -> None:
        """分组校验：无到店记录直接离店应被拒绝。"""
        headers = _auth_header(app)
        mid = self._create_md(client, headers)
        r = _post(client, f"/api/v1/itsm/d2d/leave-store/{mid}",
                  {"d2d_engineer": "E00001", "d2d_result": "5",
                   "d2d_phenomenon": "x", "d2d_handling": "y"}, headers)
        assert r.status_code == 400

    def test_group_check_urge_before_leave(self, app: Flask, client: FlaskClient) -> None:
        """分组校验：到店未离店时催单应被拒绝。"""
        headers = _auth_header(app)
        mid = self._create_md(client, headers)
        _post(client, f"/api/v1/itsm/d2d/arrive-store/{mid}",
              {"d2d_engineer": "E00001"}, headers)
        r = _post(client, f"/api/v1/itsm/d2d/urge/{mid}",
                  {"d2d_engineer": "E00001"}, headers)
        assert r.status_code == 400

    def test_leave_result3_requires_closure_reason(self, app: Flask, client: FlaskClient) -> None:
        """d2d_result='3' 关闭时 closure_reason 必填。"""
        headers = _auth_header(app)
        mid = self._create_md(client, headers)
        _post(client, f"/api/v1/itsm/d2d/arrive-store/{mid}",
              {"d2d_engineer": "E00001"}, headers)
        r = _post(client, f"/api/v1/itsm/d2d/leave-store/{mid}",
                  {"d2d_engineer": "E00001", "d2d_result": "3",
                   "d2d_handling": "关闭处理"}, headers)
        assert r.status_code == 400

    def test_default_engineer_endpoint(self, app: Flask, client: FlaskClient) -> None:
        """default-engineer 接口可访问，返回 engineer + source 字段。"""
        headers = _auth_header(app)
        mid = self._create_md(client, headers)
        resp = client.get(f"/api/v1/itsm/d2d/{mid}/default-engineer", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "engineer" in data
        assert "source" in data

    def test_urge_without_any_record(self, app: Flask, client: FlaskClient) -> None:
        """无任何 d2d 记录时催单应允许（门店报修后催单）。"""
        headers = _auth_header(app)
        mid = self._create_md(client, headers)
        r = _post(
            client,
            f"/api/v1/itsm/d2d/urge/{mid}",
            {"d2d_engineer": "E00001"},
            headers,
        )
        assert r.status_code == 201
        assert r.get_json()["data"]["d2d_type"] == "3"

    def test_group_check_leave_after_leave(self, app: Flask, client: FlaskClient) -> None:
        """分组校验：已离店再次离店应被拒绝。"""
        headers = _auth_header(app)
        mid = self._create_md(client, headers)
        _post(
            client,
            f"/api/v1/itsm/d2d/arrive-store/{mid}",
            {"d2d_engineer": "E00001"},
            headers,
        )
        _post(
            client,
            f"/api/v1/itsm/d2d/leave-store/{mid}",
            {
                "d2d_engineer": "E00001",
                "d2d_result": "5",
                "d2d_phenomenon": "x",
                "d2d_handling": "y",
            },
            headers,
        )
        r = _post(
            client,
            f"/api/v1/itsm/d2d/leave-store/{mid}",
            {
                "d2d_engineer": "E00001",
                "d2d_result": "5",
                "d2d_phenomenon": "x",
                "d2d_handling": "y",
            },
            headers,
        )
        assert r.status_code == 400
