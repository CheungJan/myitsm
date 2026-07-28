"""系统管理业务服务。"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.extensions import db
from app.models.master import Item
from app.repositories.system_repository import SystemRepository


class SystemService:
    """系统管理 Service。"""

    def __init__(self, repo: SystemRepository | None = None) -> None:
        self._repo = repo or SystemRepository()

    def _fill_dept_nm(self, user_dict: dict[str, Any]) -> dict[str, Any]:
        """补充部门名称。"""
        if not user_dict.get("dept_cd"):
            user_dict["dept_nm"] = ""
            return user_dict
        dept = self._repo.get_department_by_cd(user_dict["dept_cd"])
        user_dict["dept_nm"] = dept.dept_nm if dept else ""
        return user_dict

    def _fill_user_groups(self, user_dict: dict[str, Any]) -> dict[str, Any]:
        """补充用户所属组名称列表。"""
        ug_list = self._repo.get_user_groups(user_dict["user_cd"])
        group_cds = [ug["group_cd"] for ug in ug_list]
        if group_cds:
            all_groups = {g.group_cd: g.group_nm for g in self._repo.get_groups()}
            user_dict["groups"] = [
                {"group_cd": gc, "group_nm": all_groups.get(gc, gc)} for gc in group_cds
            ]
        else:
            user_dict["groups"] = []
        return user_dict

    def list_users(
        self,
        status: str | None = None,
        user_cd: str | None = None,
        user_nm: str | None = None,
        dept_cd: str | None = None,
        useflg: str | None = None,
    ) -> list[dict[str, Any]]:
        """获取用户列表，支持多条件筛选。"""
        users = self._repo.get_users(
            status=status, user_cd=user_cd, user_nm=user_nm, dept_cd=dept_cd, useflg=useflg
        )
        result = [self._fill_dept_nm(u.to_dict()) for u in users]
        return [self._fill_user_groups(d) for d in result]

    def get_user(self, user_cd: str) -> dict[str, Any] | None:
        """获取用户详情。"""
        user = self._repo.get_user_by_cd(user_cd)
        return self._fill_dept_nm(user.to_dict()) if user else None

    def create_user(self, data: dict[str, Any]) -> dict[str, Any]:
        """新增用户，自动哈希密码。"""
        from werkzeug.security import generate_password_hash

        payload = dict(data)
        if payload.get("password"):
            payload["password"] = generate_password_hash(
                payload["password"], method="pbkdf2:sha256"
            )
        return self._repo.create_user(payload).to_dict()

    def update_user(self, user_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """更新用户，可选更新密码。"""
        r = self._repo.get_user_by_cd(user_cd)
        if not r:
            return None
        payload = dict(data)
        if payload.get("password"):
            from werkzeug.security import generate_password_hash

            payload["password"] = generate_password_hash(
                payload["password"], method="pbkdf2:sha256"
            )
        else:
            payload.pop("password", None)
        return self._repo.update_user(r, payload).to_dict()

    def delete_user(self, user_cd: str) -> bool:
        """删除用户。"""
        r = self._repo.get_user_by_cd(user_cd)
        if r:
            self._repo.delete_user(r)
            return True
        return False

    def list_departments(self) -> list[dict[str, Any]]:
        """获取部门列表。"""
        depts = self._repo.get_departments()
        return [d.to_dict() for d in depts]

    def create_department(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._repo.create_department(data).to_dict()

    def update_department(self, dept_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        r = self._repo.get_department_by_cd(dept_cd)
        return self._repo.update_department(r, data).to_dict() if r else None

    def delete_department(self, dept_cd: str) -> bool:
        r = self._repo.get_department_by_cd(dept_cd)
        if r:
            self._repo.delete_department(r)
            return True
        return False

    def list_groups(self) -> list[dict[str, Any]]:
        """获取用户组列表（含组长姓名）。"""
        from app.models.system import User

        groups = self._repo.get_groups()
        leader_cds = [g.leader_cd for g in groups if g.leader_cd]
        leader_map: dict[str, str] = {}
        if leader_cds:
            rows = (
                db.session.query(User.user_cd, User.user_nm)
                .filter(User.user_cd.in_(leader_cds))
                .all()
            )
            leader_map = {r.user_cd: r.user_nm for r in rows}
        result: list[dict[str, Any]] = []
        for grp in groups:
            d = grp.to_dict()
            d["leader_nm"] = leader_map.get(grp.leader_cd, "") if grp.leader_cd else ""
            result.append(d)
        return result

    def create_group(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._repo.create_group(data).to_dict()

    def update_group(self, group_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        r = self._repo.get_group_by_cd(group_cd)
        return self._repo.update_group(r, data).to_dict() if r else None

    def delete_group(self, group_cd: str) -> bool:
        r = self._repo.get_group_by_cd(group_cd)
        if r:
            self._repo.delete_group(r)
            return True
        return False

    def get_group_members(self, group_cd: str, active_only: bool = False) -> list[dict[str, Any]]:
        return self._repo.get_group_members(group_cd, active_only=active_only)

    def add_group_member(self, user_cd: str, group_cd: str) -> bool:
        try:
            self._repo.add_group_member(user_cd, group_cd)
            return True
        except Exception:
            return False

    def remove_group_member(self, user_cd: str, group_cd: str) -> bool:
        return self._repo.remove_group_member(user_cd, group_cd)

    # ——— 权限管理 ———

    def get_group_rights(self, group_cd: str) -> list[dict[str, str]]:
        return self._repo.get_group_rights(group_cd)

    def set_group_rights(self, group_cd: str, rights: list[dict[str, str]]) -> None:
        self._repo.set_group_rights(group_cd, rights)

    def get_user_permissions(self, user_cd: str) -> list[dict[str, str]]:
        return self._repo.get_user_permissions(user_cd)

    def get_user_groups(self, user_cd: str) -> list[dict[str, Any]]:
        """获取用户所属用户组。"""
        return self._repo.get_user_groups(user_cd)

    def list_menus(self) -> list[dict[str, Any]]:
        """获取菜单列表。"""
        menus = self._repo.get_menus()
        return [m.to_dict() for m in menus]

    def get_perm_tree(self) -> list[dict[str, Any]]:
        """获取权限树（从数据库动态读取菜单+功能定义）。"""
        return self._repo.get_perm_tree()

    def list_sysparms(self) -> list[dict[str, Any]]:
        """获取系统参数列表。"""
        parms = self._repo.get_sysparms()
        return [p.to_dict() for p in parms]

    def get_sysparm(self, parm_cd: str) -> dict[str, Any] | None:
        """获取指定系统参数。"""
        parm = self._repo.get_sysparm_by_cd(parm_cd)
        return parm.to_dict() if parm else None

    def update_sysparm(self, parm_cd: str, data: dict[str, Any]) -> dict[str, Any]:
        """更新或创建系统参数。"""
        r = self._repo.update_sysparm(parm_cd, data)
        return r.to_dict()

    # ——— 物料分类 ———

    def list_item_classes(self) -> list[dict[str, Any]]:
        """获取所有物料分类（扁平列表）。"""
        classes = self._repo.get_item_classes()
        return [c.to_dict() for c in classes]

    def get_item_class_tree(self) -> list[dict[str, Any]]:
        """获取物料分类树。"""
        return self._repo.get_item_class_tree()

    def get_bom_class_tree(self, typflg: str = "1") -> list[dict[str, Any]]:
        """获取分类树（按 typflg 过滤，默认只含成品）。"""
        return self._repo.get_bom_class_tree(typflg)

    def get_item_suppliers(self, item_cd: str) -> list[dict[str, Any]]:
        """查询物料关联的供应商列表。"""
        return self._repo.get_item_suppliers(item_cd)

    def get_item_prices(self, item_cd: str) -> list[dict[str, Any]]:
        """查询物料关联的价格记录。"""
        return self._repo.get_item_prices(item_cd)

    def add_item_price(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._repo.add_item_price(data).to_dict()

    def update_item_price(
        self, item_cd: str, busityp: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        r = self._repo.get_item_price(item_cd, busityp)
        if not r:
            return None
        # busityp 是复合主键，如果请求改了 busityp → 删旧建新
        if "busityp" in data and data["busityp"] != busityp:
            new_busityp = data.pop("busityp")
            existing = self._repo.get_item_price(item_cd, new_busityp)
            if existing:
                return None  # 目标busityp已存在
            self._repo.delete_item_price(r)
            data["itemcd"] = item_cd
            data["busityp"] = new_busityp
            return self._repo.add_item_price(data).to_dict()
        return self._repo.update_item_price(r, data).to_dict()

    def delete_item_price(self, item_cd: str, busityp: str) -> bool:
        r = self._repo.get_item_price(item_cd, busityp)
        return self._repo.delete_item_price(r) if r else False

    def get_related_boms(self, item_cd: str) -> list[dict[str, Any]]:
        """反查包含该物料的 BOM 列表。"""
        return self._repo.get_related_boms(item_cd)

    def add_item_supplier(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._repo.add_item_supplier(data).to_dict()

    def update_item_supplier(
        self, item_cd: str, cust_cd: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        r = self._repo.get_item_supplier(item_cd, cust_cd)
        return self._repo.update_item_supplier(r, data).to_dict() if r else None

    def delete_item_supplier(self, item_cd: str, cust_cd: str) -> bool:
        r = self._repo.get_item_supplier(item_cd, cust_cd)
        return self._repo.delete_item_supplier(r) if r else False

    def list_all_suppliers(self) -> list[dict[str, Any]]:
        return self._repo.list_all_suppliers()

    # ========== Supplier CRUD ==========

    def get_supplier(self, supp_cd: str) -> dict[str, Any] | None:
        obj = self._repo.get_supplier(supp_cd)
        return obj.to_dict() if obj else None

    def list_suppliers(
        self, keyword: str = "", class_cd: str = "", page: int = 1, per_page: int = 20
    ) -> dict[str, Any]:
        return self._repo.list_suppliers_paginated(keyword, class_cd, page, per_page)

    def list_suppliers_all(self) -> list:
        """全量供应商简表，用于下拉选择。"""
        return self._repo.list_suppliers_all()

    def create_supplier(self, data: dict[str, Any]) -> dict[str, Any]:
        supp_cd = data.get("supp_cd", "").strip()
        if supp_cd:
            existing = self._repo.get_supplier(supp_cd)
            if existing:
                raise ValueError(f"供应商编码 {supp_cd} 已存在")
        else:
            max_cd = self._repo.get_max_supp_cd()
            next_num = int(max_cd) + 1 if max_cd else 1
            supp_cd = str(next_num).zfill(8)
            data["supp_cd"] = supp_cd
        if not data.get("supp_nm"):
            raise ValueError("供应商名称不能为空")
        return self._repo.create_supplier(data).to_dict()

    def update_supplier(self, supp_cd: str, data: dict[str, Any]) -> dict[str, Any]:
        obj = self._repo.get_supplier(supp_cd)
        if not obj:
            raise ValueError(f"供应商 {supp_cd} 不存在")
        return self._repo.update_supplier(obj, data).to_dict()

    def delete_supplier(self, supp_cd: str) -> dict[str, Any]:
        obj = self._repo.get_supplier(supp_cd)
        if not obj:
            raise ValueError(f"供应商 {supp_cd} 不存在")
        conflicts = self._check_supplier_delete_conflicts(supp_cd)
        if conflicts:
            raise ValueError(f"该供应商存在以下关联：{'; '.join(conflicts)}，无法删除")
        self._repo.delete_supplier(obj)
        return {"supp_cd": supp_cd, "conflicts": []}

    def _check_supplier_delete_conflicts(self, supp_cd: str) -> list[str]:
        conflicts = []
        if self._repo.count_orders_by_supplier(supp_cd) > 0:
            conflicts.append("采购订单关联")
        if self._repo.count_prices_by_supplier(supp_cd) > 0:
            conflicts.append("供应商价格记录")
        if self._repo.count_custitems_by_supplier(supp_cd) > 0:
            conflicts.append("供应商商品关联")
        if self._repo.count_appraisals_by_supplier(supp_cd) > 0:
            conflicts.append("供应商评价记录")
        return conflicts

    # ========== Supplier Items ==========

    def get_supplier_items(self, supp_cd: str) -> list[dict[str, Any]]:
        """查询供应商关联的商品列表。"""
        return self._repo.get_supplier_items(supp_cd)

    def add_supplier_item(self, supp_cd: str, data: dict[str, Any]) -> dict[str, Any]:
        """新增供应商-商品关联。"""
        item_cd = data.get("itemcd", "")
        if not item_cd:
            raise ValueError("物料编码不能为空")
        if not db.session.query(Item.item_cd).filter(Item.item_cd == item_cd).first():
            raise ValueError(f"物料 {item_cd} 不存在")
        existing = self._repo.get_supplier_item(supp_cd, item_cd)
        if existing:
            raise ValueError(f"物料 {item_cd} 已关联")
        if data.get("dfltflg") == "Y":
            self._repo.set_item_default_supplier(item_cd, supp_cd)
        return self._repo.add_supplier_item(supp_cd, data).to_dict()

    def update_supplier_item(
        self, supp_cd: str, item_cd: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """更新供应商-商品关联。"""
        obj = self._repo.get_supplier_item(supp_cd, item_cd)
        if not obj:
            raise ValueError("关联不存在")
        if data.get("dfltflg") == "Y":
            self._repo.set_item_default_supplier(item_cd, supp_cd)
        updatable = {
            "dfltflg",
            "delivercycle",
            "servicecycle",
            "guaranteeperiod",
            "backup",
            "useflg",
        }
        for k, v in data.items():
            if k in updatable and hasattr(obj, k):
                setattr(obj, k, v)
        db.session.commit()
        return obj.to_dict()

    def delete_supplier_item(self, supp_cd: str, item_cd: str) -> None:
        """删除供应商-商品关联。"""
        obj = self._repo.get_supplier_item(supp_cd, item_cd)
        if not obj:
            raise ValueError("关联不存在")
        if self._repo.check_supplier_item_has_orders(supp_cd, item_cd):
            raise ValueError("该商品关联存在采购订单，无法删除")
        self._repo.delete_supplier_item(obj)

    # ========== Supplier Prices ==========

    def get_supplier_prices(
        self, supp_cd: str, item_cd: str = "", current_only: bool = False
    ) -> list[dict[str, Any]]:
        return self._repo.get_supplier_prices(supp_cd, item_cd, current_only)

    def _validate_supplier_price(self, item_cd: str, price: float | Decimal) -> str | None:
        """校验供应商报价是否低于标准采购价的 80%。返回警告文本或 None。"""
        std = self._repo.get_item_standard_price(item_cd, busityp="20")
        if not std or not std.itemprice:
            return None
        threshold = Decimal("0.8")
        if Decimal(str(price)) < std.itemprice * threshold:
            return f"报价 {price} 低于物料标准采购价 {float(std.itemprice)} 的 80%，是否确认保存？"
        return None

    def create_supplier_price(
        self, supp_cd: str, data: dict[str, Any], force: bool = False
    ) -> dict[str, Any]:
        item_cd = data.get("itemcd", "")
        if not item_cd:
            raise ValueError("物料编码不能为空")
        if not self._repo.check_custitems_exists(supp_cd, item_cd):
            raise ValueError("该供应商未关联此商品，请先维护供应商品关系")
        # 日期清理：空字符串转为 None
        for field in ("effective_date", "expire_date"):
            if data.get(field) == "" or data.get(field) == None:
                data[field] = None
        if not data.get("effective_date"):
            raise ValueError("生效日期不能为空")
        if not force:
            warning = self._validate_supplier_price(item_cd, data.get("itemprice", 0))
            if warning:
                return {"warning": warning, "requires_confirmation": True}
        data["supp_cd"] = supp_cd
        return self._repo.create_supplier_price(data).to_dict()

    def update_supplier_price(self, price_id: int, data: dict[str, Any]) -> dict[str, Any]:
        obj = self._repo.get_supplier_price(price_id)
        if not obj:
            raise ValueError("报价记录不存在")
        # 日期清理：空字符串转为 None
        for field in ("effective_date", "expire_date"):
            if field in data and (data[field] == "" or data[field] == None):
                data[field] = None
        return self._repo.update_supplier_price(obj, data).to_dict()

    def delete_supplier_price(self, price_id: int) -> None:
        obj = self._repo.get_supplier_price(price_id)
        if not obj:
            raise ValueError("报价记录不存在")
        self._repo.delete_supplier_price(obj)

    # ========== 价格解析 ==========

    def resolve_price(self, item_cd: str, supp_cd: str, qty: float = 1) -> dict[str, Any]:
        """按优先级解析最优价格，供采购订单自动取价。

        优先级：
        1. 供应商当前有效报价（满足起订量，取最低价）
        2. 物料标准采购价（TIP01 busityp='20'）
        3. 无可用价格，返回空由用户手动填写
        """
        # 1. 供应商报价
        sp = self._repo.get_supplier_price_current(item_cd, supp_cd, qty)
        if sp:
            return {
                "price": float(sp.itemprice) if sp.itemprice else None,
                "source": "supplier",
                "source_name": "供应商报价",
                "effective_date": sp.effective_date.isoformat() if sp.effective_date else None,
                "expire_date": sp.expire_date.isoformat() if sp.expire_date else None,
                "min_qty": float(sp.min_qty) if sp.min_qty else 0,
            }

        # 2. 物料标准采购价
        std = self._repo.get_item_standard_price(item_cd, busityp="20")
        if std and std.itemprice:
            return {
                "price": float(std.itemprice),
                "source": "standard",
                "source_name": "标准采购价",
                "effective_date": std.effective_date.isoformat() if std.effective_date else None,
                "expire_date": std.expire_date.isoformat() if std.expire_date else None,
                "min_qty": 0,
            }

        # 3. 无可用价格
        return {"price": None, "source": "manual", "source_name": "手动填写", "min_qty": 0}

    def create_item_class(self, data: dict[str, Any]) -> dict[str, Any]:
        """新增物料分类。"""
        parent = (data.get("parent_cd") or "").strip()
        if parent and parent == data["class_cd"]:
            raise ValueError("父分类不能指向自己")
        return self._repo.create_item_class(data).to_dict()

    def update_item_class(self, class_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """更新物料分类。"""
        parent = (data.get("parent_cd") or "").strip()
        if parent and parent == class_cd:
            raise ValueError("父分类不能指向自己")
        r = self._repo.get_item_class_by_cd(class_cd)
        return self._repo.update_item_class(r, data).to_dict() if r else None

    def delete_item_class(self, class_cd: str) -> bool:
        """删除物料分类（有子分类则拒绝）。"""
        r = self._repo.get_item_class_by_cd(class_cd)
        if not r:
            return False
        children = [
            c
            for c in self._repo.get_item_classes()
            if c.parent_cd and c.parent_cd.strip() == class_cd
        ]
        if children:
            child_cds = [c.class_cd for c in children]
            raise ValueError(
                f"该分类下有 {len(children)} 个子分类，请先删除子分类: {', '.join(child_cds[:5])}{'...' if len(child_cds) > 5 else ''}"
            )
        self._repo.delete_item_class(r)
        return True

    # ——— 基础数据 ———

    def list_items(
        self,
        page: int = 1,
        per_page: int = 20,
        class_cd: str | None = None,
        recursive: bool = True,
        search: str | None = None,
        typflg: str | None = None,
    ) -> dict[str, Any]:
        """获取物料列表，支持分类筛选、递归子分类、搜索、成品/配件过滤。"""
        items, total = self._repo.get_items(
            page=page,
            per_page=per_page,
            class_cd=class_cd,
            recursive=recursive,
            search=search,
            typflg=typflg,
        )
        return {"items": [i.to_dict() for i in items], "total": total}

    def list_pos_models(self) -> list[dict[str, Any]]:
        """获取在产机型列表(整机成品 JOIN Bom useflg=1)。

        对齐 PB 语义:Bom.useflg='1' 表示配方有效即机型在产可选。
        返回字段:item_cd, item_nm, rent_money(busityp=40), sale_money(busityp=10)。
        """
        return self._repo.get_pos_models()

    # ——— 客户分类 ———

    def list_cust_classes(self) -> list[dict[str, Any]]:
        """获取所有客户分类（扁平列表）。"""
        classes = self._repo.get_cust_classes()
        return [c.to_dict() for c in classes]

    def get_cust_class_tree(self) -> list[dict[str, Any]]:
        """获取客户分类树。"""
        return self._repo.get_cust_class_tree()

    def create_cust_class(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._repo.create_cust_class(data).to_dict()

    def update_cust_class(self, class_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        r = self._repo.get_cust_class_by_cd(class_cd)
        return self._repo.update_cust_class(r, data).to_dict() if r else None

    def delete_cust_class(self, class_cd: str) -> bool:
        """删除客户分类（有子分类或有客户则拒绝）。"""
        r = self._repo.get_cust_class_by_cd(class_cd)
        if not r:
            return False
        # 检查子分类
        children = [
            c
            for c in self._repo.get_cust_classes()
            if c.parent_cd and c.parent_cd.strip() == class_cd
        ]
        if children:
            child_cds = [c.class_cd for c in children]
            raise ValueError(
                f"该分类下有 {len(children)} 个子分类，请先删除子分类: {', '.join(child_cds[:5])}{'...' if len(child_cds) > 5 else ''}"
            )
        # 检查该分类下是否有客户
        _, cust_total = self._repo.get_customers(page=1, per_page=1, class_cd=class_cd)
        if cust_total > 0:
            raise ValueError(f"该分类下有 {cust_total} 个客户，请先将客户移至其他分类或删除后再试")
        self._repo.delete_cust_class(r)
        return True

    # ——— 客户 ———

    def _resolve_customer_refs(self, cust: dict[str, Any]) -> dict[str, Any]:
        """解析客户关联字段为中文名称。"""
        # 懒加载码表缓存（类级别，首次调用后复用）
        # 若缓存中缺少 geo_province 则重建（升级兼容）
        if not hasattr(self.__class__, "_ref_cache") or "geo_province" not in getattr(self.__class__, "_ref_cache", {}):
            self.__class__._ref_cache = self._build_ref_cache()  # type: ignore[attr-defined]
        cache = getattr(self.__class__, "_ref_cache")
        # 客户分类
        cust["class_cd_nm"] = cache.get("custclass", {}).get(cust.get("class_cd", ""), "")
        # 上级客户（parentcd 存的是客户分类编码，去空格）
        parentcd = (cust.get("parentcd") or "").strip()
        cust["parentcd_nm"] = cache.get("custclass", {}).get(parentcd, "") if parentcd else ""
        # 业务类型 BT
        cust["busi_typ_nm"] = cache["bt"].get(cust.get("busi_typ", ""), "")
        # 门店属性 YB
        cust["ppt_code_nm"] = cache["yb"].get(cust.get("ppt_code", ""), "")
        # 所属云类别 PY
        cust["yun_type_nm"] = cache["py"].get(cust.get("yun_type", ""), "")
        # 支付方式 ZF
        cust["zf_type_nm"] = cache["zf"].get(cust.get("zf_type", ""), "")
        # 通讯方式（tmm31_syscodes code_typ='CM'）
        cust["comm_mode_nm"] = cache["cm"].get(cust.get("comm_mode", ""), "")
        # 负责区域：兼容 area_cd（新）和 area_id（旧数据）
        _area_val = str(cust.get("area") or "")
        cust["area_nm"] = cache["area"].get(_area_val, "") or cache["area_by_id"].get(_area_val, "")
        # 环线位置（WZ 系统字典）
        cust["location_nm"] = cache["wz"].get(cust.get("location", ""), "")
        # POS 状态（posstatus1 是子码，无独立中文名）
        cust["posstatus_nm"] = cache.get("ps", {}).get(cust.get("posstatus", ""), "")
        # 设备状态
        cust["s_status_nm"] = cache.get("ss", {}).get(cust.get("s_status", ""), "")
        # POS 数量 = 有效设备数
        cust["pos_count"] = self._repo.get_cust_pos_count(cust["cust_cd"])
        # 最新机型名称（对齐 PB uf_storeposinfo，取有效设备中最新日期对应 ITEMNM）
        cust["latest_item_nm"] = self._repo.get_cust_latest_itemnm(cust["cust_cd"])
        # 生命周期状态
        cust["customer_status_nm"] = cache.get("cs", {}).get(cust.get("customer_status", ""), "")
        cust["source_type_nm"] = cache.get("src", {}).get(cust.get("source_type", ""), "")
        # 行政区域（老字段）
        cust["country_nm"] = cache.get("country", {}).get(cust.get("country_cd", ""), "")
        cust["prvn_nm"] = cache.get("province", {}).get(cust.get("prvn_cd", ""), "")
        cust["city_nm"] = cache.get("city", {}).get(cust.get("city_cd", ""), "")
        cust["town_nm"] = cache.get("town", {}).get(cust.get("town_cd", ""), "")
        # 国标地理字段名称解析
        cust["geo_prvn_nm"] = cache.get("geo_province", {}).get(cust.get("geo_prvn_cd", "") or "", "")
        cust["geo_city_nm"] = cache.get("geo_city", {}).get(cust.get("geo_city_cd", "") or "", "")
        cust["geo_area_nm"] = cache.get("geo_area", {}).get(cust.get("geo_area_cd", "") or "", "")
        # 街道数据量大，按需查询
        street_cd = cust.get("geo_street_cd") or ""
        if street_cd:
            from app.models.master import GeoStreet
            s = db.session.get(GeoStreet, street_cd)
            cust["geo_street_nm"] = s.name if s else ""
        else:
            cust["geo_street_nm"] = ""
        return cust

    @staticmethod
    def _build_ref_cache() -> dict[str, dict[str, str]]:
        """构建码表查找缓存。"""
        repo = SystemRepository()
        cache: dict[str, dict[str, str]] = {"bt": {}, "yb": {}, "zf": {}, "cm": {}, "area": {}, "area_by_id": {}, "wz": {}, "py": {}}
        for s in repo.get_syscodes("BT"):
            cache["bt"][s.code_cd] = s.code_nm or ""
        for s in repo.get_syscodes("YB"):
            cache["yb"][s.code_cd] = s.code_nm or ""
        for s in repo.get_syscodes("PY"):
            cache["py"][s.code_cd] = s.code_nm or ""
        for s in repo.get_syscodes("ZF"):
            cache["zf"][s.code_cd] = s.code_nm or ""
        for s in repo.get_syscodes("PS"):
            cache["ps"] = cache.get("ps", {})
            cache["ps"][s.code_cd] = s.code_nm or ""
        for s in repo.get_syscodes("SS"):
            cache["ss"] = cache.get("ss", {})
            cache["ss"][s.code_cd] = s.code_nm or ""
        for s in repo.get_syscodes("CS"):
            cache["cs"] = cache.get("cs", {})
            cache["cs"][s.code_cd] = s.code_nm or ""
        for s in repo.get_syscodes("SRC"):
            cache["src"] = cache.get("src", {})
            cache["src"][s.code_cd] = s.code_nm or ""
        for cc in repo.get_cust_classes():
            cache["custclass"] = cache.get("custclass", {})
            cache["custclass"][cc.class_cd] = cc.class_nm or ""
        for c in repo.get_syscodes("CM"):
            cache["cm"][c.code_cd] = c.code_nm or ""
        for a in repo.get_areas():
            cache["area"][a.area_cd] = a.name or a.area_nm or ""
            cache["area_by_id"][str(a.area_id)] = a.name or a.area_nm or ""
        for s in repo.get_syscodes("WZ"):
            cache["wz"][s.code_cd] = s.code_nm or ""
        for c in repo.get_countries():
            cache["country"] = cache.get("country", {})
            cache["country"][c.country_cd] = c.country_nm or ""
        for p in repo.get_provinces():
            cache["province"] = cache.get("province", {})
            cache["province"][p.prvn_cd] = p.prvn_nm or ""
        for c in repo.get_cities():
            cache["city"] = cache.get("city", {})
            cache["city"][c.city_cd] = c.city_nm or ""
        for t in repo.get_towns():
            cache["town"] = cache.get("town", {})
            cache["town"][t.town_cd] = t.town_nm or ""
        # 国标地理码表
        for p in repo.get_geo_provinces():
            cache["geo_province"] = cache.get("geo_province", {})
            cache["geo_province"][p.code] = p.name or ""
        for c in repo.get_geo_cities():
            cache["geo_city"] = cache.get("geo_city", {})
            cache["geo_city"][c.code] = c.name or ""
        for a in repo.get_geo_areas():
            cache["geo_area"] = cache.get("geo_area", {})
            cache["geo_area"][a.code] = a.name or ""
        # 街道数据量4万条，不全量缓存，按需查询
        return cache

    def list_customers(
        self,
        page: int = 1,
        per_page: int = 20,
        class_cd: str | None = None,
        search: str | None = None,
        customer_status: str | None = None,
        useflg: str | None = None,
    ) -> dict[str, Any]:
        items, total = self._repo.get_customers(
            page=page, per_page=per_page, class_cd=class_cd, search=search,
            customer_status=customer_status, useflg=useflg,
        )
        resolved = [self._resolve_customer_refs(c.to_dict()) for c in items]
        return {"items": resolved, "total": total}

    def list_yx_companies(self) -> list[dict[str, Any]]:
        """有限公司下拉数据（tmm22.class_cd 关联 tmm21_custclass.class_nm）。

        返回 [{class_cd, class_nm}, ...]，按 class_cd 排序。
        """
        from app.extensions import db
        from app.models.master import Customer, CustClass

        rows = (
            db.session.query(Customer.class_cd, CustClass.class_nm)
            .join(CustClass, Customer.class_cd == CustClass.class_cd)
            .filter(Customer.useflg == "1", Customer.class_cd.isnot(None))
            .distinct()
            .order_by(Customer.class_cd)
            .all()
        )
        return [{"class_cd": r[0], "class_nm": r[1]} for r in rows]

    def get_customer(self, cust_cd: str) -> dict[str, Any] | None:
        """获取客户详情，含中文解析。"""
        r = self._repo.get_customer(cust_cd)
        return self._resolve_customer_refs(r.to_dict()) if r else None

    def get_customer_assets(
        self,
        cust_cd: str,
        page: int = 1,
        per_page: int = 100,
        useflg: str = "1",
    ) -> dict[str, Any]:
        """获取门店在网资产列表。"""
        return self.list_assets(
            page=page,
            per_page=per_page,
            cust_cd=cust_cd,
            useflg=useflg,
        )

    # ——— EID ———

    def get_eid_itemcd_tree(self) -> list[dict[str, Any]]:
        """获取物料分类树（含 EID 数量）。"""
        return self._repo.get_eid_itemcd_tree()

    def list_eid(
        self,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        class_cd: str | None = None,
        whcd: str | None = None,
    ) -> dict[str, Any]:
        items, total = self._repo.get_eid_list(
            page=page, per_page=per_page, search=search, class_cd=class_cd, whcd=whcd
        )
        # 解析物料名称 + 仓库名称
        item_map: dict[str, str] = {}
        wh_map: dict[str, str] = {}
        from app.models.warehouse import Warehouse

        for e in items:
            if e.itemcd and e.itemcd not in item_map:
                item = self._repo.get_item(e.itemcd)
                item_map[e.itemcd] = item.item_nm if item else ""
            if e.whcd and e.whcd not in wh_map:
                wh = db.session.get(Warehouse, e.whcd)
                wh_map[e.whcd] = wh.whnm if wh else ""
        # 关联单号（3级优先级：翻新单 → C记录(时间校验) → 空）
        plan_map: dict[str, str] = {}
        if items:
            eids = [e.eid for e in items]

            # 1. 优先：翻新单 tit15_maintenance_renovate（按 new_device_id 匹配）
            renovate_rows = db.session.execute(
                db.text("""
                    SELECT new_device_id, renew_id FROM tit15_maintenance_renovate
                    WHERE new_device_id = ANY(:eids)
                """),
                {"eids": eids},
            ).fetchall()
            for new_device_id, renew_id in renovate_rows:
                plan_map[new_device_id] = renew_id

            # 2. 其次：C 记录（refid 非空 且 change_date >= 设备生产日期）
            gendate_map = {e.eid: e.gendate for e in items if e.gendate}
            from app.models.master import EidTrack

            tracks = (
                db.session.query(EidTrack.eid, EidTrack.refid, EidTrack.change_date)
                .filter(
                    EidTrack.eid.in_(eids),
                    EidTrack.type == "C",
                    EidTrack.refid != "",
                )
                .order_by(EidTrack.change_date.desc())
                .all()
            )
            for t in tracks:
                if t.eid not in plan_map:  # 翻新单已匹配则跳过
                    gd = gendate_map.get(t.eid)
                    if gd and t.change_date and t.change_date >= gd:
                        plan_map[t.eid] = t.refid

        result = []
        for e in items:
            d = e.to_dict()
            d["item_nm"] = item_map.get(e.itemcd, "")
            d["wh_nm"] = wh_map.get(e.whcd, "")
            d["plan_refid"] = plan_map.get(e.eid, "")
            result.append(d)
        return {"items": result, "total": total}

    def list_assets(
        self,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        class_cd: str | None = None,
        asset_type: str | None = None,
        asset_owner: str | None = None,
        useflg: str | None = None,
        location: str | None = None,
        whcd: str | None = None,
        sflg: str | None = None,
        cust_cd: str | None = None,
        item_class: str | None = None,
    ) -> dict[str, Any]:
        items, total = self._repo.get_cust_pos_rl(
            page=page,
            per_page=per_page,
            search=search,
            class_cd=class_cd,
            asset_type=asset_type,
            asset_owner=asset_owner,
            useflg=useflg,
            location=location,
            whcd=whcd,
            sflg=sflg,
            cust_cd=cust_cd,
            item_class=item_class,
        )
        return {"items": items, "total": total}

    def get_asset(self, asset_id: int) -> dict[str, Any] | None:
        """获取单个资产记录（CustPosRl）。"""
        r = self._repo.get_cust_pos_rl_by_id(asset_id)
        return r.to_dict() if r else None

    # ——— CRUD ———

    def create_item(self, data: dict[str, Any]) -> dict[str, Any]:
        item_cd = data.get("item_cd", "")
        if item_cd:
            self._validate_item_cd(item_cd)
        return self._repo.create_item(data).to_dict()

    def update_item(self, item_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        r = self._repo.get_item(item_cd)
        if not r:
            return None
        new_cd = data.get("item_cd", "")
        if new_cd and new_cd != item_cd:
            # 检查新编码是否与分类编码冲突
            self._validate_item_cd(new_cd)
        result = self._repo.update_item(r, data).to_dict()
        if new_cd and new_cd != item_cd:
            # 告知调用方受影响的引用记录数（FK CASCADE 已自动同步）
            affected = self._get_item_ref_counts(item_cd)
            if affected:
                result["_affected_refs"] = affected
        return result

    @staticmethod
    def _validate_item_cd(item_cd: str) -> None:
        """检查物料编码是否与物料分类编码冲突。"""
        from app.models.master import ItemClass

        if db.session.get(ItemClass, item_cd):
            raise ValueError(f"编码 {item_cd} 已被物料分类占用，请使用其他编码")

    @staticmethod
    def _get_item_ref_counts(item_cd: str) -> dict[str, int]:
        """查询物料编码被引用的记录数。"""
        from app.models.inventory import SupplierPrice
        from app.models.master import CustItems
        from app.models.procurement import PurchasePlanDt, PurchaseRegisterDt

        result: dict[str, int] = {}
        for model, key in [
            (PurchasePlanDt, "采购需求明细"),
            (PurchaseRegisterDt, "采购订单明细"),
            (CustItems, "供应商商品关联"),
            (SupplierPrice, "供应商报价"),
        ]:
            count = db.session.query(model).filter(model.itemcd == item_cd).count()
            if count:
                result[key] = count
        return result

    def delete_item(self, item_cd: str) -> bool:
        r = self._repo.get_item(item_cd)
        if not r:
            return False
        # 级联删除关联数据
        from app.repositories.bom_repository import BomRepository

        bom = BomRepository.get_bom(item_cd.upper())
        if bom:
            for dt in BomRepository.list_details(item_cd.upper()):
                BomRepository.delete_detail(dt)
            BomRepository.delete_bom(bom)
        self._repo.delete_item(r)
        return True

    def create_customer(self, data: dict[str, Any]) -> dict[str, Any]:
        """新增客户 — 检查所属分类是否有效。"""
        class_cd = data.get("class_cd")
        if class_cd:
            cc = self._repo.get_cust_class_by_cd(class_cd)
            if cc and cc.useflg == "0":
                raise ValueError(f"客户分类 '{class_cd}' 已失效，无法新增客户")
        return self._repo.create_customer(data).to_dict()

    def update_customer(self, cust_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        r = self._repo.get_customer(cust_cd)
        return self._repo.update_customer(r, data).to_dict() if r else None

    def delete_customer(self, cust_cd: str) -> bool:
        r = self._repo.get_customer(cust_cd)
        if r:
            self._repo.delete_customer(r)
            return True
        return False

    def create_eid(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._repo.create_eid(data).to_dict()

    def update_eid(self, itemcd: str, eid_val: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """更新 EID 资产属性，并写 type='A' 属性变更轨迹（11f）。

        业务语义层写 type='A'（属性变更），DB 操作层由 11a 事件监听自动写 type='u'。
        仅当资产属性字段（asset_type/recyclable/recycle_status/asset_owner/install_date 等）
        实际变更时才写 A 记录，记录变更前后值。
        """
        from datetime import UTC
        from datetime import datetime as _dt

        from app.models.master import Eid
        from app.repositories.system_repository import SystemRepository as _Repo
        from app.services.itsm_service import TRACK_TYPE_ATTRIBUTE

        # 资产属性字段白名单（对齐 eid_listeners._TRACKED_FIELDS 资产扩展部分）
        asset_fields: tuple[str, ...] = (
            "asset_type",
            "recyclable",
            "recycle_status",
            "asset_owner",
            "install_date",
            "etyp",
            "sflg",
            "refid",
            "qcflg",
            "whcd",
            "prddate",
            "itemtyp",
            "remark",
            "manuf_seq",
            "old_degree",
        )

        # 取变更前快照
        before = db.session.get(Eid, (itemcd, eid_val))
        if before is None:
            return None

        old_vals: dict[str, Any] = {f: getattr(before, f, None) for f in asset_fields}

        # 执行更新
        updated = self._repo.update_eid(itemcd, eid_val, data)
        if updated is None:
            return None

        # 比对变更，构造新旧值字典
        changes: dict[str, tuple[Any, Any]] = {}
        for f in asset_fields:
            old_v = old_vals.get(f)
            new_v = getattr(updated, f, None)
            if old_v != new_v:
                changes[f] = (old_v, new_v)

        if not changes:
            return updated.to_dict()

        # 写 type='A' 属性变更轨迹
        operator = data.get("opercd", "") or ""
        remark_parts: list[str] = [f"{f}: {changes[f][0]}→{changes[f][1]}" for f in changes]
        _Repo.create_eid_track(
            eid=eid_val,
            itemcd=itemcd,
            track_type=TRACK_TYPE_ATTRIBUTE,
            operator=operator,
            refid="",
            change_date=_dt.now(UTC),
            sflg=old_vals.get("sflg"),
            n_sflg=getattr(updated, "sflg", None),
            whcd=old_vals.get("whcd"),
            n_whcd=getattr(updated, "whcd", None),
            install_date=old_vals.get("install_date"),
            n_install_date=getattr(updated, "install_date", None),
            remark="属性变更：" + "; ".join(remark_parts),
        )
        db.session.commit()
        return updated.to_dict()

    def delete_eid(self, itemcd: str, eid_val: str) -> bool:
        return self._repo.delete_eid(itemcd, eid_val)

    def get_warehouses(self) -> list[dict[str, Any]]:
        return self._repo.get_warehouses()

    def create_warehouse(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._repo.create_warehouse(data).to_dict()

    def update_warehouse(self, whcd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        r = self._repo.get_warehouse(whcd)
        return self._repo.update_warehouse(r, data).to_dict() if r else None

    def delete_warehouse(self, whcd: str) -> bool:
        r = self._repo.get_warehouse(whcd)
        if r:
            self._repo.delete_warehouse(r)
            return True
        return False

    def get_eid_tracks(self, itemcd: str, eid: str) -> list[dict[str, Any]]:
        tracks = self._repo.get_eid_tracks(itemcd, eid)
        eid_record = self._repo.get_eid(itemcd, eid)
        gendate = eid_record.gendate if eid_record else None

        # 翻新单（用于校验 C 记录 refid）
        reno_refid: str | None = None
        if eid_record:
            row = db.session.execute(
                db.text(
                    "SELECT renew_id FROM tit15_maintenance_renovate WHERE new_device_id = :eid"
                ),
                {"eid": eid},
            ).fetchone()
            if row:
                reno_refid = row[0]

        from app.models.master import Customer
        from app.models.warehouse import Warehouse

        wh_map: dict[str, str] = {}
        cust_map: dict[str, str] = {}
        result = []
        for t in tracks:
            d = t.to_dict()
            for wh_field in ["whcd", "n_whcd"]:
                whcd = d.get(wh_field)
                if whcd and whcd not in wh_map:
                    wh = db.session.get(Warehouse, whcd)
                    wh_map[whcd] = wh.whnm if wh else ""
                key = "wh_nm" if wh_field == "whcd" else "n_wh_nm"
                d[key] = wh_map.get(whcd, "")
            for cust_field in ["cust_cd", "n_cust_cd"]:
                cd = d.get(cust_field)
                if cd and cd not in cust_map:
                    c = db.session.get(Customer, cd)
                    cust_map[cd] = c.cust_card if c else ""
                d[cust_field + "_card"] = cust_map.get(cd, "")

            # C 记录校验：change_date 不得早于设备生产日期，refid 优先用翻新单
            if t.type == "C" and gendate and t.change_date:
                if t.change_date < gendate:
                    # 从 CustPosRl 取正确的安装日期
                    pos_row = db.session.execute(
                        db.text("SELECT posupddate FROM tmm35_cust_pos_rl WHERE eid = :eid"),
                        {"eid": eid},
                    ).fetchone()
                    if pos_row and pos_row[0]:
                        d["change_date"] = pos_row[0].isoformat()
                if reno_refid and t.refid != reno_refid:
                    d["refid"] = reno_refid
                    d["_refid_corrected"] = True
            result.append(d)
        # 纠正后重新按时间排序（change_date 可能在上面被修正过）
        result.sort(key=lambda d: (d.get("change_date") or "", d.get("seqno") or 0))
        return result

    # ——— 码表查询 ———

    def get_syscodes(self, code_typ: str) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._repo.get_syscodes(code_typ)]

    def get_all_syscodes(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._repo.get_all_syscodes()]

    def create_syscode(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._repo.create_syscode(data).to_dict()

    def update_syscode(self, code_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        r = self._repo.get_syscode_by_id(code_id)
        return self._repo.update_syscode(r, data).to_dict() if r else None

    def delete_syscode(self, code_id: int) -> bool:
        r = self._repo.get_syscode_by_id(code_id)
        if r:
            self._repo.delete_syscode(r)
            return True
        return False

    def get_areas(self) -> list[dict[str, Any]]:
        """区域列表，enrichment 翻译 usercd → usercd_nm。"""
        items = [a.to_dict() for a in self._repo.get_areas()]
        return self._enrich_area_user_names(items)

    def get_area(self, area_cd: str) -> dict[str, Any] | None:
        record = self._repo.get_area_by_cd(area_cd)
        if record is None:
            return None
        items = self._enrich_area_user_names([record.to_dict()])
        return items[0]

    def create_area(self, data: dict[str, Any]) -> dict[str, Any]:
        if self._repo.get_area_by_cd(data["area_cd"]):
            raise ValueError(f"区域编码 {data['area_cd']} 已存在")
        record = self._repo.create_area(data)
        db.session.commit()
        return record.to_dict()

    def update_area(self, area_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = self._repo.get_area_by_cd(area_cd)
        if record is None:
            return None
        self._repo.update_area(record, data)
        db.session.commit()
        return record.to_dict()

    def delete_area(self, area_cd: str) -> bool:
        record = self._repo.get_area_by_cd(area_cd)
        if record is None:
            return False
        if self._repo.count_userarea_by_area_cd(area_cd) > 0:
            raise ValueError("该区域下有关联用户，无法删除")
        self._repo.delete_area(record)
        return True

    def _enrich_area_user_names(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """批量翻译 usercd → usercd_nm（tmc13_users）。"""
        if not items:
            return items
        codes = {str(r.get("usercd", "")).strip() for r in items if r.get("usercd")}
        if not codes:
            return items
        from app.models.system import User
        user_map = {
            u.user_cd: u.user_nm or u.user_cd
            for u in db.session.query(User).filter(User.user_cd.in_(codes)).all()
        }
        for r in items:
            v = str(r.get("usercd", "")).strip()
            if v and v in user_map:
                r["usercd_nm"] = user_map[v]
        return items

    def get_countries(self) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self._repo.get_countries()]

    def get_provinces(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in self._repo.get_provinces()]

    def get_cities(self, prvn_cd: str | None = None) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self._repo.get_cities(prvn_cd)]

    def get_towns(self, city_cd: str | None = None) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self._repo.get_towns(city_cd)]

    # ========== 国标地理表（geo_*）==========

    def get_geo_provinces(self) -> list[dict[str, Any]]:
        """国标省级列表。"""
        return [p.to_dict() for p in self._repo.get_geo_provinces()]

    def get_geo_cities(self, province_code: str | None = None) -> list[dict[str, Any]]:
        """国标地级市列表。"""
        return [c.to_dict() for c in self._repo.get_geo_cities(province_code)]

    def get_geo_areas(self, city_code: str | None = None, province_code: str | None = None) -> list[dict[str, Any]]:
        """国标区县列表。"""
        return [a.to_dict() for a in self._repo.get_geo_areas(city_code, province_code)]

    def get_geo_streets(self, area_code: str | None = None, city_code: str | None = None) -> list[dict[str, Any]]:
        """国标街道列表。"""
        return [s.to_dict() for s in self._repo.get_geo_streets(area_code, city_code)]

    # ========== SupplierClass CRUD ==========

    def get_supplier_classes(self) -> list[dict[str, Any]]:
        return self._repo.get_supplier_classes()

    def get_supplier_class_tree(self) -> list[dict[str, Any]]:
        return self._repo.get_supplier_class_tree()

    def create_supplier_class(self, data: dict[str, Any]) -> dict[str, Any]:
        """新增供应商分类，编码自动生成（2位数字，不足补零）。"""
        # 自动生成编码
        max_cd = self._repo.get_max_supplier_class_cd()
        if max_cd and max_cd.isdigit():
            next_num = int(max_cd) + 1
        else:
            next_num = 1
        class_cd = str(next_num).zfill(2)
        data["class_cd"] = class_cd
        return self._repo.create_supplier_class(data).to_dict()

    def update_supplier_class(self, class_cd: str, data: dict[str, Any]) -> dict[str, Any]:
        obj = self._repo.get_supplier_class(class_cd)
        if not obj:
            raise ValueError(f"分类 {class_cd} 不存在")
        return self._repo.update_supplier_class(obj, data).to_dict()

    def delete_supplier_class(self, class_cd: str) -> None:
        obj = self._repo.get_supplier_class(class_cd)
        if not obj:
            raise ValueError(f"分类 {class_cd} 不存在")
        child_count = self._repo.count_child_classes(class_cd)
        if child_count > 0:
            raise ValueError(f"分类 {class_cd} 下存在 {child_count} 个子分类，无法删除")
        supplier_count = self._repo.count_suppliers_by_class(class_cd)
        if supplier_count > 0:
            raise ValueError(f"分类 {class_cd} 下存在 {supplier_count} 个供应商，无法删除")
        self._repo.delete_supplier_class(obj)


class UserAreaService:
    """区域-用户关联服务（TIT06_USERAREA）。"""

    def __init__(self) -> None:
        from app.repositories.system_repository import UserAreaRepository
        self._repo = UserAreaRepository

    def list_users_by_area_cd(self, area_cd: str) -> list[dict[str, Any]]:
        """返回全量用户列表 + choose 标记（对齐 PB d_mc_areausers）。

        Returns:
            [{user_cd, user_nm, dept_cd, choose(0/1)}, ...]
        """
        from app.models.system import User
        chosen = self._repo.list_user_cds_by_area_cd(area_cd)
        users = (
            db.session.query(User)
            .filter(db.or_(User.useflg == "1", User.useflg.is_(None)))
            .order_by(User.user_cd)
            .all()
        )
        return [
            {
                "user_cd": u.user_cd,
                "user_nm": u.user_nm or u.user_cd,
                "dept_cd": u.dept_cd or "",
                "choose": 1 if u.user_cd in chosen else 0,
            }
            for u in users
        ]

    def set_users(self, area_cd: str, user_cds: list[str]) -> dict[str, Any]:
        """批量分配用户到区域。"""
        self._repo.set_users(area_cd, user_cds)
        db.session.commit()
        return {"area_cd": area_cd, "user_cds": user_cds}
