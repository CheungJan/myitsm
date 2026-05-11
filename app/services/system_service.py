"""系统管理业务服务。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
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
            user_dict["groups"] = [{"group_cd": gc, "group_nm": all_groups.get(gc, gc)} for gc in group_cds]
        else:
            user_dict["groups"] = []
        return user_dict

    def list_users(
        self,
        status: str | None = None,
        user_cd: str | None = None,
        user_nm: str | None = None,
        dept_cd: str | None = None,
    ) -> list[dict[str, Any]]:
        """获取用户列表，支持多条件筛选。"""
        users = self._repo.get_users(status=status, user_cd=user_cd, user_nm=user_nm, dept_cd=dept_cd)
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
            payload["password"] = generate_password_hash(payload["password"], method="pbkdf2:sha256")
        return self._repo.create_user(payload).to_dict()

    def update_user(self, user_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """更新用户，可选更新密码。"""
        r = self._repo.get_user_by_cd(user_cd)
        if not r:
            return None
        payload = dict(data)
        if payload.get("password"):
            from werkzeug.security import generate_password_hash
            payload["password"] = generate_password_hash(payload["password"], method="pbkdf2:sha256")
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
        """获取用户组列表。"""
        groups = self._repo.get_groups()
        return [grp.to_dict() for grp in groups]

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

    def get_group_members(self, group_cd: str) -> list[dict[str, Any]]:
        return self._repo.get_group_members(group_cd)

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

    def update_sysparm(self, parm_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """更新系统参数。"""
        r = self._repo.update_sysparm(parm_cd, data)
        return r.to_dict() if r else None

    # ——— 物料分类 ———

    def list_item_classes(self) -> list[dict[str, Any]]:
        """获取所有物料分类（扁平列表）。"""
        classes = self._repo.get_item_classes()
        return [c.to_dict() for c in classes]

    def get_item_class_tree(self) -> list[dict[str, Any]]:
        """获取物料分类树。"""
        return self._repo.get_item_class_tree()

    def create_item_class(self, data: dict[str, Any]) -> dict[str, Any]:
        """新增物料分类。"""
        return self._repo.create_item_class(data).to_dict()

    def update_item_class(self, class_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """更新物料分类。"""
        r = self._repo.get_item_class_by_cd(class_cd)
        return self._repo.update_item_class(r, data).to_dict() if r else None

    def delete_item_class(self, class_cd: str) -> bool:
        """删除物料分类（有子分类则拒绝）。"""
        r = self._repo.get_item_class_by_cd(class_cd)
        if not r:
            return False
        children = [c for c in self._repo.get_item_classes() if c.parent_cd and c.parent_cd.strip() == class_cd]
        if children:
            child_cds = [c.class_cd for c in children]
            raise ValueError(f"该分类下有 {len(children)} 个子分类，请先删除子分类: {', '.join(child_cds[:5])}{'...' if len(child_cds) > 5 else ''}")
        self._repo.delete_item_class(r)
        return True

    # ——— 基础数据 ———

    def list_items(
        self, page: int = 1, per_page: int = 20,
        class_cd: str | None = None, recursive: bool = True,
        search: str | None = None,
    ) -> dict[str, Any]:
        """获取物料列表，支持分类筛选、递归子分类、搜索。"""
        items, total = self._repo.get_items(
            page=page, per_page=per_page,
            class_cd=class_cd, recursive=recursive, search=search,
        )
        return {"items": [i.to_dict() for i in items], "total": total}

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
        children = [c for c in self._repo.get_cust_classes() if c.parent_cd and c.parent_cd.strip() == class_cd]
        if children:
            child_cds = [c.class_cd for c in children]
            raise ValueError(f"该分类下有 {len(children)} 个子分类，请先删除子分类: {', '.join(child_cds[:5])}{'...' if len(child_cds) > 5 else ''}")
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
        if not hasattr(self.__class__, "_ref_cache"):
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
        # 支付方式 ZF
        cust["zf_type_nm"] = cache["zf"].get(cust.get("zf_type", ""), "")
        # 通讯方式
        cust["comm_mode_nm"] = cache["commode"].get(cust.get("comm_mode", ""), "")
        # 行政区域（area 存储的是整数 area_id，cache key 是字符串）
        cust["area_nm"] = cache["area"].get(str(cust.get("area") or ""), "")
        # 环线位置
        loc_map = {"1": "内环", "2": "中环", "3": "外环"}
        cust["location_nm"] = loc_map.get(cust.get("location", ""), "")
        # POS 状态（posstatus1 是子码，无独立中文名）
        cust["posstatus_nm"] = cache.get("ps", {}).get(cust.get("posstatus", ""), "")
        # 设备状态
        cust["s_status_nm"] = cache.get("ss", {}).get(cust.get("s_status", ""), "")
        # POS 数量 = 有效设备数
        cust["pos_count"] = self._repo.get_cust_pos_count(cust["cust_cd"])
        # 生命周期状态
        cust["customer_status_nm"] = cache.get("cs", {}).get(cust.get("customer_status", ""), "")
        cust["source_type_nm"] = cache.get("src", {}).get(cust.get("source_type", ""), "")
        # 行政区域
        cust["country_nm"] = cache.get("country", {}).get(cust.get("country_cd", ""), "")
        cust["prvn_nm"] = cache.get("province", {}).get(cust.get("prvn_cd", ""), "")
        cust["city_nm"] = cache.get("city", {}).get(cust.get("city_cd", ""), "")
        cust["town_nm"] = cache.get("town", {}).get(cust.get("town_cd", ""), "")
        return cust

    @staticmethod
    def _build_ref_cache() -> dict[str, dict[str, str]]:
        """构建码表查找缓存。"""
        repo = SystemRepository()
        cache: dict[str, dict[str, str]] = {"bt": {}, "yb": {}, "zf": {}, "commode": {}, "area": {}}
        for s in repo.get_syscodes("BT"):
            cache["bt"][s.code_cd] = s.code_nm or ""
        for s in repo.get_syscodes("YB"):
            cache["yb"][s.code_cd] = s.code_nm or ""
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
        for c in repo.get_commodes():
            cache["commode"][c.cmm_cd] = c.cmm_nm or ""
        for a in repo.get_areas():
            cache["area"][a.area_cd] = a.name or a.area_nm or ""
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
        return cache

    def list_customers(
        self, page: int = 1, per_page: int = 20,
        class_cd: str | None = None, search: str | None = None,
    ) -> dict[str, Any]:
        items, total = self._repo.get_customers(
            page=page, per_page=per_page, class_cd=class_cd, search=search)
        resolved = [self._resolve_customer_refs(c.to_dict()) for c in items]
        return {"items": resolved, "total": total}

    # ——— EID ———

    def get_eid_itemcd_tree(self) -> list[dict[str, Any]]:
        """获取物料分类树（含 EID 数量）。"""
        return self._repo.get_eid_itemcd_tree()

    def list_eid(self, page: int = 1, per_page: int = 20,
                 search: str | None = None, class_cd: str | None = None) -> dict[str, Any]:
        items, total = self._repo.get_eid_list(page=page, per_page=per_page, search=search, class_cd=class_cd)
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
        result = []
        for e in items:
            d = e.to_dict()
            d["item_nm"] = item_map.get(e.itemcd, "")
            d["wh_nm"] = wh_map.get(e.whcd, "")
            result.append(d)
        return {"items": result, "total": total}

    def list_assets(self, page: int = 1, per_page: int = 20,
                    search: str | None = None, class_cd: str | None = None,
                    asset_type: str | None = None, asset_owner: str | None = None,
                    useflg: str | None = None) -> dict[str, Any]:
        items, total = self._repo.get_cust_pos_rl(
            page=page, per_page=per_page, search=search,
            class_cd=class_cd, asset_type=asset_type, asset_owner=asset_owner, useflg=useflg)
        return {"items": items, "total": total}

    def get_asset(self, asset_id: int) -> dict[str, Any] | None:
        """获取单个资产记录（CustPosRl）。"""
        r = self._repo.get_cust_pos_rl_by_id(asset_id)
        return r.to_dict() if r else None

    # ——— CRUD ———

    def create_item(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._repo.create_item(data).to_dict()

    def update_item(self, item_cd: str, data: dict[str, Any]) -> dict[str, Any] | None:
        r = self._repo.get_item(item_cd)
        return self._repo.update_item(r, data).to_dict() if r else None

    def delete_item(self, item_cd: str) -> bool:
        r = self._repo.get_item(item_cd)
        if r: self._repo.delete_item(r); return True
        return False

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
        if r: self._repo.delete_customer(r); return True
        return False

    def create_eid(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._repo.create_eid(data).to_dict()

    def update_eid(self, itemcd: str, eid_val: str, data: dict[str, Any]) -> dict[str, Any] | None:
        r = self._repo.update_eid(itemcd, eid_val, data)
        return r.to_dict() if r else None

    def delete_eid(self, itemcd: str, eid_val: str) -> bool:
        return self._repo.delete_eid(itemcd, eid_val)

    def get_warehouses(self) -> list[dict[str, Any]]:
        return [w.to_dict() for w in self._repo.get_warehouses()]

    def get_eid_tracks(self, itemcd: str, eid: str) -> list[dict[str, Any]]:
        tracks = self._repo.get_eid_tracks(itemcd, eid)
        from app.models.warehouse import Warehouse
        wh_map: dict[str, str] = {}
        result = []
        for t in tracks:
            d = t.to_dict()
            for wh_field in ['whcd', 'n_whcd']:
                whcd = d.get(wh_field)
                if whcd and whcd not in wh_map:
                    wh = db.session.get(Warehouse, whcd)
                    wh_map[whcd] = wh.whnm if wh else ""
                key = 'wh_nm' if wh_field == 'whcd' else 'n_wh_nm'
                d[key] = wh_map.get(whcd, "")
            result.append(d)
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
        if r: self._repo.delete_syscode(r); return True
        return False

    def get_areas(self) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self._repo.get_areas()]

    def get_commodes(self) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self._repo.get_commodes()]

    def get_countries(self) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self._repo.get_countries()]

    def get_provinces(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in self._repo.get_provinces()]

    def get_cities(self, prvn_cd: str | None = None) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self._repo.get_cities(prvn_cd)]

    def get_towns(self, city_cd: str | None = None) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self._repo.get_towns(city_cd)]
