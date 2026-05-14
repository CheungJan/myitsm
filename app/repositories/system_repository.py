"""系统管理数据访问层。"""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models.master import Area, City, ComMode, Country, CustClass, CustPosRl, Customer, Eid, EidTrack, Item, ItemClass, PosREid, Province, SysCode, Town
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
        """物料分类树（PostgreSQL WITH RECURSIVE CTE + 叶子物料）。"""
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
        # 查询所有物料作为叶子节点
        items = list(db.session.query(Item.item_cd, Item.item_nm, Item.class_cd)
                     .order_by(Item.item_cd).all())
        node_map: dict[str, dict[str, Any]] = {}
        roots: list[dict[str, Any]] = []
        for r in rows:
            node = {"class_cd": r.class_cd, "class_nm": r.class_nm,
                    "childflg": r.childflg, "parent_cd": r.parent_cd.strip() if r.parent_cd else "",
                    "children": [], "type": "class"}
            node_map[r.class_cd] = node
            parent = r.parent_cd.strip() if r.parent_cd else None
            if parent and parent in node_map:
                node_map[parent]["children"].append(node)
            else:
                roots.append(node)
        # 将物料挂载到对应分类下
        for item_cd, item_nm, class_cd in items:
            label = f"{item_cd} {item_nm}" if item_nm and item_nm != item_cd else item_cd
            leaf = {"class_cd": item_cd, "class_nm": label,
                    "childflg": "0", "parent_cd": class_cd,
                    "children": [], "type": "item"}
            if class_cd and class_cd in node_map:
                node_map[class_cd]["children"].append(leaf)
        return roots

    @staticmethod
    def get_bom_class_tree() -> list[dict[str, Any]]:
        """BOM 分类树：只含 typflg=1 成品的分类 + 成品作为叶子节点。"""
        # 找到有成品（typflg=1）的分类集合
        finished_classes = set(r[0] for r in db.session.query(Item.class_cd)
                               .filter(Item.typflg == "1").distinct().all())
        # 递归收集所有父分类（保证层级完整）
        all_relevant: set[str] = set(finished_classes)
        while True:
            parents = set(r[0] for r in db.session.query(ItemClass.parent_cd)
                         .filter(ItemClass.class_cd.in_(list(all_relevant)),
                                 ItemClass.parent_cd.isnot(None),
                                 ItemClass.parent_cd != "").all())
            new_parents = parents - all_relevant
            if not new_parents:
                break
            all_relevant.update(new_parents)
            # 防止死循环
            if len(all_relevant) > 500:
                break

        # CTE 生成完整树（含所有分类）
        sql = db.text("""
            WITH RECURSIVE tree AS (
                SELECT ic.class_cd, ic.class_nm, ic.childflg, ic.parent_cd,
                       ic.opercd, COALESCE(u.user_nm, ic.opercd) AS oper_nm,
                       COALESCE(ic.gendate, ic.created_at) AS gendate, 0 AS depth
                FROM tmm11_itemclass ic
                LEFT JOIN tmc13_users u ON u.user_cd = TRIM(ic.opercd)
                WHERE ic.parent_cd IS NULL
                UNION ALL
                SELECT c.class_cd, c.class_nm, c.childflg, c.parent_cd,
                       c.opercd, COALESCE(u2.user_nm, c.opercd) AS oper_nm,
                       COALESCE(c.gendate, c.created_at), t.depth + 1
                FROM tmm11_itemclass c
                JOIN tree t ON c.parent_cd = t.class_cd
                LEFT JOIN tmc13_users u2 ON u2.user_cd = TRIM(c.opercd)
            )
            SELECT class_cd, class_nm, childflg, parent_cd, opercd, oper_nm, gendate, depth
            FROM tree ORDER BY depth, class_cd
        """)
        rows = db.session.execute(sql).fetchall()

        # 成品叶子节点
        finished_items = list(db.session.query(Item.item_cd, Item.item_nm, Item.class_cd)
                              .filter(Item.typflg == "1").order_by(Item.item_cd).all())

        node_map: dict[str, dict[str, Any]] = {}
        roots: list[dict[str, Any]] = []
        for r in rows:
            if r.class_cd not in all_relevant:
                continue  # 没有成品的分类不显示
            node = {"class_cd": r.class_cd, "class_nm": r.class_nm,
                    "childflg": r.childflg, "parent_cd": r.parent_cd.strip() if r.parent_cd else "",
                    "opercd": (r.oper_nm or r.opercd or ""),
                    "gendate": str(r.gendate)[:10] if r.gendate else "",
                    "children": [], "type": "class"}
            node_map[r.class_cd] = node
            parent = r.parent_cd.strip() if r.parent_cd else None
            if parent and parent in node_map:
                node_map[parent]["children"].append(node)
            else:
                roots.append(node)

        for item_cd, item_nm, class_cd in finished_items:
            label = f"{item_cd} {item_nm}" if item_nm and item_nm != item_cd else item_cd
            leaf = {"class_cd": item_cd, "class_nm": label,
                    "childflg": "0", "parent_cd": class_cd,
                    "children": [], "type": "item"}
            if class_cd and class_cd in node_map:
                node_map[class_cd]["children"].append(leaf)
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
    def get_item_suppliers(item_cd: str) -> list[dict[str, Any]]:
        """查询物料关联的供应商列表（含供应商名称）。"""
        from app.models.master import CustItems
        rows = db.session.query(CustItems).filter(CustItems.itemcd == item_cd).all()
        result = []
        for r in rows:
            d = r.to_dict()
            from app.models.master import Supplier
            s = db.session.get(Supplier, r.custcd)
            d["supp_nm"] = s.supp_nm if s else ""
            result.append(d)
        return result

    @staticmethod
    def get_item_supplier(item_cd: str, cust_cd: str):
        from app.models.master import CustItems
        return db.session.get(CustItems, (item_cd, cust_cd))

    @staticmethod
    def add_item_supplier(data: dict[str, Any]):
        from app.models.master import CustItems
        r = CustItems(**data)
        db.session.add(r)
        db.session.commit()
        return r

    @staticmethod
    def update_item_supplier(r: Any, data: dict[str, Any]) -> Any:
        for k, v in data.items():
            setattr(r, k, v)
        db.session.commit()
        return r

    @staticmethod
    def delete_item_supplier(r: Any) -> bool:
        db.session.delete(r)
        db.session.commit()
        return True

    @staticmethod
    def list_all_suppliers():
        from app.models.master import Supplier
        rows = db.session.query(Supplier.supp_cd, Supplier.supp_nm).order_by(Supplier.supp_cd).all()
        return [{"supp_cd": r[0], "supp_nm": r[1]} for r in rows]

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
                  class_cd: str | None = None, recursive: bool = True,
                  typflg: str | None = None) -> tuple[list[Item], int]:
        """获取物料列表，支持分类筛选、递归子分类、搜索、成品/配件过滤。"""
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
        if typflg:
            q = q.filter(Item.typflg == typflg)
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
        from app.models.system import User
        whs = list(db.session.query(Warehouse).order_by(Warehouse.whcd).all())
        user_map: dict[str, str] = {}
        result = []
        for w in whs:
            d = w.to_dict()
            leader = w.leader or ""
            if leader and leader not in user_map:
                u = db.session.get(User, leader)
                user_map[leader] = u.user_nm if u else ""
            d["leader_nm"] = user_map.get(leader, "")
            result.append(d)
        return result

    @staticmethod
    def get_warehouse(whcd: str) -> Any:
        from app.models.warehouse import Warehouse
        return db.session.get(Warehouse, whcd)

    @staticmethod
    def create_warehouse(data: dict[str, Any]) -> Any:
        from app.models.warehouse import Warehouse
        w = Warehouse(**data)
        db.session.add(w)
        db.session.commit()
        return w

    @staticmethod
    def update_warehouse(record: Any, data: dict[str, Any]) -> Any:
        for k, v in data.items():
            setattr(record, k, v)
        db.session.commit()
        return record

    @staticmethod
    def delete_warehouse(record: Any) -> None:
        db.session.delete(record)
        db.session.commit()

    @staticmethod
    def get_eid_tracks(itemcd: str, eid: str) -> list[EidTrack]:
        return list(db.session.query(EidTrack).filter(
            EidTrack.itemcd == itemcd, EidTrack.eid == eid
        ).order_by(EidTrack.change_date.asc(), EidTrack.seqno.asc()).all())

    @staticmethod
    def get_cust_pos_rl(page: int = 1, per_page: int = 20, search: str | None = None,
                         class_cd: str | None = None, asset_type: str | None = None,
                         asset_owner: str | None = None, useflg: str | None = None,
                         location: str | None = None, whcd: str | None = None,
                         sflg: str | None = None, cust_cd: str | None = None,
                         item_class: str | None = None) -> tuple[list[dict], int]:
        """资产台账列表（以 Eid 为主表，BOM 归属按页批量后解析）。"""
        from app.models.master import Customer as CustModel, Item, CustClass

        # BOM 配件归属子查询：找出所有"父设备有客户"的 BOM 配件 EID
        bom_cust_subq = (
            db.session.query(PosREid.eid.label("bom_eid"))
            .join(CustPosRl, db.and_(
                PosREid.posid == CustPosRl.eid,
                CustPosRl.useflg == "1",
            ))
            .filter(PosREid.useflg == "1")
            .distinct()
            .subquery()
        )

        q = (db.session.query(Eid, CustPosRl, bom_cust_subq.c.bom_eid,
              CustModel.cust_nm, CustModel.parentcd, CustModel.class_cd,
              CustModel.cust_card, Item.item_nm, CustClass.class_nm.label("cust_class_nm"))
        .outerjoin(CustPosRl, Eid.eid == CustPosRl.eid)
        .outerjoin(CustModel, CustPosRl.cust_cd == CustModel.cust_cd)
        .outerjoin(Item, Eid.itemcd == Item.item_cd)
        .outerjoin(CustClass, CustModel.class_cd == CustClass.class_cd)
        .outerjoin(bom_cust_subq, Eid.eid == bom_cust_subq.c.bom_eid))

        if class_cd:
            q = q.filter(CustModel.class_cd == class_cd)
        if search:
            q = q.filter(db.or_(
                Eid.eid.ilike(f"%{search}%"),
                CustModel.cust_nm.ilike(f"%{search}%"),
                CustModel.cust_card.ilike(f"%{search}%"),
            ))
        if asset_type:
            q = q.filter(Eid.asset_type == asset_type)
        if asset_owner:
            q = q.filter(Eid.asset_owner == asset_owner)
        if sflg:
            q = q.filter(Eid.sflg == sflg)
        if cust_cd:
            q = q.filter(CustPosRl.cust_cd == cust_cd)
        if item_class:
            all_cds: set[str] = set()
            direct_items: set[str] = set()
            for ic in item_class.split(","):
                ic = ic.strip()
                if not ic:
                    continue
                if SystemRepository.get_item_class_by_cd(ic):
                    all_cds.update(SystemRepository._get_descendant_class_cds(ic))
                else:
                    direct_items.add(ic)
            conditions: list = []
            if all_cds:
                item_cds = db.session.query(Item.item_cd).filter(Item.class_cd.in_(list(all_cds))).all()
                conditions.append(Eid.itemcd.in_([r[0] for r in item_cds]))
            if direct_items:
                conditions.append(Eid.itemcd.in_(list(direct_items)))
            if conditions:
                q = q.filter(db.or_(*conditions))

        has_rl = CustPosRl.id.isnot(None)
        has_bom_cust = bom_cust_subq.c.bom_eid.isnot(None)
        is_customer = db.or_(has_rl, has_bom_cust)

        if location == "customer":
            q = q.filter(is_customer)
        elif location == "warehouse":
            q = q.filter(~is_customer)

        if useflg:
            if location == "warehouse":
                q = q.filter(Eid.useflg == useflg)
            else:
                q = q.filter(db.or_(
                    db.and_(has_rl, CustPosRl.useflg == useflg),
                    db.and_(~has_rl, has_bom_cust),
                    db.and_(~has_rl, ~has_bom_cust, Eid.useflg == useflg),
                ))
        if whcd:
            whcds = [w.strip() for w in whcd.split(",") if w.strip()]
            if whcds:
                q = q.filter(Eid.whcd.in_(whcds))

        total = q.count()
        rows = q.order_by(Eid.eid.desc()).offset((page - 1) * per_page).limit(per_page).all()

        # —— 按页批量解析 BOM 归属（仅对无直接 CustPosRl 的设备） ——
        bom_eids = [e.eid for e, r, *_ in rows if not r]
        bom_map: dict[str, dict[str, str | None]] = {}
        if bom_eids:
            bom_rows = (db.session.query(PosREid.eid, PosREid.posid,
                        CustModel.cust_nm, CustModel.parentcd, CustModel.cust_card,
                        CustClass.class_nm)
                .filter(PosREid.eid.in_(bom_eids), PosREid.useflg == "1")
                .join(CustPosRl, db.and_(PosREid.posid == CustPosRl.eid, CustPosRl.useflg == "1"))
                .join(CustModel, CustPosRl.cust_cd == CustModel.cust_cd)
                .outerjoin(CustClass, CustModel.class_cd == CustClass.class_cd)
                .all())
            for eid, posid, cn, pcd, card, ccnm in bom_rows:
                bom_map[eid] = {"host_eid": posid, "cust_nm": cn, "parentcd": pcd,
                                "cust_card": card, "cust_class_nm": ccnm}

        pd_map: dict[str, str] = {}
        wh_map: dict[str, str] = {}
        result = []
        for e, r, bom_eid, cust_nm, parentcd, _cd, cust_card, item_nm, cust_class_nm in rows:
            d = e.to_dict()
            if r:
                d["id"] = r.id
                d["cust_nm"] = cust_nm or "库存"
                d["cust_card"] = cust_card or ""
                d["cust_class_nm"] = cust_class_nm or ""
                d["useflg"] = r.useflg or (e.useflg or "1")
                d["asset_status"] = getattr(r, 'asset_status', None) or ""
                d["parentcd"] = (parentcd or "").strip()
            elif e.eid in bom_map:
                bm = bom_map[e.eid]
                d["id"] = None
                d["cust_nm"] = bm["cust_nm"] or "库存"
                d["cust_card"] = bm["cust_card"] or ""
                d["cust_class_nm"] = bm["cust_class_nm"] or ""
                d["useflg"] = e.useflg or "1"
                d["asset_status"] = ""
                d["parentcd"] = (bm["parentcd"] or "").strip()
                d["host_eid"] = bm["host_eid"]
            else:
                d["id"] = None
                d["cust_nm"] = "库存"
                d["cust_card"] = ""
                d["cust_class_nm"] = ""
                d["useflg"] = e.useflg or "1"
                d["asset_status"] = ""
                d["parentcd"] = ""
            # 仓库名解析
            whcd_val = e.whcd or ""
            if whcd_val and whcd_val not in wh_map:
                from app.models.warehouse import Warehouse
                wh = db.session.get(Warehouse, whcd_val)
                wh_map[whcd_val] = wh.whnm if wh else ""
            d["wh_nm"] = wh_map.get(whcd_val, "")
            # 管理单位解析
            parentcd_raw = d.get("parentcd", "")
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
