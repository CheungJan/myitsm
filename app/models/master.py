"""
主数据模型。

对应数据库表：TMM01_COMPANY, TMM11_ITEMCLASS, TMM12_ITEMS,
TMM18_SUPPLIERCLASS, TMM19_SUPPLIERS, TMM21_CUSTCLASS,
TMM22_CUSTOMERS, TMM31_SYSCODES, TMM34_IDMASTER,
TMM35_CUST_POS_RL, TMM46_AREA, TMM47_COMMODE
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel


class Company(BaseModel):
    """公司表（TMM01_COMPANY）。"""

    __tablename__ = "tmm01_company"

    comp_cd = db.Column(db.String(20), primary_key=True, comment="公司编码")
    comp_nm = db.Column(db.String(100), nullable=False, comment="公司名称")
    address = db.Column(db.String(200), comment="地址")
    phone = db.Column(db.String(30), comment="电话")
    # --- 以下为 Oracle 原表恢复字段 ---
    leader = db.Column(db.String(10), comment="负责人")
    telex = db.Column(db.String(20), comment="电传号")
    faxno = db.Column(db.String(20), comment="传真")
    banknm = db.Column(db.String(30), comment="开户银行")
    bankaccno = db.Column(db.String(20), comment="银行账号")
    taxno = db.Column(db.String(18), comment="税号")
    opendate = db.Column(db.DateTime, comment="开业日期")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    mailcd = db.Column(db.String(6), comment="邮编")
    produce = db.Column(db.Integer, comment="生产标志")
    maintenance = db.Column(db.Integer, comment="维护标志")


class Area(BaseModel):
    """区域表（TMM46_AREA）。"""

    __tablename__ = "tmm46_area"

    area_cd = db.Column(db.String(20), primary_key=True, comment="区域编码")
    area_nm = db.Column(db.String(50), nullable=False, comment="区域名称")
    parent_cd = db.Column(db.String(20), comment="上级区域")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    # --- Oracle 原表恢复字段 ---
    area_id = db.Column(db.Integer, comment="区域ID")
    name = db.Column(db.String(50), comment="区域全称")
    usercd = db.Column(db.String(6), comment="负责人编码")


class ComMode(BaseModel):
    """通讯方式表（TMM47_COMMODE）。"""

    __tablename__ = "tmm47_commode"

    cmm_cd = db.Column(db.String(20), primary_key=True, comment="通讯方式编码")
    cmm_nm = db.Column(db.String(50), nullable=False, comment="通讯方式名称")
    cmm_type = db.Column(db.String(10), comment="类型")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    # --- Oracle 原表恢复字段 ---
    parent = db.Column(db.String(20), comment="上级编码")
    childflg = db.Column(db.String(1), comment="子节点标志")


class CustClass(BaseModel):
    """客户分类表（TMM21_CUSTCLASS）。"""

    __tablename__ = "tmm21_custclass"

    class_cd = db.Column(db.String(20), primary_key=True, comment="分类编码")
    class_nm = db.Column(db.String(50), nullable=False, comment="分类名称")
    parent_cd = db.Column(db.String(20), comment="上级分类")
    # --- Oracle 原表恢复字段 ---
    classtyp = db.Column(db.String(1), comment="分类类型")
    childflg = db.Column(db.String(1), comment="子节点标志")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")


class Customer(BaseModel):
    """
    客户/门店主表（TMM22_CUSTOMERS）。

    优化方案3：新增 customer_status 字段实现客户生命周期管理。
    原系统缺陷：预计划创建的客户直接写入主表，取消后无标记变为"幽灵数据"。
    """

    __tablename__ = "tmm22_customers"

    cust_cd = db.Column(db.String(20), primary_key=True, comment="客户编码")
    cust_nm = db.Column(db.String(100), nullable=False, comment="客户名称")
    cust_card = db.Column(db.String(30), unique=True, comment="磁卡号")
    class_cd = db.Column(db.String(20), comment="客户分类")
    area_cd = db.Column(db.String(20), comment="区域编码")
    address = db.Column(db.String(200), comment="地址")
    phone_no = db.Column(db.String(30), comment="电话")
    contactor = db.Column(db.String(50), comment="联系人")
    busi_typ = db.Column(db.String(10), comment="业务类型")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    # 优化字段：客户生命周期状态
    customer_status = db.Column(
        db.String(10),
        default="ACTIVE",
        comment="生命周期状态（TEMP/PENDING/ACTIVE/INVALID）",
    )
    ppt_code = db.Column(db.String(20), comment="品牌编码")
    zf_type = db.Column(db.String(10), comment="支付方式")
    comm_mode = db.Column(db.String(20), comment="通讯方式")
    store_cd = db.Column(db.String(30), comment="门店编码")
    # --- Oracle 原表恢复字段（31个） ---
    cust_anm = db.Column(db.String(40), comment="客户别名")
    cust_brcd = db.Column(db.String(20), comment="客户条码")
    zipcd = db.Column(db.String(6), comment="邮编")
    faxno = db.Column(db.String(20), comment="传真")
    taxno = db.Column(db.String(18), comment="税号")
    banknm = db.Column(db.String(40), comment="开户银行")
    bankaccno = db.Column(db.String(50), comment="银行账号")
    parentcd = db.Column(db.String(8), comment="上级客户编码")
    backup = db.Column(db.String(200), comment="备注")
    location = db.Column(db.String(1), comment="位置标志")
    area = db.Column(db.Integer, comment="区域编号")
    pos_n = db.Column(db.Integer, comment="POS数量")
    opersystem = db.Column(db.String(128), comment="POS操作系统")
    data_base = db.Column(db.String(128), comment="POS数据库版本")
    soft_edition = db.Column(db.String(128), comment="POS软件版本")
    s_status = db.Column(db.String(1), comment="状态标志")
    ad_video = db.Column(db.String(1), comment="广告机标志")
    card3g = db.Column(db.String(30), comment="3G卡号")
    adr3g = db.Column(db.String(20), comment="3G地址")
    systemcode = db.Column(db.String(50), comment="内核版本")
    custrnm = db.Column(db.String(80), comment="客户全称")
    opendate = db.Column(db.DateTime, comment="首次开通日期")
    replacedate = db.Column(db.DateTime, comment="最近更换日期")
    levels = db.Column(db.String(2), comment="客户等级")
    ordertype = db.Column(db.String(10), comment="要货方式")
    jl_contactor = db.Column(db.String(10), comment="经理联系人")
    jl_phoneno = db.Column(db.String(60), comment="经理电话")
    posstatus = db.Column(db.String(2), comment="POS运行状态")
    posstatus1 = db.Column(db.String(2), comment="POS状态1")
    is_contract = db.Column(db.String(2), comment="合同标志")
    yj_money = db.Column(db.Numeric(12, 2), comment="押金金额")
    # --- 优化方案1 未落地字段（4个） ---
    source_type = db.Column(db.String(20), comment="来源类型（PREPLAN/MANUAL/IMPORT/API）")
    verified_at = db.Column(db.DateTime, comment="转正时间")
    preplan_id = db.Column(db.String(50), comment="关联预计划号")
    valid_until = db.Column(db.DateTime, comment="临时客户有效期")

    positions = db.relationship("CustPosRl", back_populates="customer", lazy="dynamic")


class CustomerHistory(BaseModel):
    """
    客户变更历史表（TMM22_CUSTOMERS_HISTORY）。

    优化方案4：磁卡号变更前保存历史记录。
    原系统缺陷：CHANGE_TYPE='CK'时直接覆盖旧磁卡号，历史不可追溯。
    """

    __tablename__ = "tmm22_customers_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cust_cd = db.Column(db.String(20), nullable=False, comment="客户编码")
    change_type = db.Column(db.String(10), nullable=False, comment="变更类型（CK=磁卡号）")
    old_value = db.Column(db.String(200), comment="变更前值")
    new_value = db.Column(db.String(200), comment="变更后值")
    oper_cd = db.Column(db.String(20), comment="操作员")
    oper_date = db.Column(db.DateTime, comment="操作时间")
    # --- 优化方案3 未落地字段（2个） ---
    change_reason = db.Column(db.String(200), comment="变更原因")
    device_change_id = db.Column(db.String(20), comment="关联变更单号")


class CustPosRl(BaseModel):
    """
    门店设备关联表（TMM35_CUST_POS_RL）。

    优化方案2：扩展资产属性字段。
    原系统缺陷：缺少资产类型、回收状态等关键字段。
    """

    __tablename__ = "tmm35_cust_pos_rl"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cust_cd = db.Column(
        db.String(20), db.ForeignKey("tmm22_customers.cust_cd"), nullable=False, comment="客户编码"
    )
    pos_cd = db.Column(db.String(30), comment="POS编码")
    item_cd = db.Column(db.String(20), comment="物料编码")
    eid = db.Column(db.String(50), comment="设备序列号")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    # 优化字段：资产属性扩展
    asset_type = db.Column(
        db.String(10),
        default="NEW",
        comment="资产类型（NEW=新机/USED=旧机/REFURB=翻新机/SCRAP=报废）",
    )
    recyclable = db.Column(db.Boolean, default=False, comment="可回收标志")
    recycle_status = db.Column(
        db.String(10),
        comment="回收状态（PENDING/RECYCLED/SCRAPPED）",
    )
    install_date = db.Column(db.DateTime, comment="安装日期")
    # --- Oracle 原表恢复字段（11个） ---
    sysinfo = db.Column(db.String(30), comment="系统信息")
    softinfo = db.Column(db.String(30), comment="软件信息")
    posupddate = db.Column(db.DateTime, comment="POS更新日期")
    posinfo = db.Column(db.String(30), comment="POS信息")
    pos_area = db.Column(db.String(2), comment="区域")
    status = db.Column(db.String(1), comment="设备状态")
    typflg = db.Column(db.String(2), comment="类型标志")
    maintenancedate = db.Column(db.DateTime, comment="维护日期")
    maintenancetyp = db.Column(db.String(6), comment="维护类型")
    maintenanceno = db.Column(db.String(10), comment="维护单号")
    # --- 优化方案4 未落地字段（4个） ---
    asset_status = db.Column(db.String(10), comment="资产状态（ACTIVE/RETURNED/SCRAPPED）")
    created_from = db.Column(db.String(20), comment="来源追溯")
    source_id = db.Column(db.String(20), comment="来源单号")
    warranty_expire = db.Column(db.DateTime, comment="保修到期日")

    customer = db.relationship("Customer", back_populates="positions")


class ItemClass(BaseModel):
    """物料分类表（TMM11_ITEMCLASS）。"""

    __tablename__ = "tmm11_itemclass"

    class_cd = db.Column(db.String(20), primary_key=True, comment="分类编码")
    class_nm = db.Column(db.String(50), nullable=False, comment="分类名称")
    parent_cd = db.Column(db.String(20), comment="上级分类")
    # --- Oracle 原表恢复字段 ---
    classtyp = db.Column(db.String(1), comment="分类类型")
    childflg = db.Column(db.String(1), comment="子节点标志")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")


class Item(BaseModel):
    """物料/商品主表（TMM12_ITEMS）。"""

    __tablename__ = "tmm12_items"

    item_cd = db.Column(db.String(20), primary_key=True, comment="物料编码")
    item_nm = db.Column(db.String(100), nullable=False, comment="物料名称")
    class_cd = db.Column(db.String(20), comment="分类编码")
    spec = db.Column(db.String(100), comment="规格型号")
    unit = db.Column(db.String(10), comment="单位")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    # --- Oracle 原表恢复字段（18个） ---
    itemanm = db.Column(db.String(40), comment="物料别名")
    itembrcd = db.Column(db.String(30), comment="物料条码")
    itemsize = db.Column(db.String(30), comment="规格尺寸")
    countrycd = db.Column(db.String(3), comment="产地国家")
    provincecd = db.Column(db.String(2), comment="省份")
    citycd = db.Column(db.String(4), comment="城市")
    wunit = db.Column(db.String(4), comment="计量单位")
    pcrep = db.Column(db.String(6), comment="采购负责人")
    keeper = db.Column(db.String(6), comment="库管员")
    upperlimit = db.Column(db.Integer, comment="库存上限")
    lowerlimit = db.Column(db.Integer, comment="库存下限")
    minorder = db.Column(db.Integer, comment="最小订购量")
    newperiod = db.Column(db.Integer, comment="新品周期(天)")
    oldperiod = db.Column(db.Integer, comment="旧品周期(天)")
    backup = db.Column(db.String(200), comment="备注")
    typflg = db.Column(db.String(1), comment="物料类型标志")
    purchasetyp = db.Column(db.String(1), comment="采购类型")
    consume = db.Column(db.String(1), comment="消耗标志")


class SupplierClass(BaseModel):
    """供应商分类表（TMM18_SUPPLIERCLASS）。"""

    __tablename__ = "tmm18_supplierclass"

    class_cd = db.Column(db.String(20), primary_key=True, comment="分类编码")
    class_nm = db.Column(db.String(50), nullable=False, comment="分类名称")
    # --- Oracle 原表恢复字段 ---
    classtyp = db.Column(db.String(1), comment="分类类型")
    parent = db.Column(db.String(20), comment="上级分类")
    childflg = db.Column(db.String(1), comment="子节点标志")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")


class Supplier(BaseModel):
    """供应商主表（TMM19_SUPPLIERS）。"""

    __tablename__ = "tmm19_suppliers"

    supp_cd = db.Column(db.String(20), primary_key=True, comment="供应商编码")
    supp_nm = db.Column(db.String(100), nullable=False, comment="供应商名称")
    class_cd = db.Column(db.String(20), comment="分类编码")
    address = db.Column(db.String(200), comment="地址")
    phone = db.Column(db.String(30), comment="电话")
    contactor = db.Column(db.String(50), comment="联系人")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    # --- Oracle 原表恢复字段（14个） ---
    custcd = db.Column(db.String(8), comment="关联客户编码")
    custnm = db.Column(db.String(60), comment="供应商全称")
    custanm = db.Column(db.String(20), comment="供应商别名")
    custbrcd = db.Column(db.String(20), comment="供应商条码")
    scale = db.Column(db.String(1), comment="规模等级")
    zipcd = db.Column(db.String(6), comment="邮编")
    phoneno = db.Column(db.String(20), comment="座机电话")
    faxno = db.Column(db.String(20), comment="传真")
    taxno = db.Column(db.String(18), comment="税号")
    banknm = db.Column(db.String(40), comment="开户银行")
    bankaccno = db.Column(db.String(50), comment="银行账号")
    pcrep = db.Column(db.String(6), comment="采购联系人")
    suppinfo = db.Column(db.String(1), comment="供应商状态")
    agreements = db.Column(db.String(1), comment="协议标志")


class SysCode(BaseModel):
    """系统编码表（TMM31_SYSCODES）。"""

    __tablename__ = "tmm31_syscodes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code_typ = db.Column(db.String(10), nullable=False, comment="编码类型")
    code_cd = db.Column(db.String(20), nullable=False, comment="编码值")
    code_nm = db.Column(db.String(50), comment="编码名称")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    sort_no = db.Column(db.Integer, default=0, comment="排序号")
    # --- Oracle 原表恢复字段 ---
    sysflg = db.Column(db.String(1), comment="系统标志")

    __table_args__ = (db.UniqueConstraint("code_typ", "code_cd", name="uq_syscode"),)


class IdMaster(BaseModel):
    """编号生成器表（TMM34_IDMASTER）。"""

    __tablename__ = "tmm34_idmaster"

    id_type = db.Column(db.String(20), primary_key=True, comment="编号类型")
    prefix = db.Column(db.String(10), comment="前缀")
    current_no = db.Column(db.Integer, default=0, comment="当前编号")
    step = db.Column(db.Integer, default=1, comment="步长")
    # --- Oracle 原表恢复字段（6个） ---
    idtyp = db.Column(db.String(2), comment="ID类型")
    idtypnm = db.Column(db.String(20), comment="类型名称")
    curbillid = db.Column(db.String(30), comment="当前流水号")
    maxbillid = db.Column(db.String(30), comment="最大流水号")
    loops = db.Column(db.String(1), comment="循环标志")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
