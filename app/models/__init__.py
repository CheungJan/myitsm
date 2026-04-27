"""数据模型。"""

from app.models.attendance import (
    Attendance,
    AttendanceCount,
)
from app.models.auxiliary import (
    Contract,
    Invoice,
)
from app.models.deposit import (
    Deposit,
    DepositDetail,
    DepositIO,
    DepositList,
    DepositPosModel,
)
from app.models.inventory import (
    AdjustPrice,
    InventoryLimit,
    InventoryLimitHistory,
    Price,
)
from app.models.itsm import (
    AccessoriesUpdate,
    ArchiveCode,
    CloseBills,
    CustPosDaily,
    DeviceChange,
    EquipmentOpen,
    EquipmentRenovate,
    FreeReplace,
    FreeReplaceDt,
    ItsmSysCode,
    LiabilityReg,
    LiabilityRegDt,
    Maintenance,
    MaintenanceArchive,
    MaintenanceAttc,
    MaintenanceD2D,
    MaintenanceDaily,
    MaintenanceDailyTrack,
    MaintenanceDispatch,
    MaintenanceLiability,
    MaintenanceOpen,
    MaintenancePlan,
    MaintenanceRenovate,
    MaintenanceRV,
    NoCloseTrack,
    OnChooseDt,
    PayList,
    PosDetail,
    RecycleTask,
    RecycleTaskDtl,
    RepairInfo,
    StoreClose,
    TimepointArea,
    UserArea,
)
from app.models.master import (
    Area,
    ComMode,
    Company,
    CustClass,
    Customer,
    CustomerHistory,
    CustPosRl,
    IdMaster,
    Item,
    ItemClass,
    Supplier,
    SupplierClass,
    SysCode,
)
from app.models.notification import (
    Notification,
    NotificationTemplate,
)
from app.models.procurement import (
    PurchaseBill,
    PurchasePlan,
    PurchasePlanDt,
    PurchasePlanStatus,
    PurchaseRegister,
    PurchaseRegisterDt,
    ReturnPurchaseBill,
    ReturnPurchaseBillDt,
    SupplierAppraisal,
    SupplierAppraisalDt,
)
from app.models.sales import (
    PlanCust,
    SalesBill,
    SalesExtend,
    SalesExtendDt,
)
from app.models.sla import (
    SlaDefinition,
    SlaTicket,
)
from app.models.system import (
    AccLog,
    Department,
    Group,
    GroupRight,
    Menu,
    MenuDetail,
    SysParm,
    User,
    UserBusiTyp,
    UserGroup,
    UserMenu,
)
from app.models.warehouse import (
    AssetCheckAccept,
    AssetCheckAcceptDtl,
    OverLost,
    OverLostDt,
    OverLostEid,
    PosChange,
    PosChangeDt,
    StockDetail,
    StockDetailDt,
    StockIn,
    StockInDetail,
    StockOut,
    StockOutDetailEid,
    StockOutDetailPrd,
    Warehouse,
)

__all__ = [
    # 系统管理
    "User",
    "Group",
    "UserGroup",
    "UserBusiTyp",
    "Department",
    "Menu",
    "MenuDetail",
    "UserMenu",
    "GroupRight",
    "SysParm",
    "AccLog",
    # 主数据
    "Company",
    "Area",
    "ComMode",
    "CustClass",
    "Customer",
    "CustomerHistory",
    "CustPosRl",
    "Item",
    "ItemClass",
    "Supplier",
    "SupplierClass",
    "SysCode",
    "IdMaster",
    # ITSM 字典/配置
    "TimepointArea",
    "LiabilityReg",
    "LiabilityRegDt",
    "ItsmSysCode",
    "ArchiveCode",
    "RepairInfo",
    "UserArea",
    # ITSM 日常维护
    "MaintenanceDaily",
    "MaintenanceLiability",
    "MaintenanceDailyTrack",
    "PosDetail",
    "MaintenanceAttc",
    "MaintenanceArchive",
    # ITSM 新机开通
    "MaintenanceOpen",
    "EquipmentOpen",
    # ITSM 旧机翻新
    "MaintenanceRenovate",
    "EquipmentRenovate",
    # ITSM 设备变更
    "DeviceChange",
    # ITSM 日常保养
    "Maintenance",
    "CustPosDaily",
    "MaintenancePlan",
    # ITSM 门店关闭
    "StoreClose",
    # ITSM 配件选取
    "OnChooseDt",
    # ITSM 分派
    "MaintenanceDispatch",
    # ITSM 公用附表
    "MaintenanceD2D",
    "MaintenanceRV",
    "AccessoriesUpdate",
    "PayList",
    "CloseBills",
    # ITSM 免费更换
    "FreeReplace",
    "FreeReplaceDt",
    # ITSM 回收任务（P0-1/优化4.2）
    "RecycleTask",
    "RecycleTaskDtl",
    # ITSM 未关单跟踪
    "NoCloseTrack",
    # 仓储管理
    "Warehouse",
    "StockDetail",
    "StockDetailDt",
    "StockIn",
    "StockInDetail",
    "StockOut",
    "StockOutDetailEid",
    "StockOutDetailPrd",
    "OverLost",
    "OverLostDt",
    "OverLostEid",
    "AssetCheckAccept",
    "AssetCheckAcceptDtl",
    "PosChange",
    "PosChangeDt",
    # 采购管理
    "PurchasePlan",
    "PurchasePlanDt",
    "PurchasePlanStatus",
    "PurchaseRegister",
    "PurchaseRegisterDt",
    "PurchaseBill",
    "ReturnPurchaseBill",
    "ReturnPurchaseBillDt",
    "SupplierAppraisal",
    "SupplierAppraisalDt",
    # 销售管理
    "PlanCust",
    "SalesBill",
    "SalesExtend",
    "SalesExtendDt",
    # SLA 服务级别管理（Tier-1）
    "SlaDefinition",
    "SlaTicket",
    # 考勤管理
    "Attendance",
    "AttendanceCount",
    # 库存预警与价格
    "InventoryLimit",
    "InventoryLimitHistory",
    "Price",
    "AdjustPrice",
    # 押金管理
    "Deposit",
    "DepositDetail",
    "DepositIO",
    "DepositList",
    "DepositPosModel",
    # 合同管理（Tier-1）
    "Contract",
    "Invoice",
    # 通知系统（Tier-1）
    "NotificationTemplate",
    "Notification",
]
