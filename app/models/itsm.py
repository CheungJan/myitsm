"""
ITSM 业务模型。

阶段2：补全主表业务字段 + 新增子表/公用附表/字典表。

对应数据库表：
  字典表：TIT01, TIT02, TIT03, TIT04, TIT05, TIT06
  日常维护：TIT10 系列（主表 + LIABILITY + TRACK + POS_DETAIL + ATTC + ARCHIVE）
  新机开通：TIT13 + TIT14
  旧机翻新：TIT15（主表 + EQUIPMENT）
  设备变更：TIT16
  日常保养：TIT17（主表 + CUST_POS_DAILY + PLAN）
  门店关闭：TIT18
  配件选取：TIT19
  分派：TIT21
  上门服务：TIT23（公用）
  回访：TIT24（公用）
  配件更新：TIT25
  收费：TIT26
  关单：TIT27
  免费更换：TIT28 + DT
  未关单跟踪：TIT29

主子表关系参见 AGENTS.md「ITSM业务表结构约定」。
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel

# ---------------------------------------------------------------------------
# ITSM 字典/配置表
# ---------------------------------------------------------------------------


class TimepointArea(BaseModel):
    """合约响应时间-区域等级（TIT01_TIMEPOINT_AREA）。"""

    __tablename__ = "tit01_timepoint_area"

    levels = db.Column(db.String(2), primary_key=True, comment="响应等级")
    explain = db.Column(db.String(20), comment="说明")
    timepoint = db.Column(db.DateTime, comment="时间点")
    before_tm = db.Column(db.Numeric(5, 2), comment="时间点前（小时）")
    after_tm = db.Column(db.Numeric(5, 2), comment="时间点后（小时）")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")


class LiabilityReg(BaseModel):
    """免责条例字典（TIT02_LIABILITYREG）。"""

    __tablename__ = "tit02_liabilityreg"

    liab_cd = db.Column(db.String(4), primary_key=True, comment="科目编码")
    liab_nm = db.Column(db.String(20), comment="科目名称")
    describe = db.Column(db.String(200), comment="描述")
    liab_type = db.Column(db.String(1), comment="分类")
    parent = db.Column(db.String(4), comment="上级编码")
    child_flg = db.Column(db.String(1), comment="子类别标志")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")

    details = db.relationship("LiabilityRegDt", back_populates="liability", lazy="dynamic")


class LiabilityRegDt(BaseModel):
    """免责条例明细（TIT02_LIABILITYREGDT）。"""

    __tablename__ = "tit02_liabilityregdt"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lbdt_cd = db.Column(db.String(8), nullable=False, comment="明细编码")
    liab_cd = db.Column(
        db.String(8),
        db.ForeignKey("tit02_liabilityreg.liab_cd"),
        nullable=False,
        comment="科目编码",
    )
    define = db.Column(db.String(200), comment="明细定义")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")

    liability = db.relationship("LiabilityReg", back_populates="details")

    __table_args__ = (db.UniqueConstraint("lbdt_cd", "liab_cd", name="uq_liabilityregdt"),)


class ItsmSysCode(BaseModel):
    """ITSM 字典表（TIT03_SYSCODES）。"""

    __tablename__ = "tit03_syscodes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code_typ = db.Column(db.String(2), nullable=False, comment="类型")
    code_cd = db.Column(db.String(2), nullable=False, comment="编码")
    code_nm = db.Column(db.String(20), comment="名称")
    memo = db.Column(db.String(60), comment="备注")
    sys_flg = db.Column(db.String(1), comment="系统标记")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")

    __table_args__ = (db.UniqueConstraint("code_typ", "code_cd", name="uq_itsm_syscode"),)


class ArchiveCode(BaseModel):
    """维护单归档字典（TIT04_ARCHIVECODE）。"""

    __tablename__ = "tit04_archivecode"

    arch_cd = db.Column(db.String(10), primary_key=True, comment="科目编码")
    arch_nm = db.Column(db.String(60), comment="科目名称")
    describe = db.Column(db.String(200), comment="描述")
    arch_type = db.Column(db.String(1), comment="分类")
    parent = db.Column(db.String(10), comment="上级编码")
    child_flg = db.Column(db.String(1), comment="子类别标志")
    max_level = db.Column(db.Integer, comment="最大级次")
    arch_group = db.Column(db.String(1), comment="故障分组")
    fault_type = db.Column(db.String(10), comment="故障类型")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")


class RepairInfo(BaseModel):
    """ITSM 返修范围维护（TIT05_REPAIRINFO）。"""

    __tablename__ = "tit05_repairinfo"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rep_type = db.Column(db.String(2), nullable=False, comment="类型（01客户/02配件）")
    obj_cd = db.Column(db.String(8), nullable=False, comment="对象编号")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")

    __table_args__ = (db.UniqueConstraint("rep_type", "obj_cd", name="uq_repairinfo"),)


class UserArea(BaseModel):
    """ITSM 区域人员（TIT06_USERAREA）。"""

    __tablename__ = "tit06_userarea"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    area_id = db.Column(db.Integer, nullable=False, comment="区域ID")
    user_cd = db.Column(db.String(6), nullable=False, comment="人员编号")

    __table_args__ = (db.UniqueConstraint("area_id", "user_cd", name="uq_userarea"),)


# ---------------------------------------------------------------------------
# TIT10 日常维护单（主表 + 子表 + 附表）
# ---------------------------------------------------------------------------


class MaintenanceDaily(BaseModel):
    """
    日常维护单主表（TIT10_MAINTENANCEDAY）。

    CURRENT_STATUS 状态码：
        00=草稿, 01=已计划, 04=已派工, 02=实施中, 05=已完成, 09=已取消
    """

    __tablename__ = "tit10_maintenanceday"

    maintenance_id = db.Column(db.String(8), primary_key=True, comment="维护单号")
    company_id = db.Column(db.String(8), comment="所属区域公司ID")
    store_id = db.Column(db.String(8), comment="门店ID")
    temp_contract = db.Column(db.String(60), comment="临时联系电话")
    fault_type = db.Column(db.String(8), comment="故障类型")
    servrity = db.Column(db.String(1), comment="严重程度")
    emergency_level = db.Column(db.String(1), comment="紧急程度")
    priority = db.Column(db.String(1), comment="优先级")
    requester = db.Column(db.String(6), comment="请求人员")
    request_time = db.Column(db.DateTime, comment="请求时间")
    expected_completion_time = db.Column(db.DateTime, comment="合同要求完成时间")
    deliver_no = db.Column(db.String(8), comment="送货单号")
    short_description = db.Column(db.String(80), comment="故障简述")
    detail_description = db.Column(db.String(200), comment="详细描述")
    device_id = db.Column(db.String(13), comment="故障设备编号")
    current_status = db.Column(db.String(2), default="00", comment="当前状态")
    is_success = db.Column(db.String(1), comment="成功标志")
    is_old = db.Column(db.String(1), comment="是否补单")
    faultcode = db.Column(db.String(80), comment="故障编码")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")
    firstor = db.Column(db.String(6), comment="第一次上门工程师ID")
    first_time = db.Column(db.DateTime, comment="第一次上门时间")
    leave_time = db.Column(db.DateTime, comment="第一次离店时间")
    close_time = db.Column(db.DateTime, comment="关单时间")
    revisit_time = db.Column(db.DateTime, comment="回访时间")
    is_archive = db.Column(db.String(1), comment="是否归档")
    view_type = db.Column(db.String(1), comment="视频操作类型")
    memo = db.Column(db.String(200), comment="异常状态备注")
    requst_typ = db.Column(db.String(10), comment="请求类型")
    requset_paper_id = db.Column(db.String(10), comment="请求单号")
    # P0-1 优化字段
    source_type = db.Column(
        db.String(10),
        comment="来源类型（DAILY=日常维护/RECYCLE=取机回收）",
    )

    tracks = db.relationship("MaintenanceDailyTrack", back_populates="maintenance", lazy="dynamic")
    pos_details = db.relationship("PosDetail", back_populates="maintenance", lazy="dynamic")
    liabilities = db.relationship(
        "MaintenanceLiability", back_populates="maintenance", lazy="dynamic"
    )
    archives = db.relationship("MaintenanceArchive", back_populates="maintenance", lazy="dynamic")


class MaintenanceLiability(BaseModel):
    """单据豁免信息表（TIT10_MAINTENANCE_LIABILITY）。"""

    __tablename__ = "tit10_maintenance_liability"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    maintenance_id = db.Column(
        db.String(8),
        db.ForeignKey("tit10_maintenanceday.maintenance_id"),
        nullable=False,
        comment="维护单ID",
    )
    exceptions_cd = db.Column(db.String(10), comment="免责条款编码")
    exceptions_nm = db.Column(db.String(200), comment="条款名称")
    dept_nm = db.Column(db.String(20), comment="审核部门")
    assess_flg = db.Column(db.String(1), comment="是否考核")
    exempt_flg = db.Column(db.String(1), comment="是否豁免")
    type = db.Column(db.String(1), comment="类型（1未完成/2未达标）")
    is_finish = db.Column(db.String(1), comment="处理状态（0未处理/1已分配/2已处理/3已审核）")
    useflg = db.Column(db.String(1), default="1", comment="有效标记")
    set_from = db.Column(db.String(10), comment="来源")

    maintenance = db.relationship("MaintenanceDaily", back_populates="liabilities")


class MaintenanceDailyTrack(BaseModel):
    """日常维护单状态变更轨迹（TIT10_MAIN_TRACK）。"""

    __tablename__ = "tit10_main_track"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    maintenance_id = db.Column(
        db.String(8),
        db.ForeignKey("tit10_maintenanceday.maintenance_id"),
        nullable=False,
        comment="维护单ID",
    )
    dep_cd = db.Column(db.String(8), comment="部门编码")
    memo = db.Column(db.String(255), comment="备注")
    updatetime = db.Column(db.DateTime, comment="更新时间")
    # 状态机增强字段
    from_status = db.Column(db.String(2), comment="原状态")
    to_status = db.Column(db.String(2), comment="目标状态")
    oper_cd = db.Column(db.String(20), comment="操作员")

    maintenance = db.relationship("MaintenanceDaily", back_populates="tracks")


class PosDetail(BaseModel):
    """维护单换机配件明细（TIT10_POS_DETAIL）。"""

    __tablename__ = "tit10_pos_detail"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bill_id = db.Column(
        db.String(8),
        db.ForeignKey("tit10_maintenanceday.maintenance_id"),
        nullable=False,
        comment="单据编号",
    )
    sm_id = db.Column(db.Integer, comment="SM表ID")
    noflg = db.Column(db.String(1), comment="新旧设备标记")
    device_id = db.Column(db.String(13), comment="整机ID")
    item_cd = db.Column(db.String(6), comment="配件类型")
    accessories_id = db.Column(db.String(13), comment="配件编号")
    status = db.Column(db.String(1), comment="状态")

    maintenance = db.relationship("MaintenanceDaily", back_populates="pos_details")


class MaintenanceAttc(BaseModel):
    """日常维护单附表-备用（TIT11_MAINTENANCE_ATTC）。"""

    __tablename__ = "tit11_maintenance_attc"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    maintenance_id = db.Column(db.String(8), nullable=False, comment="维护单ID")
    business_operation_id = db.Column(db.Integer, comment="业务流水操作表ID")
    attc_id = db.Column(db.String(8), comment="附件ID")
    attc_nm = db.Column(db.String(40), comment="附件名称")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")


class MaintenanceArchive(BaseModel):
    """日常维护归档表（TIT12_MAINTENANCE_ARCHIVE）。"""

    __tablename__ = "tit12_maintenance_archive"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    maintenance_id = db.Column(
        db.String(8),
        db.ForeignKey("tit10_maintenanceday.maintenance_id"),
        nullable=False,
        comment="维护单ID",
    )
    business_operation_id = db.Column(db.Integer, comment="业务流水操作表ID")
    fault_cd = db.Column(db.String(10), comment="故障编码")
    fault_cd_audit = db.Column(db.String(10), comment="故障编码（审核后）")
    fault_type = db.Column(db.String(10), comment="故障大类")
    fault_detail_type = db.Column(db.String(10), comment="故障小类")
    description = db.Column(db.String(200), comment="描述")
    useflg = db.Column(db.String(1), default="1", comment="有效标记")
    is_audit = db.Column(db.String(1), comment="审核标记")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")

    maintenance = db.relationship("MaintenanceDaily", back_populates="archives")


# ---------------------------------------------------------------------------
# TIT13 新机开通单
# ---------------------------------------------------------------------------


class MaintenanceOpen(BaseModel):
    """新机开通维护单表（TIT13_MAINTENANCE_OPEN）。"""

    __tablename__ = "tit13_maintenance_open"

    new_opening_id = db.Column(db.String(8), primary_key=True, comment="新机开通表ID")
    company_id = db.Column(db.String(8), comment="所属区域公司ID")
    store_id = db.Column(db.String(8), comment="门店ID")
    request_time = db.Column(db.DateTime, comment="请求时间")
    requset_paper_id = db.Column(db.String(8), comment="仓储请求单ID")
    device_id = db.Column(db.String(13), comment="整机编号")
    count = db.Column(db.Integer, comment="开通数量")
    expected_completion_time = db.Column(db.DateTime, comment="合同要求完成时间")
    deliver_no = db.Column(db.String(8), comment="送货单号")
    short_description = db.Column(db.String(80), comment="简述")
    detail_description = db.Column(db.String(200), comment="详细描述")
    current_status = db.Column(db.String(2), default="00", comment="当前状态")
    is_success = db.Column(db.String(1), comment="成功标志")
    is_old = db.Column(db.String(1), comment="是否补单")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")
    firstor = db.Column(db.String(6), comment="第一次上门工程师ID")
    first_time = db.Column(db.DateTime, comment="第一次上门时间")
    leave_time = db.Column(db.DateTime, comment="第一次离店时间")
    close_time = db.Column(db.DateTime, comment="关单时间")
    revisit_time = db.Column(db.DateTime, comment="回访时间")
    from_custcard = db.Column(db.String(20), comment="来源磁卡号")
    from_custcd = db.Column(db.String(8), comment="来源客户编码")

    equipments = db.relationship("EquipmentOpen", back_populates="opening", lazy="dynamic")


class EquipmentOpen(BaseModel):
    """新机开通设备附表（TIT14_EQUIPMENT_OPEN）。"""

    __tablename__ = "tit14_equipment_open"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    new_opening_id = db.Column(
        db.String(8),
        db.ForeignKey("tit13_maintenance_open.new_opening_id"),
        nullable=False,
        comment="新机开通ID",
    )
    business_operation_id = db.Column(db.Integer, comment="业务流水操作表ID")
    device_id = db.Column(db.String(13), comment="整机ID")
    price = db.Column(db.Numeric(5, 3), comment="价格")
    delivery_id = db.Column(db.String(8), comment="送货单号")
    is_finish = db.Column(db.String(1), comment="是否完成")
    is_change = db.Column(db.String(1), comment="是否换机")
    change_eid = db.Column(db.String(50), comment="换机设备号")
    from_custcard = db.Column(db.String(20), comment="来源磁卡号")
    from_posid = db.Column(db.String(13), comment="来源POS编号")
    from_custcd = db.Column(db.String(8), comment="来源客户编码")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")

    opening = db.relationship("MaintenanceOpen", back_populates="equipments")


# ---------------------------------------------------------------------------
# TIT15 旧机翻新单
# ---------------------------------------------------------------------------


class MaintenanceRenovate(BaseModel):
    """旧机翻新维护单（TIT15_MAINTENANCE_RENOVATE）。"""

    __tablename__ = "tit15_maintenance_renovate"

    renew_id = db.Column(db.String(8), primary_key=True, comment="旧机翻新表ID")
    company_id = db.Column(db.String(8), comment="所属区域公司ID")
    store_id = db.Column(db.String(8), comment="门店ID")
    request_time = db.Column(db.DateTime, comment="请求时间")
    requset_paper_id = db.Column(db.String(8), comment="仓储请求单ID")
    old_device_id = db.Column(db.String(13), comment="旧设备编号")
    new_device_id = db.Column(db.String(13), comment="换新设备编号")
    count = db.Column(db.Integer, comment="变更数量")
    expected_completion_time = db.Column(db.DateTime, comment="合同要求完成时间")
    deliver_no = db.Column(db.String(8), comment="送货单号")
    short_description = db.Column(db.String(80), comment="简述")
    detail_description = db.Column(db.String(200), comment="详细描述")
    current_status = db.Column(db.String(2), default="00", comment="当前状态")
    is_success = db.Column(db.String(1), comment="成功标志")
    is_old = db.Column(db.String(1), comment="是否补单")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")
    firstor = db.Column(db.String(6), comment="第一次上门工程师ID")
    first_time = db.Column(db.DateTime, comment="第一次上门时间")
    leave_time = db.Column(db.DateTime, comment="第一次离店时间")
    close_time = db.Column(db.DateTime, comment="关单时间")
    revisit_time = db.Column(db.DateTime, comment="回访时间")
    is_back = db.Column(db.String(1), comment="设备是否返回（Y/N）")

    equipments = db.relationship("EquipmentRenovate", back_populates="renovate", lazy="dynamic")


class EquipmentRenovate(BaseModel):
    """旧机翻新设备附表（TIT15_EQUIPMENT_RENOVATE）。"""

    __tablename__ = "tit15_equipment_renovate"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    renovate_id = db.Column(
        db.String(8),
        db.ForeignKey("tit15_maintenance_renovate.renew_id"),
        nullable=False,
        comment="旧机翻新ID",
    )
    business_operation_id = db.Column(db.Integer, comment="业务流水操作表ID")
    device_id = db.Column(db.String(13), comment="旧机ID")
    new_device_id = db.Column(db.String(13), comment="新机ID")
    price = db.Column(db.Numeric(5, 3), comment="价格")
    delivery_id = db.Column(db.String(8), comment="送货单号")
    is_finish = db.Column(db.String(1), comment="是否完成")
    is_change = db.Column(db.String(1), comment="是否换机")
    change_eid = db.Column(db.String(50), comment="换机设备号")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")

    renovate = db.relationship("MaintenanceRenovate", back_populates="equipments")


# ---------------------------------------------------------------------------
# TIT16 设备变更单
# ---------------------------------------------------------------------------


class DeviceChange(BaseModel):
    """
    设备变更单（TIT16_DEVICE_CHANGE）。

    CHANGE_TYPE: CK=改磁卡号, BQ=信息变更, BG=设备变更
    """

    __tablename__ = "tit16_device_change"

    device_change_id = db.Column(db.String(8), primary_key=True, comment="变更单ID")
    store_id = db.Column(db.String(8), comment="门店ID")
    requset_paper_id = db.Column(db.String(8), comment="变更请求单ID")
    change_type = db.Column(db.String(8), comment="变更类型（CK/BQ/BG）")
    device_id = db.Column(db.String(13), comment="整机ID")
    new_contactor = db.Column(db.String(10), comment="变更后联系人")
    new_tel = db.Column(db.String(60), comment="变更后电话")
    new_address = db.Column(db.String(200), comment="变更后地址")
    new_store_card = db.Column(db.String(20), comment="变更后门店磁卡号")
    new_store_id = db.Column(db.String(8), comment="变更后门店ID")
    is_store_inside_change = db.Column(db.String(1), comment="是否店内移机（Y/N）")
    request_time = db.Column(db.DateTime, comment="请求时间")
    expected_completion_time = db.Column(db.DateTime, comment="合同要求完成时间")
    short_description = db.Column(db.String(80), comment="简述")
    detail_description = db.Column(db.String(200), comment="详细描述")
    current_status = db.Column(db.String(2), default="00", comment="当前状态")
    is_success = db.Column(db.String(1), comment="成功标志")
    is_old = db.Column(db.String(1), comment="是否补单")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")
    firstor = db.Column(db.String(6), comment="第一次上门工程师ID")
    first_time = db.Column(db.DateTime, comment="第一次上门时间")
    leave_time = db.Column(db.DateTime, comment="第一次离店时间")
    close_time = db.Column(db.DateTime, comment="关单时间")
    revisit_time = db.Column(db.DateTime, comment="回访时间")


# ---------------------------------------------------------------------------
# TIT17 日常保养单
# ---------------------------------------------------------------------------


class Maintenance(BaseModel):
    """日常保养单主表（TIT17_MAINTENANCE）。"""

    __tablename__ = "tit17_maintenance"

    daily_maintenance_id = db.Column(db.String(8), primary_key=True, comment="日常保养维护单ID")
    store_id = db.Column(db.String(8), comment="门店ID")
    has_video_device = db.Column(db.String(1), comment="是否有视频")
    video_device_status = db.Column(db.String(20), comment="视频状态")
    video_device_error_des = db.Column(db.String(200), comment="视频故障描述")
    request_enginner_id = db.Column(db.String(6), comment="请求工程师ID")
    request_time = db.Column(db.DateTime, comment="请求时间")
    short_description = db.Column(db.String(80), comment="简述")
    detail_description = db.Column(db.String(200), comment="详细描述")
    current_status = db.Column(db.String(2), default="00", comment="当前状态")
    is_success = db.Column(db.String(1), comment="成功标志")
    is_old = db.Column(db.String(1), comment="是否补单")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")
    firstor = db.Column(db.String(6), comment="第一次上门工程师ID")
    first_time = db.Column(db.DateTime, comment="第一次上门时间")
    leave_time = db.Column(db.DateTime, comment="第一次离店时间")
    close_time = db.Column(db.DateTime, comment="关单时间")
    revisit_time = db.Column(db.DateTime, comment="回访时间")

    pos_daily_items = db.relationship("CustPosDaily", back_populates="maintenance", lazy="dynamic")


class CustPosDaily(BaseModel):
    """保养设备明细（TIT17_CUST_POS_DAILY）。"""

    __tablename__ = "tit17_cust_pos_daily"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    daily_maintenance_id = db.Column(
        db.String(8),
        db.ForeignKey("tit17_maintenance.daily_maintenance_id"),
        nullable=False,
        comment="保养单号",
    )
    business_operation_id = db.Column(db.Integer, comment="业务操作流水ID")
    cust_cd = db.Column(db.String(8), comment="客户代码")
    eid = db.Column(db.String(13), comment="设备序列号")
    item_cd = db.Column(db.String(6), comment="机型")
    startdate = db.Column(db.DateTime, comment="开通日期")
    sysinfo = db.Column(db.String(30), comment="系统程序")
    softinfo = db.Column(db.String(30), comment="软件配置")
    posupddate = db.Column(db.DateTime, comment="设备更新时间")
    posinfo = db.Column(db.String(30), comment="POS版本")
    area = db.Column(db.String(2), comment="划区")
    status = db.Column(db.String(1), comment="设备状态（1在用/0备机）")
    typ_flg = db.Column(db.String(2), comment="类型（1.POS机/2.视频机）")
    maintenancedate = db.Column(db.DateTime, comment="保养时间")
    maintenancetyp = db.Column(db.String(6), comment="保养状态（1已保养/0未保养）")
    request_enginner_id = db.Column(db.String(6), comment="操作工程师")
    request_time = db.Column(db.DateTime, comment="请求时间")
    short_description = db.Column(db.String(80), comment="简述")
    detail_description = db.Column(db.String(200), comment="详细描述")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")

    maintenance = db.relationship("Maintenance", back_populates="pos_daily_items")


class MaintenancePlan(BaseModel):
    """保养计划表（TIT17_MAINTENANCE_PLAN）。"""

    __tablename__ = "tit17_maintenance_plan"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plan_y = db.Column(db.String(4), nullable=False, comment="计划年")
    plan_yymm = db.Column(db.String(6), nullable=False, comment="计划年月")
    area_id = db.Column(db.Integer, nullable=False, comment="区域")
    plan_qty = db.Column(db.Integer, comment="计划量")
    create_time = db.Column(db.DateTime, comment="创建日期")
    creator = db.Column(db.String(6), comment="创建人")

    __table_args__ = (
        db.UniqueConstraint("plan_y", "plan_yymm", "area_id", name="uq_maintenance_plan"),
    )


# ---------------------------------------------------------------------------
# TIT18 门店关闭
# ---------------------------------------------------------------------------


class StoreClose(BaseModel):
    """门店关闭表（TIT18_STORE_CLOSE）。"""

    __tablename__ = "tit18_store_close"

    store_close_id = db.Column(db.String(8), primary_key=True, comment="门店关闭单ID")
    store_id = db.Column(db.String(8), comment="门店ID")
    request_time = db.Column(db.DateTime, comment="请求时间")
    requset_paper_id = db.Column(db.String(8), comment="请求单号")
    close_type = db.Column(db.String(2), comment="关闭类型")
    temp_close_date_begin = db.Column(db.DateTime, comment="临时关闭开始时间")
    temp_close_date_end = db.Column(db.DateTime, comment="临时关闭结束时间")
    expected_completion_time = db.Column(db.DateTime, comment="要求完成时间")
    short_description = db.Column(db.String(80), comment="简述")
    detail_description = db.Column(db.String(200), comment="详细描述")
    current_status = db.Column(db.String(2), default="00", comment="当前状态")
    is_success = db.Column(db.String(1), comment="成功标志")
    is_old = db.Column(db.String(1), comment="是否补单")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")
    firstor = db.Column(db.String(6), comment="第一次上门工程师ID")
    first_time = db.Column(db.DateTime, comment="第一次上门时间")
    leave_time = db.Column(db.DateTime, comment="第一次离店时间")
    close_time = db.Column(db.DateTime, comment="关单时间")
    revisit_time = db.Column(db.DateTime, comment="回访时间")


# ---------------------------------------------------------------------------
# TIT19 配件选取明细
# ---------------------------------------------------------------------------


class OnChooseDt(BaseModel):
    """新旧配件选取明细（TIT19_ON_CHOOSEDT）。"""

    __tablename__ = "tit19_on_choosedt"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bill_id = db.Column(db.String(8), nullable=False, comment="单据编号")
    business_id = db.Column(db.Integer, comment="设备操作流水")
    oldflg = db.Column(db.String(1), comment="新旧设备标记")
    device_id = db.Column(db.String(13), comment="整机ID")
    item_cd = db.Column(db.String(6), comment="配件类型")
    accessories_id = db.Column(db.String(13), comment="配件编号")
    chooseflg = db.Column(db.String(1), comment="选取标记")
    updateflg = db.Column(db.String(1), comment="是否提交")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")


# ---------------------------------------------------------------------------
# TIT21 维护单分派
# ---------------------------------------------------------------------------


class MaintenanceDispatch(BaseModel):
    """维护单分派表（TIT21_MAINTENANCE_DISPATCH）。"""

    __tablename__ = "tit21_maintenance_dispatch"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    maintenance_id = db.Column(db.String(8), nullable=False, comment="维护单ID")
    business_operation_id = db.Column(db.Integer, comment="业务操作流水表ID")
    maintenance_type = db.Column(db.String(2), comment="维护类型")
    operator = db.Column(db.String(6), comment="操作人")
    accpectd_group = db.Column(db.String(2), comment="分派组")
    accpectder = db.Column(db.String(6), comment="分派人")
    dispatch_time = db.Column(db.DateTime, comment="分派时间")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")


# ---------------------------------------------------------------------------
# TIT23 上门服务记录（公用附表）
# ---------------------------------------------------------------------------


class MaintenanceD2D(BaseModel):
    """
    维护单上门服务表（TIT23_MAINTENANCE_D2D）。

    跨单据复用：日常维护(MD)/新机开通(MO)/旧机翻新(MR)/保养(BY)/设备变更(BG) 均使用。
    """

    __tablename__ = "tit23_maintenance_d2d"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    maintenance_id = db.Column(db.String(8), nullable=False, comment="维护单ID（跨单据复用）")
    business_operation_id = db.Column(db.Integer, comment="业务操作流水表ID")
    d2d_engineer = db.Column(db.String(6), comment="上门工程师")
    arrive_time = db.Column(db.DateTime, comment="到达时间")
    leave_time = db.Column(db.DateTime, comment="离店时间")
    jjbz = db.Column(db.String(1), comment="解决标志")
    d2d_descripiton = db.Column(db.String(200), comment="处理过程描述")
    d2d_phone = db.Column(db.String(60), comment="电话")
    old_business_id = db.Column(db.Integer, comment="原操作流水ID")
    d2d_group = db.Column(db.Integer, comment="分组")
    d2d_type = db.Column(db.String(1), comment="类型（1到店/2离店/3催单/4记录）")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    posstatus = db.Column(db.String(2), comment="POS状态")
    posstatus1 = db.Column(db.String(2), comment="POS状态1")


# ---------------------------------------------------------------------------
# TIT24 客户回访记录（公用附表）
# ---------------------------------------------------------------------------


class MaintenanceRV(BaseModel):
    """维护单客户回访表（TIT24_MAINTENANCE_RV）。"""

    __tablename__ = "tit24_maintenance_rv"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    maintenance_id = db.Column(db.String(8), nullable=False, comment="维护单ID")
    business_operation_id = db.Column(db.Integer, comment="业务操作流水表ID")
    rv_time = db.Column(db.DateTime, comment="回访时间")
    rv_operator = db.Column(db.String(20), comment="回访人员")
    feedback = db.Column(db.String(200), comment="客户反馈")
    satisfaction = db.Column(db.String(1), comment="满意度")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")


# ---------------------------------------------------------------------------
# TIT25 配件更新记录
# ---------------------------------------------------------------------------


class AccessoriesUpdate(BaseModel):
    """配件更新表（TIT25_ACCESSORIES_UPDATE）。"""

    __tablename__ = "tit25_accessories_update"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    maintenance_id = db.Column(db.String(8), nullable=False, comment="维修单ID")
    business_operation_id = db.Column(db.Integer, comment="业务流水操作表ID")
    store_id = db.Column(db.String(8), comment="门店ID")
    device_id = db.Column(db.String(13), comment="整机ID")
    old_accessories_id = db.Column(db.String(13), comment="旧配件ID")
    accessories_type = db.Column(db.String(60), comment="配件类型名称")
    new_accessories_id = db.Column(db.String(13), comment="新配件ID")
    is_new = db.Column(db.String(1), comment="新配件是否为新品")
    description = db.Column(db.String(200), comment="过程描述")
    price = db.Column(db.Numeric(10, 3), comment="价格")
    engineer_id = db.Column(db.String(6), comment="工程师ID")
    in_wh = db.Column(db.String(1), comment="是否入库")
    invflg = db.Column(db.String(1), comment="是否开票")
    receipt_id = db.Column(db.String(8), comment="收据号")
    delivery_id = db.Column(db.String(8), comment="送货单号")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")
    auditflg = db.Column(db.String(1), comment="提交标志")
    posflg = db.Column(db.String(1), comment="更换整机标志")
    c_type = db.Column(db.String(1), comment="操作类型（1维修/2购买）")


# ---------------------------------------------------------------------------
# TIT26 单据收费记录
# ---------------------------------------------------------------------------


class PayList(BaseModel):
    """单据收费记录表（TIT26_PAYLIST）。"""

    __tablename__ = "tit26_paylist"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    maintenance_id = db.Column(db.String(8), nullable=False, comment="维修单ID")
    business_operation_id = db.Column(db.Integer, comment="业务流水操作表ID")
    store_id = db.Column(db.String(8), comment="门店ID")
    engineer_id = db.Column(db.String(6), comment="工程师ID")
    receipt_id = db.Column(db.String(8), comment="收据号")
    delivery_id = db.Column(db.String(8), comment="送货单号")
    paytype = db.Column(db.String(30), comment="收费类型")
    payje = db.Column(db.Numeric(8, 3), comment="收款金额")
    memo = db.Column(db.String(250), comment="备注")
    paydate = db.Column(db.DateTime, comment="收款日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标记")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")


# ---------------------------------------------------------------------------
# TIT27 关单记录
# ---------------------------------------------------------------------------


class CloseBills(BaseModel):
    """关单表（TIT27_CLOSE_BILLS）。"""

    __tablename__ = "tit27_close_bills"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    maintenance_id = db.Column(db.String(8), nullable=False, comment="任务单ID")
    business_operation_id = db.Column(db.Integer, comment="业务操作流水表ID")
    close_time = db.Column(db.DateTime, comment="关单时间")
    close_type = db.Column(db.String(2), comment="关单类型")
    description = db.Column(db.String(200), comment="描述")
    is_old = db.Column(db.String(1), comment="是否补关单")
    is_archive = db.Column(db.String(1), comment="是否归档")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")


# ---------------------------------------------------------------------------
# TIT28 免费更换维护单
# ---------------------------------------------------------------------------


class FreeReplace(BaseModel):
    """免费更换维护单（TIT28_FREE_REPLACE）。"""

    __tablename__ = "tit28_free_replace"

    renew_id = db.Column(db.String(8), primary_key=True, comment="免费更换表ID")
    company_id = db.Column(db.String(8), comment="所属区域公司ID")
    store_id = db.Column(db.String(8), comment="门店ID")
    request_time = db.Column(db.DateTime, comment="请求时间")
    requset_paper_id = db.Column(db.String(8), comment="请求ID")
    old_device_id = db.Column(db.String(13), comment="旧设备编号")
    new_device_id = db.Column(db.String(13), comment="换新设备编号")
    deliver_no = db.Column(db.String(8), comment="送货单号")
    count = db.Column(db.Integer, comment="变更数量")
    expected_completion_time = db.Column(db.DateTime, comment="合同要求完成时间")
    short_description = db.Column(db.String(80), comment="简述")
    detail_description = db.Column(db.String(200), comment="详细描述")
    current_status = db.Column(db.String(2), default="00", comment="当前状态")
    is_success = db.Column(db.String(1), comment="成功标志")
    is_old = db.Column(db.String(1), comment="是否补单")
    is_back = db.Column(db.String(1), comment="设备是否返回（Y/N）")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")
    firstor = db.Column(db.String(6), comment="第一次上门工程师ID")
    first_time = db.Column(db.DateTime, comment="第一次上门时间")
    leave_time = db.Column(db.DateTime, comment="第一次离店时间")
    close_time = db.Column(db.DateTime, comment="关单时间")
    revisit_time = db.Column(db.DateTime, comment="回访时间")

    equipments = db.relationship("FreeReplaceDt", back_populates="free_replace", lazy="dynamic")


class FreeReplaceDt(BaseModel):
    """免费更换设备附表（TIT28_FREE_REPLACE_DT）。"""

    __tablename__ = "tit28_free_replace_dt"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    renovate_id = db.Column(
        db.String(8),
        db.ForeignKey("tit28_free_replace.renew_id"),
        nullable=False,
        comment="免费更换ID",
    )
    business_operation_id = db.Column(db.Integer, comment="业务流水操作表ID")
    device_id = db.Column(db.String(13), comment="旧机ID")
    new_device_id = db.Column(db.String(13), comment="新机ID")
    delivery_id = db.Column(db.String(8), comment="送货单号")
    is_finish = db.Column(db.String(1), comment="是否完成")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")

    free_replace = db.relationship("FreeReplace", back_populates="equipments")


# ---------------------------------------------------------------------------
# TIT29 未关单跟踪
# ---------------------------------------------------------------------------


class NoCloseTrack(BaseModel):
    """未关单跟踪（TIT29_NOCLOSE_TRACK）。"""

    __tablename__ = "tit29_noclose_track"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    maintenance_id = db.Column(db.String(8), nullable=False, comment="维护单号")
    idnum = db.Column(db.Integer, comment="编号")
    dispos_dept = db.Column(db.String(20), comment="处理部门")
    cause_main = db.Column(db.String(20), comment="原因大类")
    cause_detail = db.Column(db.String(20), comment="原因小类")
    cause_memo = db.Column(db.String(200), comment="原因说明")
    description = db.Column(db.String(250), comment="详情")
    feedback = db.Column(db.String(200), comment="部门反馈")
    create_time = db.Column(db.DateTime, comment="创建时间")
    creator = db.Column(db.String(6), comment="创建人")
    update_time = db.Column(db.DateTime, comment="更新时间")
    updator = db.Column(db.String(6), comment="更新人")
