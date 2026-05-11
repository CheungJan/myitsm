"""
系统管理模型。

对应数据库表：TMC01_MENUS, TMC02_MENUSDT, TMC03_USERMENUS,
TMC11_DEPARTMENTS, TMC12_GROUPS, TMC13_USERS,
TMC21_USERGROUP, TMC22_USERBUSITYP, TMC31_GROUPRIGHT,
TMC41_ACCLOG, TMC71_SYSPARM
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel


class User(BaseModel):
    """用户表（TMC13_USERS）。"""

    __tablename__ = "tmc13_users"
    _hidden_fields: set[str] = {"password"}

    user_cd = db.Column(db.String(20), primary_key=True, comment="用户编码")
    user_nm = db.Column(db.String(50), nullable=False, comment="用户名称")
    password = db.Column(db.String(128), nullable=False, comment="密码")
    status = db.Column(db.String(1), default="1", comment="状态（1有效/0无效）")
    dept_cd = db.Column(db.String(20), db.ForeignKey("tmc11_departments.dept_cd"), comment="部门")
    phone = db.Column(db.String(30), comment="电话")
    email = db.Column(db.String(100), comment="邮箱")
    # --- Oracle 原表恢复字段 ---
    passwd = db.Column(db.String(128), comment="原始密码（数据迁移用）")
    credamt = db.Column(db.Numeric(12, 2), comment="信用额度")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")

    groups = db.relationship("UserGroup", back_populates="user", lazy="dynamic")


class Department(BaseModel):
    """部门表（TMC11_DEPARTMENTS）。"""

    __tablename__ = "tmc11_departments"

    dept_cd = db.Column(db.String(20), primary_key=True, comment="部门编码")
    dept_nm = db.Column(db.String(50), nullable=False, comment="部门名称")
    parent_cd = db.Column(db.String(20), comment="上级部门编码")
    status = db.Column(db.String(1), default="1", comment="状态")
    # --- Oracle 原表恢复字段（5个） ---
    levelcd = db.Column(db.String(1), comment="部门层级")
    parent = db.Column(db.String(6), comment="上级部门（Oracle原字段）")
    leader = db.Column(db.String(6), comment="部门领导")
    childflg = db.Column(db.String(1), comment="子节点标志")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")


class Group(BaseModel):
    """用户组表（TMC12_GROUPS）。"""

    __tablename__ = "tmc12_groups"

    group_cd = db.Column(db.String(20), primary_key=True, comment="组编码")
    group_nm = db.Column(db.String(50), nullable=False, comment="组名称")
    status = db.Column(db.String(1), default="1", comment="状态")
    # --- Oracle 原表恢复字段 ---
    useflg = db.Column(db.String(1), default="1", comment="有效标志")

    members = db.relationship("UserGroup", back_populates="group", lazy="dynamic")
    rights = db.relationship("GroupRight", back_populates="group", lazy="dynamic")


class UserGroup(BaseModel):
    """用户-组关联表（TMC21_USERGROUP）。"""

    __tablename__ = "tmc21_usergroup"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_cd = db.Column(db.String(20), db.ForeignKey("tmc13_users.user_cd"), nullable=False)
    group_cd = db.Column(db.String(20), db.ForeignKey("tmc12_groups.group_cd"), nullable=False)

    user = db.relationship("User", back_populates="groups")
    group = db.relationship("Group", back_populates="members")

    __table_args__ = (db.UniqueConstraint("user_cd", "group_cd", name="uq_usergroup"),)


class UserBusiTyp(BaseModel):
    """用户业务类型关联（TMC22_USERBUSITYP）。"""

    __tablename__ = "tmc22_userbusityp"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_cd = db.Column(db.String(20), db.ForeignKey("tmc13_users.user_cd"), nullable=False)
    busi_typ = db.Column(db.String(10), nullable=False, comment="业务类型")


class Menu(BaseModel):
    """菜单主表（TMC01_MENUS）。"""

    __tablename__ = "tmc01_menus"

    menu_cd = db.Column(db.String(20), primary_key=True, comment="菜单编码")
    menu_nm = db.Column(db.String(100), nullable=False, comment="菜单名称")
    parent_cd = db.Column(db.String(20), comment="上级菜单编码")
    menu_order = db.Column(db.Integer, default=0, comment="排序号")
    status = db.Column(db.String(1), default="1", comment="状态")
    # --- Oracle 原表恢复字段（7个） ---
    levelcd = db.Column(db.String(1), comment="菜单层级")
    parent = db.Column(db.String(6), comment="父级菜单（Oracle原字段）")
    picname = db.Column(db.String(30), comment="图标名称")
    ordno = db.Column(db.Integer, comment="排序号（Oracle原字段）")
    openflg = db.Column(db.String(1), comment="开放标志")
    childflg = db.Column(db.String(1), comment="子节点标志")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")

    details = db.relationship("MenuDetail", back_populates="menu", lazy="dynamic")


class MenuDetail(BaseModel):
    """菜单明细表（TMC02_MENUSDT）。"""

    __tablename__ = "tmc02_menusdt"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    menu_cd = db.Column(db.String(20), db.ForeignKey("tmc01_menus.menu_cd"), nullable=False)
    func_cd = db.Column(db.String(50), comment="功能编码")
    func_nm = db.Column(db.String(100), comment="功能名称")
    # --- Oracle 原表恢复字段 ---
    useflg = db.Column(db.String(1), default="1", comment="有效标志")

    menu = db.relationship("Menu", back_populates="details")


class UserMenu(BaseModel):
    """用户菜单权限（TMC03_USERMENUS）。"""

    __tablename__ = "tmc03_usermenus"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_cd = db.Column(db.String(20), db.ForeignKey("tmc13_users.user_cd"), nullable=False)
    menu_cd = db.Column(db.String(20), db.ForeignKey("tmc01_menus.menu_cd"), nullable=False)
    # --- Oracle 原表恢复字段 ---
    ordno = db.Column(db.Integer, comment="排序号")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")


class GroupRight(BaseModel):
    """组权限表（TMC31_GROUPRIGHT）。"""

    __tablename__ = "tmc31_groupright"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_cd = db.Column(db.String(20), db.ForeignKey("tmc12_groups.group_cd"), nullable=False)
    menu_cd = db.Column(db.String(20), nullable=False, comment="菜单编码")
    func_cd = db.Column(db.String(50), comment="功能编码")
    right_flg = db.Column(db.String(1), default="1", comment="权限标志")
    # --- Oracle 原表恢复字段 ---
    scale = db.Column(db.String(1), comment="权限范围")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")

    group = db.relationship("Group", back_populates="rights")


class SysParm(BaseModel):
    """系统参数表（TMC71_SYSPARM）。"""

    __tablename__ = "tmc71_sysparm"

    parm_cd = db.Column(db.String(50), primary_key=True, comment="参数编码")
    parm_nm = db.Column(db.String(100), comment="参数名称")
    parm_val = db.Column(db.String(500), comment="参数值")
    parm_desc = db.Column(db.String(200), comment="参数说明")
    # --- Oracle 原表恢复字段（9个） ---
    pk = db.Column(db.String(50), comment="参数主键")
    costtype = db.Column(db.String(1), comment="成本类型")
    autobackpath = db.Column(db.String(200), comment="自动备份路径")
    invoicesharepath = db.Column(db.String(200), comment="发票共享路径")
    poinvaliddays = db.Column(db.Integer, comment="采购失效天数")
    soinvaliddays = db.Column(db.Integer, comment="销售失效天数")
    allowmultilogon = db.Column(db.String(1), comment="允许多点登录")
    shopbilltype = db.Column(db.String(1), comment="店铺单据类型")
    centralwarehouse = db.Column(db.String(4), comment="中心仓库编码")
    # ITSM 新增全局参数
    jwt_expiration_seconds = db.Column(db.Integer, default=28800, comment="JWT超时(秒)")
    log_retention_days = db.Column(db.Integer, default=30, comment="日志保留天数")
    max_upload_size_mb = db.Column(db.Integer, default=10, comment="上传大小限制(MB)")


class AccLog(BaseModel):
    """访问日志表（TMC41_ACCLOG）。"""

    __tablename__ = "tmc41_acclog"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_cd = db.Column(db.String(20), comment="用户编码")
    action = db.Column(db.String(50), comment="操作类型")
    detail = db.Column(db.Text, comment="操作明细")
    ip_addr = db.Column(db.String(50), comment="IP地址")
    # --- Oracle 原表恢复字段 ---
    startdate = db.Column(db.DateTime, comment="开始日期")
