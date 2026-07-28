"""V3 测试：entitlement API 端点集成测试。

验证 1a 阶段 C8/C9 的后端 API：
  GET /api/v1/itsm/entitlement/resolve — 权益+推荐c_type+推荐SR
  GET /api/v1/itsm/entitlement/price — 价格带出

对齐文档 §3.5.4 c_type 推荐规则和 §3.5.5 价格带出规则。
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from flask import Flask
from flask.testing import FlaskClient

from app.extensions import db
from app.models.inventory import Price
from app.models.master import Customer, CustPosRl, Eid
from app.models.sales import PlanCust


def _auth_header(app: Flask) -> dict[str, str]:
    """生成 JWT 认证头。"""
    import jwt

    payload = {"sub": "T00001", "exp": 9999999999}
    token: str = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
    return {"Authorization": f"Bearer {token}", "X-User-Cd": "T00001"}


def _seed_customer(cust_cd: str = "CUSTV3") -> Customer:
    existing = db.session.get(Customer, cust_cd)
    if existing:
        return existing
    record = Customer(
        cust_cd=cust_cd,
        cust_nm=f"测试客户{cust_cd}",
        cust_card="CARDV3",
        useflg="1",
        customer_status="ACTIVE",
    )
    db.session.add(record)
    return record


def _seed_eid(
    eid: str,
    asset_owner: str = "03",
    warranty_expire: datetime | None = None,
    itemcd: str = "ITV3001",
) -> Eid:
    existing = db.session.query(Eid).filter(Eid.eid == eid).first()
    if existing:
        return existing
    record = Eid(
        itemcd=itemcd,
        eid=eid,
        opercd="T00001",
        gendate=datetime.now(UTC),
        useflg="1",
        sflg="1",
        asset_owner=asset_owner,
        warranty_expire=warranty_expire,
    )
    db.session.add(record)
    return record


def _seed_price(itemcd: str = "ITV3001", busityp: str = "10", price: float = 1500.0) -> Price:
    existing = (
        db.session.query(Price)
        .filter(Price.itemcd == itemcd, Price.busityp == busityp)
        .first()
    )
    if existing:
        return existing
    record = Price(
        itemcd=itemcd,
        busityp=busityp,
        itemprice=price,
        opercd="T00001",
        gendate=datetime.now(UTC),
        useflg="1",
        is_current=True,
    )
    db.session.add(record)
    return record


def _seed_rl(cust_cd: str, eid: str, business_mode: str = "01") -> CustPosRl:
    """创建测试 CustPosRl（设备绑定到门店+业务模式）。"""
    record = CustPosRl(
        cust_cd=cust_cd,
        eid=eid,
        item_cd="ITV3001",
        useflg="1",
        posupddate=datetime.now(UTC),
        asset_status="ACTIVE",
        created_from="MAINTENANCE_OPEN",
        business_mode=business_mode,
    )
    db.session.add(record)
    return record


class TestEntitlementResolveAPI:
    """GET /api/v1/itsm/entitlement/resolve 集成测试。"""

    def test_commercial_recommends_c_type_1(self, app: Flask, client: FlaskClient) -> None:
        """商用电子设备 → c_type 推荐 '1'（配件更换免费）。"""
        with app.app_context():
            _seed_customer()
            _seed_eid("EIDV3001", asset_owner="01")
            db.session.commit()

        resp = client.get(
            "/api/v1/itsm/entitlement/resolve?eid=EIDV3001&cust_cd=CUSTV3",
            headers=_auth_header(app),
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["code"] == 200
        data = body["data"]
        assert data["recommended_c_type"] == "1"
        assert data["asset_owner"] == "01"

    def test_customer_in_warranty_recommends_c_type_1(self, app: Flask, client: FlaskClient) -> None:
        """门店资产保内设备 → c_type 推荐 '1'（配件更换免费）。"""
        with app.app_context():
            _seed_customer()
            _seed_eid(
                "EIDV3002",
                asset_owner="03",
                warranty_expire=datetime.now(UTC) + timedelta(days=30),
            )
            _seed_rl("CUSTV3", "EIDV3002", business_mode="01")
            db.session.commit()

        resp = client.get(
            "/api/v1/itsm/entitlement/resolve?eid=EIDV3002&cust_cd=CUSTV3",
            headers=_auth_header(app),
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["recommended_c_type"] == "1"
        assert data["entitlement"]["free"] is True
        assert data["entitlement"]["reason"] == "保内"

    def test_customer_out_of_warranty_recommends_c_type_2(self, app: Flask, client: FlaskClient) -> None:
        """门店资产过保设备 → c_type 推荐 '2'（购买）。"""
        with app.app_context():
            _seed_customer()
            _seed_eid(
                "EIDV3003",
                asset_owner="03",
                warranty_expire=datetime.now(UTC) - timedelta(days=1),
            )
            _seed_rl("CUSTV3", "EIDV3003", business_mode="01")
            db.session.commit()

        resp = client.get(
            "/api/v1/itsm/entitlement/resolve?eid=EIDV3003&cust_cd=CUSTV3",
            headers=_auth_header(app),
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["recommended_c_type"] == "2"
        assert data["entitlement"]["free"] is False

    def test_no_eid_returns_400(self, app: Flask, client: FlaskClient) -> None:
        """缺少 eid 参数 → 400。"""
        resp = client.get(
            "/api/v1/itsm/entitlement/resolve?cust_cd=CUSTV3",
            headers=_auth_header(app),
        )
        assert resp.status_code == 400

    def test_eid_not_found_returns_404(self, app: Flask, client: FlaskClient) -> None:
        """设备不存在 → 404。"""
        resp = client.get(
            "/api/v1/itsm/entitlement/resolve?eid=NONEXISTENT",
            headers=_auth_header(app),
        )
        assert resp.status_code == 404

    def test_recommended_sr_in_warranty(self, app: Flask, client: FlaskClient) -> None:
        """保内门店资产 → recommended_sr='01' 内部（我们自己修，不是厂商）。"""
        with app.app_context():
            _seed_customer()
            _seed_eid(
                "EIDV3004",
                asset_owner="03",
                warranty_expire=datetime.now(UTC) + timedelta(days=30),
            )
            db.session.commit()

        resp = client.get(
            "/api/v1/itsm/entitlement/resolve?eid=EIDV3004",
            headers=_auth_header(app),
        )
        data = resp.get_json()["data"]
        assert data["recommended_sr"] == "01"


class TestEntitlementPriceAPI:
    """GET /api/v1/itsm/entitlement/price 集成测试。"""

    def test_returns_sale_price(self, app: Flask, client: FlaskClient) -> None:
        """正常查询返回销售价。"""
        with app.app_context():
            _seed_customer()
            _seed_price("ITV3001", "10", 1500.0)
            db.session.commit()

        resp = client.get(
            "/api/v1/itsm/entitlement/price?cust_cd=CUSTV3&itemcd=ITV3001",
            headers=_auth_header(app),
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["price"] == 1500.0
        assert data["busityp"] == "10"

    def test_no_price_returns_null(self, app: Flask, client: FlaskClient) -> None:
        """无价格记录 → price=null。"""
        with app.app_context():
            _seed_customer()
            db.session.commit()

        resp = client.get(
            "/api/v1/itsm/entitlement/price?cust_cd=CUSTV3&itemcd=NOITEM",
            headers=_auth_header(app),
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["price"] is None

    def test_missing_params_returns_400(self, app: Flask, client: FlaskClient) -> None:
        """缺少参数 → 400。"""
        resp = client.get(
            "/api/v1/itsm/entitlement/price?cust_cd=CUSTV3",
            headers=_auth_header(app),
        )
        assert resp.status_code == 400
