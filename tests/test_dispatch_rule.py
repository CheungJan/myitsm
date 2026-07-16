"""派单规则引擎 + 派工通知联动测试。"""

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


class TestDispatchRule:
    """派单规则引擎测试。"""

    def test_resolve_area_manager(self, app: Flask) -> None:
        """默认规则命中 area_manager：门店→区域→区域负责人。"""
        from app.extensions import db
        from app.models.itsm import DispatchRule
        from app.models.master import Area, Customer
        from app.models.system import Group
        from app.services.itsm_service import DispatchRuleService

        with app.app_context():
            # 准备区域 + 门店
            area = Area(area_cd="A001", area_nm="测试区域", usercd="T00001", useflg="1")
            db.session.add(area)
            db.session.add(Customer(cust_cd="S0000099", area_cd="A001", cust_nm="测试门店"))
            # 默认规则已由迁移 seed 插入，补一条确保存在
            rule = DispatchRule(
                rule_name="测试默认规则",
                priority=99,
                fault_type=None,
                target_type="area_manager",
                target_value=None,
                fallback_type="group_leader",
                fallback_value="A1",
                ultimate_fallback_type="manual",
                ultimate_fallback_value=None,
                useflg="1",
                creator="SYSTEM",
            )
            db.session.add(rule)
            # A1 组无 leader_cd，兜底应失败 → 命中 manual → 返回 None
            db.session.add(Group(group_cd="A1", group_nm="A1组", useflg="1"))
            db.session.commit()

            target = DispatchRuleService.resolve(fault_type=None, store_id="S0000099")
            assert target is not None
            assert target["accpectd_group"] == "A1"
            assert target["accpectder"] == "T00001"
            db.session.query(DispatchRule).delete()
            db.session.query(Customer).filter(Customer.cust_cd == "S0000099").delete()
            db.session.query(Area).filter(Area.area_cd == "A001").delete()
            db.session.query(Group).filter(Group.group_cd == "A1").delete()
            db.session.commit()

    def test_resolve_group_leader_fallback(self, app: Flask) -> None:
        """area_manager 失败时兜底到 group_leader。"""
        from app.extensions import db
        from app.models.itsm import DispatchRule
        from app.models.master import Area, Customer
        from app.models.system import Group
        from app.services.itsm_service import DispatchRuleService

        with app.app_context():
            # 区域无负责人 → area_manager 失败
            db.session.add(Area(area_cd="A002", area_nm="无负责人区域", usercd=None, useflg="1"))
            db.session.add(Customer(cust_cd="S0000088", area_cd="A002", cust_nm="测试门店2"))
            # 组 A2 有 leader
            db.session.add(Group(group_cd="A2", group_nm="A2组", leader_cd="T00002", useflg="1"))
            db.session.add(
                DispatchRule(
                    rule_name="兜底测试",
                    priority=1,
                    fault_type=None,
                    target_type="area_manager",
                    target_value=None,
                    fallback_type="group_leader",
                    fallback_value="A2",
                    ultimate_fallback_type="manual",
                    ultimate_fallback_value=None,
                    useflg="1",
                    creator="SYSTEM",
                )
            )
            db.session.commit()

            target = DispatchRuleService.resolve(fault_type=None, store_id="S0000088")
            assert target is not None
            assert target["accpectd_group"] == "A2"
            assert target["accpectder"] == "T00002"
            db.session.query(DispatchRule).delete()
            db.session.query(Customer).filter(Customer.cust_cd == "S0000088").delete()
            db.session.query(Area).filter(Area.area_cd == "A002").delete()
            db.session.query(Group).filter(Group.group_cd == "A2").delete()
            db.session.commit()

    def test_resolve_manual_returns_none(self, app: Flask) -> None:
        """规则命中 manual 时返回 None。"""
        from app.extensions import db
        from app.models.itsm import DispatchRule
        from app.services.itsm_service import DispatchRuleService

        with app.app_context():
            db.session.add(
                DispatchRule(
                    rule_name="手动派单",
                    priority=1,
                    fault_type=None,
                    target_type="manual",
                    target_value=None,
                    useflg="1",
                    creator="SYSTEM",
                )
            )
            db.session.commit()
            assert DispatchRuleService.resolve(fault_type=None, store_id="S0000001") is None
            db.session.query(DispatchRule).delete()
            db.session.commit()


class TestDispatchAutoCreateNotification:
    """派工自动创建 + 通知快照联动测试。"""

    def test_auto_create_with_notification(
        self, app: Flask, client: FlaskClient
    ) -> None:
        """维护单创建触发规则引擎派单 + 通知记录创建。"""
        from app.extensions import db
        from app.models.itsm import DispatchRule
        from app.models.master import Area, Customer
        from app.models.notification import Notification

        headers = _auth_header(app)
        with app.app_context():
            # 准备区域负责人 + 门店
            db.session.add(Area(area_cd="A003", area_nm="通知联动区域", usercd="T00001", useflg="1"))
            db.session.add(Customer(cust_cd="S0000077", area_cd="A003", cust_nm="通知联动门店"))
            # 插入 DISPATCH 模板（若迁移未执行则补）
            from app.models.notification import NotificationTemplate

            if db.session.get(NotificationTemplate, "DISPATCH") is None:
                db.session.add(
                    NotificationTemplate(
                        template_id="DISPATCH",
                        template_name="派工通知模板",
                        channel="internal",
                        subject="新派工通知：维护单 {{ maintenance_id }}",
                        body="维护单 {{ maintenance_id }}（门店 {{ store_id }}）已派给 {{ accpectder_name }}",
                        useflg="1",
                        opercd="SYSTEM",
                    )
                )
            db.session.add(
                DispatchRule(
                    rule_name="通知联动规则",
                    priority=1,
                    fault_type=None,
                    target_type="area_manager",
                    target_value=None,
                    fallback_type="manual",
                    fallback_value=None,
                    ultimate_fallback_type="manual",
                    ultimate_fallback_value=None,
                    useflg="1",
                    creator="SYSTEM",
                )
            )
            db.session.commit()

        # 触发维护单创建 → auto_create → 通知
        resp = _post(
            client,
            "/api/v1/itsm/maintenance-daily",
            {"store_id": "S0000077", "short_description": "通知联动测试"},
            headers,
        )
        assert resp.status_code == 201
        mid = resp.get_json()["data"]["maintenance_id"]

        with app.app_context():
            # 验证派工记录 + 通知记录
            from app.models.itsm import MaintenanceDispatch

            dispatch = (
                db.session.query(MaintenanceDispatch)
                .filter(MaintenanceDispatch.maintenance_id == mid)
                .first()
            )
            assert dispatch is not None
            assert dispatch.accpectder == "T00001"
            notify = (
                db.session.query(Notification)
                .filter(Notification.ref_type == "dispatch", Notification.ref_id == mid)
                .first()
            )
            assert notify is not None
            assert notify.send_status == "pending"
            assert mid in (notify.subject or "")
            # 清理
            db.session.query(Notification).filter(Notification.ref_id == mid).delete()
            db.session.query(MaintenanceDispatch).filter(
                MaintenanceDispatch.maintenance_id == mid
            ).delete()
            from app.models.itsm import MaintenanceDaily

            db.session.query(MaintenanceDaily).filter(
                MaintenanceDaily.maintenance_id == mid
            ).delete()
            db.session.query(DispatchRule).delete()
            db.session.query(Customer).filter(Customer.cust_cd == "S0000077").delete()
            db.session.query(Area).filter(Area.area_cd == "A003").delete()
            db.session.commit()
