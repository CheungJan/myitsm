"""系统管理数据访问层。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models.master import Area, City, ComMode, Country, CustClass, CustPosRl, Customer, Eid, EidTrack, Item, ItemClass, Province, SysCode, Town
from app.models.system import Department, Group, GroupRight, Menu, MenuDetail, SysParm, User, UserGroup


class SystemRepository:
    """系统管理 Repository。"""

    @staticmethod
    def get_users(
        status: str | None = None,
        user_cd: str | None = None,
        user_nm: str | None = None,
        dept_cd: str | None = None,
    ) -> list[User]:
        """获取用户列表，支持多条件筛选。"""
        query = db.session.query(User)
        if status:
            query = query.filter(User.status == status)
        if user_cd:
            query = query.filter(User.user_cd.ilike(f"%{user_cd}%"))
        if user_nm:
            query = query.filter(User.user_nm.ilike(f"%{user_nm}%"))
        if dept_cd:
            query = query.filter(User.dept_cd == dept_cd)
        return list(query.order_by(User.user_cd).all())

    @staticmethod
    def create_user(data: dict[str, Any]) -> User:
        """新增用户。"""
        user = User(**data)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update_user(record: User, data: dict[str, Any]) -> User:
        """更新用户。"""
        for k, v in data.items():
            setattr(record, k, v)
        db.session.commit()
        return record

    @staticmethod
    def delete_user(record: User) -> None:
        """删除用户。"""
        db.session.delete(record)
        db.session.commit()

    @staticmethod
    def get_user_by_cd(user_cd: str) -> User | None:
        """按编码获取用户。"""
        return db.session.get(User, user_cd)

    @staticmethod
    def get_departments() -> list[Department]:
        """获取部门列表。"""
        return list(db.session.query(Department).order_by(Department.dept_cd).all())

    @staticmethod
    def get_department_by_cd(dept_cd: str) -> Department | None:
        """按编码获取部门。"""
        return db.session.get(Department, dept_cd)

    @staticmethod
    def get_groups() -> list[Group]:
        """获取用户组列表。"""
        return list(db.session.query(Group).order_by(Group.group_cd).all())

    @staticmethod
    def get_group_by_cd(group_cd: str) -> Group | None:
        """按编码获取用户组。"""
        return db.session.get(Group, group_cd)

    @staticmethod
    def get_user_groups(user_cd: str) -> list[dict[str, Any]]:
        """获取用户所属用户组。"""
        user_groups = db.session.query(UserGroup).filter(UserGroup.user_cd == user_cd).all()
        return [{"user_cd": ug.user_cd, "group_cd": ug.group_cd} for ug in user_groups]

    # ——— 部门 CRUD ———

    @staticmethod
    def create_department(data: dict[str, Any]) -> Department:
        d = Department(**data)
        db.session.add(d)
        db.session.commit()
        return d

    @staticmethod
    def update_department(record: Department, data: dict[str, Any]) -> Department:
        for k, v in data.items():
            setattr(record, k, v)
        db.session.commit()
        return record

    @staticmethod
    def delete_department(record: Department) -> None:
        db.session.delete(record)
        db.session.commit()

    # ——— 用户组 CRUD ———

    @staticmethod
    def create_group(data: dict[str, Any]) -> Group:
        g = Group(**data)
        db.session.add(g)
        db.session.commit()
        return g

    @staticmethod
    def update_group(record: Group, data: dict[str, Any]) -> Group:
        for k, v in data.items():
            setattr(record, k, v)
        db.session.commit()
        return record

    @staticmethod
    def delete_group(record: Group) -> None:
        # 先删除关联的用户和权限记录
        db.session.query(UserGroup).filter(UserGroup.group_cd == record.group_cd).delete()
        db.session.query(GroupRight).filter(GroupRight.group_cd == record.group_cd).delete()
        db.session.delete(record)
        db.session.commit()

    @staticmethod
    def get_group_members(group_cd: str) -> list[dict[str, Any]]:
        """获取用户组成员列表（含用户名称）。"""
        rows = (
            db.session.query(UserGroup, User.user_nm)
            .join(User, UserGroup.user_cd == User.user_cd)
            .filter(UserGroup.group_cd == group_cd)
            .all()
        )
        return [{"user_cd": ug.user_cd, "group_cd": ug.group_cd, "user_nm": nm}
                for ug, nm in rows]

    @staticmethod
    def add_group_member(user_cd: str, group_cd: str) -> None:
        ug = UserGroup(user_cd=user_cd, group_cd=group_cd)
        db.session.add(ug)
        db.session.commit()

    @staticmethod
    def remove_group_member(user_cd: str, group_cd: str) -> bool:
        ug = db.session.query(UserGroup).filter(
            UserGroup.user_cd == user_cd, UserGroup.group_cd == group_cd
        ).first()
        if ug:
            db.session.delete(ug)
            db.session.commit()
            return True
        return False

    # ——— 权限管理 ———

    @staticmethod
    def get_group_rights(group_cd: str) -> list[dict[str, str]]:
        """获取用户组权限列表。"""
        rows = db.session.query(GroupRight).filter(
            GroupRight.group_cd == group_cd,
            GroupRight.right_flg == "1",
        ).all()
        return [{"menu_cd": r.menu_cd, "func_cd": r.func_cd or "view"} for r in rows]

    @staticmethod
    def set_group_rights(group_cd: str, rights: list[dict[str, str]]) -> None:
        """替换用户组权限。"""
        db.session.query(GroupRight).filter(GroupRight.group_cd == group_cd).delete()
        for r in rights:
            gr = GroupRight(
                group_cd=group_cd,
                menu_cd=r["menu_cd"],
                func_cd=r.get("func_cd", "view"),
                right_flg="1",
                useflg="1",
            )
            db.session.add(gr)
        db.session.commit()

    @staticmethod
    def get_user_permissions(user_cd: str) -> list[dict[str, str]]:
        """获取用户的有效权限（通过其所属于的用户组，并集去重）。"""
        rows = (
            db.session.query(GroupRight.menu_cd, GroupRight.func_cd)
            .join(UserGroup, GroupRight.group_cd == UserGroup.group_cd)
            .filter(
                UserGroup.user_cd == user_cd,
                GroupRight.right_flg == "1",
            )
            .distinct()
            .all()
        )
        return [{"menu_cd": r.menu_cd, "func_cd": r.func_cd or "view"} for r in rows]

    @staticmethod
    def get_menus() -> list[Menu]:
        """获取有效菜单列表。"""
        return list(
            db.session.query(Menu).filter(Menu.status == "1").order_by(Menu.menu_order).all()
        )

    @staticmethod
    def get_perm_tree() -> list[dict[str, Any]]:
        """获取权限树（菜单+功能定义），从数据库动态读取。"""
        menus = db.session.query(Menu).filter(Menu.status == "1").order_by(Menu.menu_order).all()
        funcs = db.session.query(MenuDetail).filter(MenuDetail.useflg == "1").all()
        # 功能按 menu_cd 分组
        func_map: dict[str, list[dict[str, str]]] = {}
        for f in funcs:
            func_map.setdefault(f.menu_cd, []).append({"func_cd": f.func_cd, "func_nm": f.func_nm})
        # 构建树
        menu_map = {m.menu_cd: m for m in menus}
        tree: list[dict[str, Any]] = []
        for m in menus:
            if m.parent_cd is None:
                children = []
                for child in menus:
                    if child.parent_cd == m.menu_cd:
                        children.append({
                            "menu_cd": child.menu_cd,
                            "menu_nm": child.menu_nm,
                            "funcs": func_map.get(child.menu_cd, []),
                        })
                tree.append({
                    "menu_cd": m.menu_cd,
                    "menu_nm": m.menu_nm,
                    "children": children,
                })
        return tree

    @staticmethod
    def get_sysparms() -> list[SysParm]:
        """获取系统参数列表。"""
        return list(db.session.query(SysParm).order_by(SysParm.parm_cd).all())

    @staticmethod
    def get_sysparm_by_cd(parm_cd: str) -> SysParm | None:
        """按编码获取系统参数。"""
        return db.session.get(SysParm, parm_cd)

    @staticmethod
    def update_sysparm(parm_cd: str, data: dict[str, Any]) -> SysParm | None:
        """更新系统参数（单例表）。"""
        r = db.session.get(SysParm, parm_cd)
        if r:
            for k, v in data.items():
                setattr(r, k, v)
            db.session.commit()
        return r

    # ——— 物料分类 ———

    @staticmethod
    def get_item_classes() -> list[ItemClass]:
        """获取所有物料分类（按编码排序）。"""
        return list(db.session.query(ItemClass).order_by(ItemClass.class_cd).all())

    @staticmethod
    def get_item_class_tree() -> list[dict[str, Any]]:
        """物料分类树（PostgreSQL WITH RECURSIVE CTE）。"""
        sql = db.text("""
            WITH RECURSIVE tree AS (
                SELECT class_cd, class_nm, childflg, parent_cd, 0 AS depth
                FROM tmm11_itemclass
                WHERE parent_cd IS NULL
                UNION ALL
                SELECT c.class_cd, c.class_nm, c.childflg, c.parent_cd,
                       t.depth + 1
                FROM tmm11_itemclass c
                JOIN tree t ON c.parent_cd = t.class_cd
            )
            SELECT class_cd, class_nm, childflg, parent_cd, depth
            FROM tree ORDER BY depth, class_cd
        """)
        rows = db.session.execute(sql).fetchall()
        node_map: dict[str, dict[str, Any]] = {}
        roots: list[dict[str, Any]] = []
        for r in rows:
            node = {"class_cd": r.class_cd, "class_nm": r.class_nm,
                    "childflg": r.childflg, "parent_cd": r.parent_cd.strip() if r.parent_cd else "",
                    "children": []}
            node_map[r.class_cd] = node
            parent = r.parent_cd.strip() if r.parent_cd else None
            if parent and parent in node_map:
                node_map[parent]["children"].append(node)
            else:
                roots.append(node)
        return roots

    @staticmethod
    def _get_descendant_class_cds(class_cd: str) -> list[str]:
        """CTE 递归查询指定分类的所有子分类编码。"""
        sql = db.text("""
            WITH RECURSIVE sub AS (
                SELECT class_cd FROM tmm11_itemclass WHERE class_cd = :cd
                UNION ALL
                SELECT c.class_cd FROM tmm11_itemclass c
                JOIN sub s ON c.parent_cd = s.class_cd
            )
            SELECT class_cd FROM sub
        """)
        return [r[0] for r in db.session.execute(sql, {"cd": class_cd}).fetchall()]

    @staticmethod
    def get_item_class_by_cd(class_cd: str) -> ItemClass | None:
        return db.session.get(ItemClass, class_cd)

    @staticmethod
    def create_item_class(data: dict[str, Any]) -> ItemClass:
        ic = ItemClass(**data)
        db.session.add(ic)
        db.session.commit()
        return ic

    @staticmethod
    def update_item_class(record: ItemClass, data: dict[str, Any]) -> ItemClass:
        for k, v in data.items():
            setattr(record, k, v)
        db.session.commit()
        return record

    @staticmethod
    def delete_item_class(record: ItemClass) -> None:
        db.session.delete(record)
        db.session.commit()

    # ——— 基础数据查询 ———

    @staticmethod
    def get_items(page: int = 1, per_page: int = 20, search: str | None = None,
                  class_cd: str | None = None, recursive: bool = True) -> tuple[list[Item], int]:
        """获取物料列表，支持分类筛选、递归子分类、搜索。"""
        q = db.session.query(Item)
        if class_cd:
            if recursive:
                cds = SystemRepository._get_descendant_class_cds(class_cd)
                q = q.filter(Item.class_cd.in_(cds))
            else:
                q = q.filter(Item.class_cd == class_cd)
        if search:
            q = q.filter(db.or_(
                Item.item_cd.ilike(f"%{search}%"),
                Item.item_nm.ilike(f"%{search}%"),
            ))
        q = q.order_by(Item.item_cd)
        total = q.count()
        return q.offset((page - 1) * per_page).limit(per_page).all(), total

    @staticmethod
    def get_item(item_cd: str) -> Item | None:
        return db.session.get(Item, item_cd)

    @staticmethod
    def create_item(data: dict[str, Any]) -> Item:
        item = Item(**data)
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def update_item(record: Item, data: dict[str, Any]) -> Item:
        for k, v in data.items():
            setattr(record, k, v)
        db.session.commit()
        return record

    @staticmethod
    def delete_item(record: Item) -> None:
        db.session.delete(record)
        db.session.commit()

    # ——— 客户分类 ———

    @staticmethod
    def get_cust_classes() -> list[CustClass]:
        """获取所有客户分类。"""
        return list(db.session.query(CustClass).order_by(CustClass.class_cd).all())

    @staticmethod
    def get_cust_class_tree() -> list[dict[str, Any]]:
        """客户分类树（CTE 递归，当前为单层）。"""
        sql = db.text("""
            WITH RECURSIVE tree AS (
                SELECT class_cd, class_nm, childflg, parent_cd, useflg, 0 AS depth
                FROM tmm21_custclass
                WHERE parent_cd IS NULL
                UNION ALL
                SELECT c.class_cd, c.class_nm, c.childflg, c.parent_cd, c.useflg, t.depth + 1
                FROM tmm21_custclass c
                JOIN tree t ON c.parent_cd = t.class_cd
            )
            SELECT class_cd, class_nm, childflg, parent_cd, useflg, depth
            FROM tree ORDER BY depth, class_cd
        """)
        rows = db.session.execute(sql).fetchall()
        node_map: dict[str, dict[str, Any]] = {}
        roots: list[dict[str, Any]] = []
        for r in rows:
            node = {"class_cd": r.class_cd, "class_nm": r.class_nm,
                    "childflg": r.childflg, "parent_cd": r.parent_cd.strip() if r.parent_cd else "",
                    "useflg": r.useflg, "children": []}
            node_map[r.class_cd] = node
            parent = r.parent_cd.strip() if r.parent_cd else None
            if parent and parent in node_map:
                node_map[parent]["children"].append(node)
            else:
                roots.append(node)
        return roots

    @staticmethod
    def get_cust_class_by_cd(class_cd: str) -> CustClass | None:
        return db.session.get(CustClass, class_cd)

    @staticmethod
    def create_cust_class(data: dict[str, Any]) -> CustClass:
        cc = CustClass(**data)
        db.session.add(cc)
        db.session.commit()
        return cc

    @staticmethod
    def update_cust_class(record: CustClass, data: dict[str, Any]) -> CustClass:
        for k, v in data.items():
            setattr(record, k, v)
        db.session.commit()
        return record

    @staticmethod
    def delete_cust_class(record: CustClass) -> None:
        db.session.delete(record)
        db.session.commit()

    # ——— 客户 ———

    @staticmethod
    def get_customers(page: int = 1, per_page: int = 20, search: str | None = None,
                      class_cd: str | None = None) -> tuple[list[Customer], int]:
        """获取客户列表，支持分类筛选和搜索。"""
        q = db.session.query(Customer)
        if class_cd:
            q = q.filter(Customer.class_cd == class_cd)
        if search:
            q = q.filter(db.or_(
                Customer.cust_card.ilike(f"%{search}%"),
                Customer.cust_nm.ilike(f"%{search}%"),
            ))
        q = q.order_by(Customer.cust_cd)
        total = q.count()
        return q.offset((page - 1) * per_page).limit(per_page).all(), total

    @staticmethod
    def get_customer(cust_cd: str) -> Customer | None:
        return db.session.get(Customer, cust_cd)

    @staticmethod
    def create_customer(data: dict[str, Any]) -> Customer:
        if "cust_cd" not in data or not data["cust_cd"]:
            max_cd = (
                db.session.query(Customer.cust_cd)
                .filter(Customer.cust_cd.op("~")("^[0-9]+$"))
                .order_by(Customer.cust_cd.desc())
                .first()
            )
            if max_cd and max_cd[0]:
                data["cust_cd"] = str(int(max_cd[0]) + 1).zfill(8)
            else:
                data["cust_cd"] = "00000001"
        c = Customer(**data)
        db.session.add(c)
        db.session.commit()
        return c

    @staticmethod
    def update_customer(record: Customer, data: dict[str, Any]) -> Customer:
        for k, v in data.items():
            setattr(record, k, v)
        db.session.commit()
        return record

    @staticmethod
    def delete_customer(record: Customer) -> None:
        db.session.delete(record)
        db.session.commit()

    @staticmethod
    def get_eid_itemcd_tree() -> list[dict[str, Any]]:
        """获取物料分类树，含 EID 数量。"""
        tree = SystemRepository.get_item_class_tree()
        # 统计每个 leaf 的 EID 数量
        class_counts: dict[str, int] = {}
        rows = db.session.execute(db.text("""
            SELECT i.class_cd, COUNT(*) AS cnt
            FROM tmm43_eid e
            JOIN tmm12_items i ON e.itemcd = i.item_cd
            WHERE e.useflg = '1' AND i.useflg = '1'
            GROUP BY i.class_cd
        """)).fetchall()
        for r in rows:
            class_counts[r.class_cd] = r.cnt

        def attach_count(nodes: list[dict[str, Any]]) -> int:
            total = 0
            for n in nodes:
                children_total = attach_count(n.get("children", []))
                n["eid_count"] = class_counts.get(n["class_cd"], 0) + children_total
                total += n["eid_count"]
            return total
        attach_count(tree)
        return tree

    @staticmethod
    def get_eid_list(page: int = 1, per_page: int = 20, search: str | None = None,
                     class_cd: str | None = None) -> tuple[list[Eid], int]:
        q = db.session.query(Eid)
        if class_cd:
            # 递归获取该分类下的所有物料编码
            cds = SystemRepository._get_descendant_class_cds(class_cd)
            if cds:
                item_cds = db.session.query(Item.item_cd).filter(Item.class_cd.in_(cds)).all()
                q = q.filter(Eid.itemcd.in_([r[0] for r in item_cds]))
        if search:
            q = q.filter(db.or_(Eid.eid.ilike(f"%{search}%"), Eid.itemcd.ilike(f"%{search}%")))
        q = q.order_by(Eid.eid.desc())
        total = q.count()
        return q.offset((page - 1) * per_page).limit(per_page).all(), total

    @staticmethod
    def get_eid(itemcd: str, eid_val: str) -> Eid | None:
        return db.session.get(Eid, (itemcd, eid_val))

    @staticmethod
    def create_eid(data: dict[str, Any]) -> Eid:
        e = Eid(**data)
        db.session.add(e)
        db.session.commit()
        return e

    @staticmethod
    def update_eid(itemcd: str, eid_val: str, data: dict[str, Any]) -> Eid | None:
        r = db.session.get(Eid, (itemcd, eid_val))
        if r:
            for k, v in data.items():
                setattr(r, k, v)
            db.session.commit()
        return r

    @staticmethod
    def delete_eid(itemcd: str, eid_val: str) -> bool:
        r = db.session.get(Eid, (itemcd, eid_val))
        if r:
            db.session.delete(r)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_warehouses() -> list[Any]:
        from app.models.warehouse import Warehouse
        return list(db.session.query(Warehouse).order_by(Warehouse.whcd).all())

    @staticmethod
    def get_eid_tracks(itemcd: str, eid: str) -> list[EidTrack]:
        return list(db.session.query(EidTrack).filter(
            EidTrack.itemcd == itemcd, EidTrack.eid == eid
        ).order_by(EidTrack.seqno.desc()).all())

    @staticmethod
    def get_cust_pos_rl(page: int = 1, per_page: int = 20, search: str | None = None,
                         class_cd: str | None = None, asset_type: str | None = None,
                         asset_owner: str | None = None, useflg: str | None = None,
                         location: str | None = None) -> tuple[list[dict], int]:
        """资产台账列表（以 Eid 为主表，含库存设备）。"""
        from app.models.master import Customer, Item, CustClass

        q = (db.session.query(Eid, CustPosRl, Customer.cust_nm, Customer.parentcd, Customer.class_cd,
              Customer.cust_card, Item.item_nm, CustClass.class_nm.label("cust_class_nm"))
        .outerjoin(CustPosRl, db.and_(Eid.itemcd == CustPosRl.item_cd, Eid.eid == CustPosRl.eid))
        .outerjoin(Customer, CustPosRl.cust_cd == Customer.cust_cd)
        .outerjoin(Item, Eid.itemcd == Item.item_cd)
        .outerjoin(CustClass, Customer.class_cd == CustClass.class_cd))

        if class_cd:
            q = q.filter(Customer.class_cd == class_cd)
        if search:
            q = q.filter(db.or_(Eid.eid.ilike(f"%{search}%"), Customer.cust_nm.ilike(f"%{search}%")))
        if asset_type:
            q = q.filter(Eid.asset_type == asset_type)
        if asset_owner:
            q = q.filter(Eid.asset_owner == asset_owner)
        if useflg:
            q = q.filter(CustPosRl.useflg == useflg)
        if location == "customer":
            q = q.filter(CustPosRl.id.isnot(None))
        elif location == "warehouse":
            q = q.filter(CustPosRl.id.is_(None))

        total = q.count()
        rows = q.order_by(Eid.eid.desc()).offset((page - 1) * per_page).limit(per_page).all()

        pd_map: dict[str, str] = {}
        result = []
        for e, r, cust_nm, parentcd, _cd, cust_card, item_nm, cust_class_nm in rows:
            d = e.to_dict()
            d["id"] = r.id if r else None
            d["cust_nm"] = cust_nm or "库存"
            d["cust_card"] = cust_card or ""
            d["item_nm"] = item_nm or ""
            d["cust_class_nm"] = cust_class_nm or ""
            d["useflg"] = r.useflg if r else "1"
            d["asset_status"] = getattr(r, 'asset_status', None) or "" if r else ""
            parentcd_raw = (parentcd or "").strip()
            if parentcd_raw and parentcd_raw not in pd_map:
                pc = db.session.get(CustClass, parentcd_raw)
                pd_map[parentcd_raw] = pc.class_nm if pc else ""
            d["parentcd_nm"] = pd_map.get(parentcd_raw, "")
            result.append(d)
        return result, total

    @staticmethod
    @staticmethod
    def get_cust_pos_rl_by_id(asset_id: int) -> CustPosRl | None:
        return db.session.get(CustPosRl, asset_id)

    @staticmethod
    def get_cust_pos_count(cust_cd: str) -> int:
        """统计客户有效设备数量。"""
        return db.session.query(CustPosRl).filter(
            CustPosRl.cust_cd == cust_cd, CustPosRl.useflg == "1"
        ).count()

    # ——— 码表查询 ———

    @staticmethod
    def get_syscodes(code_typ: str) -> list[SysCode]:
        return list(db.session.query(SysCode).filter(
            SysCode.code_typ == code_typ, SysCode.useflg == "1"
        ).order_by(SysCode.sort_no, SysCode.code_cd).all())

    @staticmethod
    def get_all_syscodes() -> list[SysCode]:
        return list(db.session.query(SysCode).order_by(
            SysCode.code_typ, db.func.coalesce(SysCode.sort_no, 999), SysCode.code_cd
        ).all())

    @staticmethod
    def get_syscode_by_id(code_id: int) -> SysCode | None:
        return db.session.get(SysCode, code_id)

    @staticmethod
    def create_syscode(data: dict[str, Any]) -> SysCode:
        sc = SysCode(**data)
        db.session.add(sc)
        db.session.commit()
        return sc

    @staticmethod
    def update_syscode(record: SysCode, data: dict[str, Any]) -> SysCode:
        for k, v in data.items():
            setattr(record, k, v)
        db.session.commit()
        return record

    @staticmethod
    def delete_syscode(record: SysCode) -> None:
        db.session.delete(record)
        db.session.commit()

    @staticmethod
    def get_areas() -> list[Area]:
        return list(db.session.query(Area).filter(
            db.or_(Area.useflg == "1", Area.useflg.is_(None))
        ).order_by(Area.area_cd).all())

    @staticmethod
    def get_commodes() -> list[ComMode]:
        return list(db.session.query(ComMode).filter(ComMode.useflg == "1").order_by(ComMode.cmm_cd).all())

    @staticmethod
    def get_countries() -> list[Country]:
        return list(db.session.query(Country).filter(
            db.or_(Country.useflg == "1", Country.useflg.is_(None))
        ).order_by(Country.country_cd).all())

    @staticmethod
    def get_provinces() -> list[Province]:
        return list(db.session.query(Province).filter(
            db.or_(Province.useflg == "1", Province.useflg.is_(None))
        ).order_by(Province.prvn_cd).all())

    @staticmethod
    def get_cities(prvn_cd: str | None = None) -> list[City]:
        q = db.session.query(City).filter(
            db.or_(City.useflg == "1", City.useflg.is_(None))
        )
        if prvn_cd:
            q = q.filter(City.prvn_cd == prvn_cd)
        return list(q.order_by(City.city_cd).all())

    @staticmethod
    def get_towns(city_cd: str | None = None) -> list[Town]:
        q = db.session.query(Town).filter(
            db.or_(Town.useflg == "1", Town.useflg.is_(None))
        )
        if city_cd:
            q = q.filter(Town.city_cd == city_cd)
        return list(q.order_by(Town.town_cd).all())
