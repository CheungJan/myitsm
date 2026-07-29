"""Entitlement CRUD API 测试。"""

from __future__ import annotations

from datetime import date, timedelta

from flask import Flask
from flask.testing import FlaskClient

from app.extensions import db
from app.models.entitlement import ServiceContract, SpecialAgreement


class TestSpecialAgreementApi:
    """特殊客户协议 API。"""

    def test_list(
        self, app: Flask, client: FlaskClient, auth_header: dict[str, str]
    ) -> None:
        with app.app_context():
            db.session.query(SpecialAgreement).delete()
            db.session.add(SpecialAgreement(
                agreement_id="AGL001",
                cust_cd="CUSTAPI001",
                agreement_nm="API测试协议",
                is_free="1",
                effective_date=date.today() - timedelta(days=5),
                expire_date=date.today() + timedelta(days=5),
                useflg="1",
            ))
            db.session.commit()

        resp = client.get(
            "/api/v1/entitlement/special-agreements", headers=auth_header
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert any(a["agreement_id"] == "AGL001" for a in data)

    def test_create(
        self, app: Flask, client: FlaskClient, auth_header: dict[str, str]
    ) -> None:
        with app.app_context():
            db.session.query(SpecialAgreement).delete()
            db.session.commit()

        resp = client.post(
            "/api/v1/entitlement/special-agreements",
            json={
                "agreement_id": "AGC001",
                "cust_cd": "CUSTAPI002",
                "agreement_nm": "新建协议",
                "is_free": "1",
                "effective_date": str(date.today()),
                "expire_date": str(date.today() + timedelta(days=30)),
                "useflg": "1",
            },
            headers=auth_header,
        )
        assert resp.status_code == 201
        data = resp.get_json()["data"]
        assert data["agreement_id"] == "AGC001"
        assert data["creator"] == "T00001"

    def test_update(
        self, app: Flask, client: FlaskClient, auth_header: dict[str, str]
    ) -> None:
        with app.app_context():
            db.session.query(SpecialAgreement).delete()
            db.session.add(SpecialAgreement(
                agreement_id="AGU001",
                cust_cd="CUSTAPI003",
                agreement_nm="待更新",
                is_free="1",
                effective_date=date.today(),
                useflg="1",
            ))
            db.session.commit()

        resp = client.put(
            "/api/v1/entitlement/special-agreements/AGU001",
            json={"agreement_nm": "已更新", "is_free": "0"},
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["agreement_nm"] == "已更新"
        assert data["is_free"] == "0"


class TestServiceContractApi:
    """维保合同 API。"""

    def test_list(
        self, app: Flask, client: FlaskClient, auth_header: dict[str, str]
    ) -> None:
        with app.app_context():
            db.session.query(ServiceContract).delete()
            db.session.add(ServiceContract(
                contract_id="CTL001",
                contract_no="HT2026API001",
                cust_cd="CUSTAPI004",
                eid="EIDAPI001",
                contract_nm="API测试合同",
                is_free="1",
                effective_date=date.today() - timedelta(days=5),
                expire_date=date.today() + timedelta(days=5),
                useflg="1",
            ))
            db.session.commit()

        resp = client.get(
            "/api/v1/entitlement/service-contracts", headers=auth_header
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert any(c["contract_id"] == "CTL001" for c in data)

    def test_create(
        self, app: Flask, client: FlaskClient, auth_header: dict[str, str]
    ) -> None:
        with app.app_context():
            db.session.query(ServiceContract).delete()
            db.session.commit()

        resp = client.post(
            "/api/v1/entitlement/service-contracts",
            json={
                "contract_id": "CTC001",
                "contract_no": "HT2026API002",
                "cust_cd": "CUSTAPI005",
                "eid": "EIDAPI002",
                "contract_nm": "新建合同",
                "is_free": "1",
                "effective_date": str(date.today()),
                "expire_date": str(date.today() + timedelta(days=365)),
                "useflg": "1",
            },
            headers=auth_header,
        )
        assert resp.status_code == 201
        data = resp.get_json()["data"]
        assert data["contract_id"] == "CTC001"

    def test_update(
        self, app: Flask, client: FlaskClient, auth_header: dict[str, str]
    ) -> None:
        with app.app_context():
            db.session.query(ServiceContract).delete()
            db.session.add(ServiceContract(
                contract_id="CTU001",
                cust_cd="CUSTAPI006",
                eid="EIDAPI003",
                contract_nm="待更新合同",
                is_free="1",
                effective_date=date.today(),
                expire_date=date.today() + timedelta(days=30),
                useflg="1",
            ))
            db.session.commit()

        resp = client.put(
            "/api/v1/entitlement/service-contracts/CTU001",
            json={"contract_nm": "已更新合同", "is_free": "0"},
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["contract_nm"] == "已更新合同"
        assert data["is_free"] == "0"
