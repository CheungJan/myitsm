"""生产制造 MES API 测试（Tier-3 G7）。"""

from __future__ import annotations

from typing import Any

from flask.testing import FlaskClient


class TestWorkOrderAPI:
    """生产工单测试。"""

    def test_create_work_order(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/mes/work-orders",
            json={
                "wo_id": "WO001",
                "item_cd": "ITEM001",
                "plan_qty": 100,
                "plan_start": "2026-05-01",
                "plan_end": "2026-05-15",
            },
            headers=auth_header,
        )
        assert resp.status_code == 201
        data: dict[str, Any] = resp.get_json()
        assert data["data"]["plan_qty"] == 100

    def test_list_work_orders(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/mes/work-orders",
            json={"wo_id": "WO002", "item_cd": "ITEM002", "plan_qty": 50},
            headers=auth_header,
        )
        resp = client.get("/api/v1/mes/work-orders", headers=auth_header)
        assert resp.status_code == 200

    def test_update_work_order(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/mes/work-orders",
            json={"wo_id": "WO003", "item_cd": "ITEM003", "plan_qty": 200},
            headers=auth_header,
        )
        resp = client.put(
            "/api/v1/mes/work-orders/WO003",
            json={"status": "RELEASED"},
            headers=auth_header,
        )
        assert resp.status_code == 200

    def test_get_work_order_not_found(
        self, client: FlaskClient, auth_header: dict[str, str]
    ) -> None:
        resp = client.get("/api/v1/mes/work-orders/NOTEXIST", headers=auth_header)
        assert resp.status_code == 404


class TestProcessDefAPI:
    """工序定义测试。"""

    def test_create_process(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/mes/processes",
            json={
                "process_cd": "PROC001",
                "process_nm": "组装",
                "process_type": "ASSEMBLY",
                "std_hours": 2.5,
            },
            headers=auth_header,
        )
        assert resp.status_code == 201

    def test_list_processes(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/mes/processes",
            json={"process_cd": "PROC002", "process_nm": "测试", "process_type": "TEST"},
            headers=auth_header,
        )
        resp = client.get("/api/v1/mes/processes", headers=auth_header)
        assert resp.status_code == 200

    def test_update_process(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        client.post(
            "/api/v1/mes/processes",
            json={"process_cd": "PROC003", "process_nm": "包装", "process_type": "PACKAGE"},
            headers=auth_header,
        )
        resp = client.put(
            "/api/v1/mes/processes/PROC003",
            json={"remark": "更新"},
            headers=auth_header,
        )
        assert resp.status_code == 200


class TestWorkProcessAPI:
    """工单工序测试。"""

    def test_create_work_process(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/mes/work-processes",
            json={"wo_id": "WO001", "process_cd": "PROC001", "seq_no": 1},
            headers=auth_header,
        )
        assert resp.status_code == 201


class TestMaterialConsumeAPI:
    """物料消耗测试。"""

    def test_create_material(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.post(
            "/api/v1/mes/materials",
            json={
                "wo_id": "WO001",
                "item_cd": "MAT001",
                "plan_qty": 500,
                "actual_qty": 480,
                "consume_date": "2026-05-05",
            },
            headers=auth_header,
        )
        assert resp.status_code == 201

    def test_list_materials(self, client: FlaskClient, auth_header: dict[str, str]) -> None:
        resp = client.get("/api/v1/mes/work-orders/WO001/materials", headers=auth_header)
        assert resp.status_code == 200
