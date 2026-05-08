"""Oracle→PostgreSQL 字段级映射规则与类型转换。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


def normalize_char(value: str | None) -> str | None:
    """Oracle CHAR 类型去除右侧空格。"""
    if value is None:
        return None
    return value.rstrip()


@dataclass
class FieldMapping:
    """单个字段的映射规则。"""

    new_name: str
    old_name: str | None = None
    transform: str | None = None
    default: Any = None

    def __post_init__(self) -> None:
        if self.old_name is None and self.default is None:
            raise ValueError(f"字段 '{self.new_name}' 必须指定 old_name 或 default")

    def apply(self, old_row: dict[str, Any]) -> Any:
        if self.old_name is None:
            return self.default
        value = old_row.get(self.old_name)
        if value is None and self.default is not None:
            return self.default
        if self.transform == "char":
            return normalize_char(value)
        return value


@dataclass
class TableMapping:
    """整表映射：旧表名 → 新表名 + 字段映射列表。"""

    old_table: str
    new_table: str
    fields: list[FieldMapping] = field(default_factory=list)
    batch: int = 1
    depends_on: list[str] = field(default_factory=list)


def map_source_row(mapping: TableMapping, old_row: dict[str, Any]) -> dict[str, Any]:
    """将一行源库数据按映射规则转换为目标行。"""
    return {fm.new_name: fm.apply(old_row) for fm in mapping.fields}


# ============================================================
# 全部映射定义（按批次 + 外键依赖顺序）
# ============================================================

MAPPINGS: list[TableMapping] = []


def _m(
    old: str,
    new: str,
    fields: list[FieldMapping],
    batch: int = 1,
    depends_on: list[str] | None = None,
) -> TableMapping:
    m = TableMapping(
        old_table=old, new_table=new, fields=fields,
        batch=batch, depends_on=depends_on or [],
    )
    MAPPINGS.append(m)
    return m


# ---------- 第1批：基础主数据 ----------

_m("TMC11_DEPARTMENTS", "tmc11_departments", [
    FieldMapping("deptcd", "DEPTCD", transform="char"),
    FieldMapping("deptnm", "DEPTNM"),
    FieldMapping("levelcd", "LEVELCD"),
    FieldMapping("parent", "PARENT", transform="char"),
    FieldMapping("leader", "LEADER", transform="char"),
    FieldMapping("childflg", "CHILDFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=1)

_m("TMC13_USERS", "tmc13_users", [
    FieldMapping("usercd", "USERCD", transform="char"),
    FieldMapping("usernm", "USERNM"),
    FieldMapping("passwd", "PASSWD"),
    FieldMapping("deptcd", "DEPTCD", transform="char"),
    FieldMapping("credamt", "CREDAMT"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=1)

_m("TMC01_MENUS", "tmc01_menus", [
    FieldMapping("menucd", "MENUCD"),
    FieldMapping("menunm", "MENUNM"),
    FieldMapping("levelcd", "LEVELCD"),
    FieldMapping("parent", "PARENT"),
    FieldMapping("execpath", "EXEPATH"),
    FieldMapping("picname", "PICNAME"),
    FieldMapping("ordno", "ORDNO"),
    FieldMapping("openflg", "OPENFLG", transform="char"),
    FieldMapping("childflg", "CHILDFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=1)

_m("TMC02_MENUSDT", "tmc02_menusdt", [
    FieldMapping("menucd", "MENUCD"),
    FieldMapping("funccd", "FUNCCD"),
    FieldMapping("funcnm", "FUNCNM"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=1)

_m("TMC12_GROUPS", "tmc12_groups", [
    FieldMapping("groupcd", "GROUPCD", transform="char"),
    FieldMapping("groupnm", "GROUPNM"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=1)

_m("TMM01_COMPANY", "tmm01_company", [
    FieldMapping("compcd", "COMPCD", transform="char"),
    FieldMapping("compnm", "COMPNM"),
    FieldMapping("companm", "COMPANM"),
    FieldMapping("leader", "LEADER"),
    FieldMapping("address", "ADDRESS"),
    FieldMapping("phoneno", "PHONENO"),
    FieldMapping("telex", "TELEX"),
    FieldMapping("faxno", "FAXNO"),
    FieldMapping("banknm", "BANKNM"),
    FieldMapping("bankaccno", "BANKACCNO"),
    FieldMapping("taxno", "TAXNO"),
    FieldMapping("opendate", "OPENDATE"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
    FieldMapping("mailcd", "MAILCD", transform="char"),
    FieldMapping("produce", "PRODUCE"),
    FieldMapping("maintenance", "MAINTENANCE"),
], batch=1)

_m("TMM21_CUSTCLASS", "tmm21_custclass", [
    FieldMapping("classtyp", "CLASSTYP", transform="char"),
    FieldMapping("classcd", "CLASSCD"),
    FieldMapping("classnm", "CLASSNM"),
    FieldMapping("parent", "PARENT"),
    FieldMapping("childflg", "CHILDFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
], batch=1)

_m("TMM22_CUSTOMERS", "tmm22_customers", [
    FieldMapping("custcd", "CUSTCD", transform="char"),
    FieldMapping("custnm", "CUSTNM"),
    FieldMapping("custanm", "CUSTANM"),
    FieldMapping("custbrcd", "CUSTBRCD"),
    FieldMapping("classcd", "CLASSCD"),
    FieldMapping("busityp", "BUSITYP", transform="char"),
    FieldMapping("address", "ADDRESS"),
    FieldMapping("zipcd", "ZIPCD", transform="char"),
    FieldMapping("phoneno", "PHONENO"),
    FieldMapping("faxno", "FAXNO"),
    FieldMapping("contactor", "CONTACTOR"),
    FieldMapping("taxno", "TAXNO"),
    FieldMapping("banknm", "BANKNM"),
    FieldMapping("bankaccno", "BANKACCNO"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("parentcd", "PARENTCD", transform="char"),
    FieldMapping("custcard", "CUSTCARD"),
    FieldMapping("backup", "BACKUP"),
    FieldMapping("location", "LOCATION", transform="char"),
    FieldMapping("area", "AREA"),
    FieldMapping("pos_n", "POS_N"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
    FieldMapping("opersystem", "OPERSYSTEM"),
    FieldMapping("database", "DATA_BASE"),
    FieldMapping("softedition", "SOFT_EDITION"),
    FieldMapping("sstatus", "S_STATUS", transform="char"),
    FieldMapping("advideo", "AD_VIDEO", transform="char"),
    FieldMapping("commmode", "COMMMODE"),
    FieldMapping("card3g", "CARD3G"),
    FieldMapping("adr3g", "ADR3G"),
    FieldMapping("systemcode", "SYSTEMCODE"),
    FieldMapping("custrnm", "CUSTRNM"),
    FieldMapping("opendate", "OPENDATE"),
    FieldMapping("replacedate", "REPLACEDATE"),
    FieldMapping("levels", "LEVELS"),
    FieldMapping("ordertype", "ORDERTYPE"),
    FieldMapping("pptcode", "PPTCODE"),
    FieldMapping("jl_contactor", "JL_CONTACTOR"),
    FieldMapping("jl_phoneno", "JL_PHONENO"),
    FieldMapping("zftype", "ZFTYPE"),
    FieldMapping("posstatus", "POSSTATUS"),
    FieldMapping("posstatus1", "POSSTATUS1"),
    FieldMapping("is_contract", "IS_CONTRACT"),
    FieldMapping("yjmoney", "YJ_MONEY"),
], batch=1)

_m("TMM11_ITEMCLASS", "tmm11_itemclass", [
    FieldMapping("classtyp", "CLASSTYP", transform="char"),
    FieldMapping("classcd", "CLASSCD"),
    FieldMapping("classnm", "CLASSNM"),
    FieldMapping("parent", "PARENT"),
    FieldMapping("childflg", "CHILDFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
], batch=1)

_m("TMM12_ITEMS", "tmm12_items", [
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("classcd", "CLASSCD"),
    FieldMapping("itemnm", "ITEMNM"),
    FieldMapping("itemanm", "ITEMANM"),
    FieldMapping("itembrcd", "ITEMBRCD"),
    FieldMapping("itemsize", "ITEMSIZE"),
    FieldMapping("countrycd", "COUNTRYCD", transform="char"),
    FieldMapping("provincecd", "PROVINCECD", transform="char"),
    FieldMapping("citycd", "CITYCD", transform="char"),
    FieldMapping("wunit", "WUNIT"),
    FieldMapping("pcrep", "PCREP", transform="char"),
    FieldMapping("keeper", "KEEPER", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("upperlimit", "UPPERLIMIT"),
    FieldMapping("lowerlimit", "LOWERLIMIT"),
    FieldMapping("minorder", "MINORDER"),
    FieldMapping("newperiod", "NEWPERIOD"),
    FieldMapping("oldperiod", "OLDPERIOD"),
    FieldMapping("backup", "BACKUP"),
    FieldMapping("typflg", "TYPFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
    FieldMapping("purchasetyp", "PURCHASETYP", transform="char"),
    FieldMapping("consume", "CONSUME", transform="char"),
], batch=1)

_m("TMM18_SUPPLIERCLASS", "tmm18_supplierclass", [
    FieldMapping("classtyp", "CLASSTYP", transform="char"),
    FieldMapping("classcd", "CLASSCD"),
    FieldMapping("classnm", "CLASSNM"),
    FieldMapping("parent", "PARENT"),
    FieldMapping("childflg", "CHILDFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
], batch=1)

_m("TMM19_SUPPLIERS", "tmm19_suppliers", [
    FieldMapping("custcd", "CUSTCD", transform="char"),
    FieldMapping("custnm", "CUSTNM"),
    FieldMapping("custanm", "CUSTANM"),
    FieldMapping("custbrcd", "CUSTBRCD"),
    FieldMapping("classcd", "CLASSCD"),
    FieldMapping("scale", "SCALE", transform="char"),
    FieldMapping("address", "ADDRESS"),
    FieldMapping("zipcd", "ZIPCD", transform="char"),
    FieldMapping("phoneno", "PHONENO"),
    FieldMapping("faxno", "FAXNO"),
    FieldMapping("contactor", "CONTACTOR"),
    FieldMapping("taxno", "TAXNO"),
    FieldMapping("banknm", "BANKNM"),
    FieldMapping("bankaccno", "BANKACCNO"),
    FieldMapping("pcrep", "PCREP", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("suppinfo", "SUPPINFO", transform="char"),
    FieldMapping("agreements", "AGREEMENTS", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
], batch=1)

_m("TWH01_WAREHOUSE", "twh01_warehouse", [
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("whnm", "WHNM"),
    FieldMapping("whtyp", "WHTYP", transform="char"),
    FieldMapping("address", "ADDRESS"),
    FieldMapping("phoneno", "PHONENO"),
    FieldMapping("fax", "FAX"),
    FieldMapping("leader", "LEADER", transform="char"),
    FieldMapping("defaultflg", "DEFAULTFLG", transform="char"),
    FieldMapping("remoteflg", "REMOTEFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=1)

_m("TMM46_AREA", "tmm46_area", [
    FieldMapping("id", "ID"),
    FieldMapping("name", "NAME"),
    FieldMapping("usercd", "USERCD", transform="char"),
], batch=1)

_m("TMM47_COMMODE", "tmm47_commode", [
    FieldMapping("cmmcd", "CMMCD"),
    FieldMapping("cmmnm", "CMMNM"),
    FieldMapping("cmmtype", "CMMTYPE", transform="char"),
    FieldMapping("parent", "PARENT"),
    FieldMapping("childflg", "CHILDFLG", transform="char"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("gendate", "GENDATE"),
], batch=1)

_m("TMM24_CUSTITEMS", "tmm24_custitems", [
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("custcd", "CUSTCD", transform="char"),
    FieldMapping("dfltflg", "DFLTFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("delivercycle", "DELIVERCYCLE"),
    FieldMapping("servicecycle", "SERVICECYCLE"),
    FieldMapping("guarntperiod", "GUARANTEEPERIOD"),
    FieldMapping("backup", "BACKUP"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
], batch=1)

_m("TMM31_SYSCODES", "tmm31_syscodes", [
    FieldMapping("codetyp", "CODETYP", transform="char"),
    FieldMapping("codecd", "CODECD", transform="char"),
    FieldMapping("codenm", "CODENM"),
    FieldMapping("sysflg", "SYSFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
], batch=1)

_m("TMM34_IDMASTER", "tmm34_idmaster", [
    FieldMapping("idtyp", "IDTYP", transform="char"),
    FieldMapping("idtypnm", "IDTYPNM"),
    FieldMapping("curbillid", "CURBILLID"),
    FieldMapping("maxbillid", "MAXBILLID"),
    FieldMapping("loops", "LOOPS"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=1)

_m("TMC71_SYSPARM", "tmc71_sysparm", [
    FieldMapping("pk", "PK", transform="char"),
    FieldMapping("costtype", "COSTTYPE", transform="char"),
    FieldMapping("autobackpath", "AUTOBACKPATH"),
    FieldMapping("invoicesharepath", "INVOICESHAREPATH"),
    FieldMapping("poinvaliddays", "POINVALIDDAYS"),
    FieldMapping("soinvaliddays", "SOINVALIDDAYS"),
    FieldMapping("allowmultilogon", "ALLOWMULTILOGON", transform="char"),
    FieldMapping("shopbilltype", "SHOPBILLTYPE", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("centralwarehouse", "CENTRALWAREHOUSE", transform="char"),
], batch=1)

_m("TMC41_ACCLOG", "tmc41_acclog", [
    FieldMapping("startdate", "STARTDATE"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
], batch=1)


# ---------- 第2批：ITSM 字典与配置 ----------

_m("TIT01_TIMEPOINT_AREA", "tit01_timepoint_area", [
    FieldMapping("levels", "LEVELS"),
    FieldMapping("explain", "EXPLAIN"),
    FieldMapping("timepoint", "TIMEPOINT"),
    FieldMapping("beforetm", "BEFORETM"),
    FieldMapping("aftertm", "AFTERTM"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=2)

_m("TIT02_LIABILITYREG", "tit02_liabilityreg", [
    FieldMapping("liabcd", "LIABCD"),
    FieldMapping("liabnm", "LIABNM"),
    FieldMapping("describe", "DESCRIBE"),
    FieldMapping("liabtype", "LIABTYPE", transform="char"),
    FieldMapping("parent", "PARENT"),
    FieldMapping("childflg", "CHILDFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=2)

_m("TIT02_LIABILITYREGDT", "tit02_liabilityregdt", [
    FieldMapping("lbdtcd", "LBDTCD"),
    FieldMapping("liabcd", "LIABCD"),
    FieldMapping("define", "DEFINE"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=2)

_m("TIT03_SYSCODES", "tit03_syscodes", [
    FieldMapping("codetyp", "CODETYP", transform="char"),
    FieldMapping("codecd", "CODECD", transform="char"),
    FieldMapping("codenm", "CODENM"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("sysflg", "SYSFLG", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
], batch=2)

_m("TIT04_ARCHIVECODE", "tit04_archivecode", [
    FieldMapping("archcd", "ARCHCD"),
    FieldMapping("archnm", "ARCHNM"),
    FieldMapping("describe", "DESCRIBE"),
    FieldMapping("archtype", "ARCHTYPE", transform="char"),
    FieldMapping("parent", "PARENT"),
    FieldMapping("childflg", "CHILDFLG", transform="char"),
    FieldMapping("maxlevel", "MAXLEVEL"),
    FieldMapping("archgroup", "ARCHGROUP", transform="char"),
    FieldMapping("faulttype", "FAULTTYPE"),
    FieldMapping("uncheck", "UNCHECK", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=2)

_m("TIT05_REPAIRINFO", "tit05_repairinfo", [
    FieldMapping("reptype", "REP_TYPE", transform="char"),
    FieldMapping("objcd", "OBJ_CD"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=2)

_m("TIT06_USERAREA", "tit06_userarea", [
    FieldMapping("areaid", "AREAID"),
    FieldMapping("usercd", "USERCD", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
], batch=2)

_m("TMC03_USERMENUS", "tmc03_usermenus", [
    FieldMapping("usercd", "USERCD", transform="char"),
    FieldMapping("menucd", "MENUCD"),
    FieldMapping("ordno", "ORDNO"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=2)

_m("TMC21_USERGROUP", "tmc21_usergroup", [
    FieldMapping("usercd", "USERCD", transform="char"),
    FieldMapping("groupcd", "GROUPCD", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=2)

_m("TMC22_USERBUSITYP", "tmc22_userbusityp", [
    FieldMapping("usercd", "USERCD", transform="char"),
    FieldMapping("busityp", "BUSITYP", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=2)

_m("TMC31_GROUPRIGHT", "tmc31_groupright", [
    FieldMapping("groupcd", "GROUPCD", transform="char"),
    FieldMapping("menucd", "MENUCD"),
    FieldMapping("funccd", "FUNCCD"),
    FieldMapping("scale", "SCALE"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
], batch=2)

_m("TMM35_CUST_POS_RL", "tmm35_cust_pos_rl", [
    FieldMapping("custcd", "CUSTCD", transform="char"),
    FieldMapping("eid", "EID", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("startdate", "STARTDATE"),
    FieldMapping("sysinfo", "SYSINFO"),
    FieldMapping("softinfo", "SOFTINFO"),
    FieldMapping("posupddate", "POSUPDDATE"),
    FieldMapping("posinfo", "POSINFO"),
    FieldMapping("area", "AREA", transform="char"),
    FieldMapping("status", "STATUS", transform="char"),
    FieldMapping("typflg", "TYPFLG", transform="char"),
    FieldMapping("maintenancedate", "MAINTENANCEDATE"),
    FieldMapping("maintenancetyp", "MAINTENANCETYP", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("maintenanceno", "MAINTENANCENO"),
    FieldMapping("asset_type", default="POS"),
    FieldMapping("recycle_status", default="ACTIVE"),
], batch=2)

_m("TMM36_CUST_VE_RL", "tmm36_cust_ve_rl", [
    FieldMapping("custcd", "CUSTCD", transform="char"),
    FieldMapping("eid", "EID", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("startdate", "STARTDATE"),
    FieldMapping("sysinfo", "SYSINFO"),
    FieldMapping("softinfo", "SOFTINFO"),
    FieldMapping("posupddate", "POSUPDDATE"),
    FieldMapping("posinfo", "POSINFO"),
    FieldMapping("area", "AREA", transform="char"),
    FieldMapping("status", "STATUS", transform="char"),
    FieldMapping("typflg", "TYPFLG", transform="char"),
    FieldMapping("maintenancedate", "MAINTENANCEDATE"),
    FieldMapping("maintenancetyp", "MAINTENANCETYP"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=2)


# ---------- 第3批：ITSM 业务单据 ----------

def _itsm_main_fields(id_field: str, id_col: str) -> list[FieldMapping]:
    """ITSM 主表通用字段映射工厂。"""
    return [
        FieldMapping(id_field, id_col),
        FieldMapping("company_id", "COMPANY_ID", transform="char"),
        FieldMapping("store_id", "STORE_ID", transform="char"),
        FieldMapping("request_time", "REQUEST_TIME"),
        FieldMapping("requset_paper_id", "REQUSET_PAPER_ID"),
        FieldMapping("expected_completion_time", "EXPECTED_COMPLETION_TIME"),
        FieldMapping("deliver_no", "DELIVER_NO"),
        FieldMapping("short_description", "SHORT_DESCRIPTION"),
        FieldMapping("detail_description", "DETAIL_DESCRIPTION"),
        FieldMapping("current_status", "CURRENT_STATUS", transform="char"),
        FieldMapping("is_success", "IS_SUCCESS", transform="char"),
        FieldMapping("is_old", "IS_OLD", transform="char"),
        FieldMapping("create_time", "CREATE_TIME"),
        FieldMapping("creator", "CREATOR", transform="char"),
        FieldMapping("update_time", "UPDATE_TIME"),
        FieldMapping("updator", "UPDATOR", transform="char"),
        FieldMapping("firstor", "FIRSTOR", transform="char"),
        FieldMapping("first_time", "FIRST_TIME"),
        FieldMapping("leave_time", "LEAVE_TIME"),
        FieldMapping("close_time", "CLOSE_TIME"),
        FieldMapping("revisit_time", "REVISIT_TIME"),
    ]


_m("TIT10_MAINTENANCEDAY", "tit10_maintenanceday", [
    *_itsm_main_fields("maintenance_id", "MAINTENANCE_ID"),
    FieldMapping("temp_contract", "TEMP_CONTRACT"),
    FieldMapping("fault_type", "FAULT_TYPE"),
    FieldMapping("servrity", "SERVRITY", transform="char"),
    FieldMapping("emergency_level", "EMERGENCY_LEVEL", transform="char"),
    FieldMapping("priority", "PRIORITY", transform="char"),
    FieldMapping("requester", "REQUESTER", transform="char"),
    FieldMapping("device_id", "DEVICE_ID", transform="char"),
    FieldMapping("faultcode", "FAULTCODE"),
    FieldMapping("is_archive", "IS_ARCHIVE", transform="char"),
    FieldMapping("view_type", "VIEW_TYPE", transform="char"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("requst_typ", "REQUST_TYP"),
    FieldMapping("source_type", default="DAILY"),
], batch=3)

_m("TIT10_MAINTENANCE_LIABILITY", "tit10_maintenance_liability", [
    FieldMapping("maintenance_id", "MAINTENANCE_ID"),
    FieldMapping("exceptionscd", "EXCEPTIONSCD"),
    FieldMapping("exceptionsnm", "EXCEPTIONSNM"),
    FieldMapping("deptnm", "DEPTNM"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("assessflg", "ASSESSFLG", transform="char"),
    FieldMapping("exemptflg", "EXEMPTFLG", transform="char"),
    FieldMapping("type", "TYPE", transform="char"),
    FieldMapping("is_finish", "IS_FINISH", transform="char"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("setfrom", "SETFROM"),
], batch=3)

_m("TIT10_MAIN_TRACK", "tit10_main_track", [
    FieldMapping("maintenance_id", "MAINTENANCE_ID"),
    FieldMapping("depcd", "DEP_CD"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("updatetime", "UPDATETIME"),
], batch=3)

_m("TIT10_POS_DETAIL", "tit10_pos_detail", [
    FieldMapping("bill_id", "BILL_ID"),
    FieldMapping("sm_id", "SM_ID"),
    FieldMapping("noflg", "NOFLG", transform="char"),
    FieldMapping("device_id", "DEVICE_ID", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("accessories_id", "ACCESSORIES_ID", transform="char"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("status", "STATUS", transform="char"),
], batch=3)

_m("TIT13_MAINTENANCE_OPEN", "tit13_maintenance_open", [
    FieldMapping("new_opening_id", "NEW_OPENING_ID"),
    FieldMapping("company_id", "COMPANY_ID", transform="char"),
    FieldMapping("store_id", "STORE_ID", transform="char"),
    FieldMapping("request_time", "REQUEST_TIME"),
    FieldMapping("requset_paper_id", "REQUSET_PAPER_ID"),
    FieldMapping("device_id", "DEVICE_ID", transform="char"),
    FieldMapping("count", "COUNT"),
    FieldMapping("expected_completion_time", "EXPECTED_COMPLETION_TIME"),
    FieldMapping("deliver_no", "DELIVER_NO"),
    FieldMapping("short_description", "SHORT_DESCRIPTION"),
    FieldMapping("detail_description", "DETAIL_DESCRIPTION"),
    FieldMapping("current_status", "CURRENT_STATUS", transform="char"),
    FieldMapping("is_success", "IS_SUCCESS", transform="char"),
    FieldMapping("is_old", "IS_OLD", transform="char"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
    FieldMapping("firstor", "FIRSTOR", transform="char"),
    FieldMapping("first_time", "FIRST_TIME"),
    FieldMapping("leave_time", "LEAVE_TIME"),
    FieldMapping("close_time", "CLOSE_TIME"),
    FieldMapping("revisit_time", "REVISIT_TIME"),
    FieldMapping("from_custcard", "FROM_CUSTCARD"),
    FieldMapping("from_custcd", "FROM_CUSTCD", transform="char"),
], batch=3)

_m("TIT15_MAINTENANCE_RENOVATE", "tit15_maintenance_renovate", [
    FieldMapping("renew_id", "RENEW_ID"),
    FieldMapping("company_id", "COMPANY_ID", transform="char"),
    FieldMapping("store_id", "STORE_ID", transform="char"),
    FieldMapping("request_time", "REQUEST_TIME"),
    FieldMapping("requset_paper_id", "REQUSET_PAPER_ID"),
    FieldMapping("old_device_id", "OLD_DEVICE_ID", transform="char"),
    FieldMapping("new_device_id", "NEW_DEVICE_ID", transform="char"),
    FieldMapping("count", "COUNT"),
    FieldMapping("expected_completion_time", "EXPECTED_COMPLETION_TIME"),
    FieldMapping("deliver_no", "DELIVER_NO"),
    FieldMapping("short_description", "SHORT_DESCRIPTION"),
    FieldMapping("detail_description", "DETAIL_DESCRIPTION"),
    FieldMapping("current_status", "CURRENT_STATUS", transform="char"),
    FieldMapping("is_success", "IS_SUCCESS", transform="char"),
    FieldMapping("is_old", "IS_OLD", transform="char"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
    FieldMapping("firstor", "FIRSTOR", transform="char"),
    FieldMapping("first_time", "FIRST_TIME"),
    FieldMapping("leave_time", "LEAVE_TIME"),
    FieldMapping("close_time", "CLOSE_TIME"),
    FieldMapping("revisit_time", "REVISIT_TIME"),
    FieldMapping("is_back", "IS_BACK", transform="char"),
], batch=3)

_m("TIT16_DEVICE_CHANGE", "tit16_device_change", [
    FieldMapping("device_change_id", "DEVICE_CHANGE_ID"),
    FieldMapping("store_id", "STORE_ID", transform="char"),
    FieldMapping("requset_paper_id", "REQUSET_PAPER_ID"),
    FieldMapping("change_type", "CHANGE_TYPE"),
    FieldMapping("device_id", "DEVICE_ID", transform="char"),
    FieldMapping("new_contactor", "NEW_CONTACTOR"),
    FieldMapping("new_tel", "NEW_TEL"),
    FieldMapping("new_address", "NEW_ADDRESS"),
    FieldMapping("new_store_card", "NEW_STORE_CARD"),
    FieldMapping("new_store_id", "NEW_STORE_ID", transform="char"),
    FieldMapping("is_store_inside_change", "IS_STORE_INSIDE_CHANGE", transform="char"),
    FieldMapping("request_time", "REQUEST_TIME"),
    FieldMapping("expected_completion_time", "EXPECTED_COMPLETION_TIME"),
    FieldMapping("short_description", "SHORT_DESCRIPTION"),
    FieldMapping("detail_description", "DETAIL_DESCRIPTION"),
    FieldMapping("current_status", "CURRENT_STATUS", transform="char"),
    FieldMapping("is_success", "IS_SUCCESS", transform="char"),
    FieldMapping("is_old", "IS_OLD", transform="char"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
    FieldMapping("firstor", "FIRSTOR", transform="char"),
    FieldMapping("first_time", "FIRST_TIME"),
    FieldMapping("leave_time", "LEAVE_TIME"),
    FieldMapping("close_time", "CLOSE_TIME"),
    FieldMapping("revisit_time", "REVISIT_TIME"),
    FieldMapping("customer_status", default="ACTIVE"),
], batch=3)

_m("TIT17_MAINTENANCE", "tit17_maintenance", [
    FieldMapping("daily_maintenance_id", "DAILY_MAINTENANCE_ID"),
    FieldMapping("store_id", "STORE_ID", transform="char"),
    FieldMapping("has_video_device", "HAS_VIDEO_DEVICE", transform="char"),
    FieldMapping("video_device_status", "VIDEO_DEVICE_STATUS"),
    FieldMapping("video_device_error_des", "VIDEO_DEVICE_ERROR_DES"),
    FieldMapping("request_engineer_id", "REQUEST_ENGINNER_ID", transform="char"),
    FieldMapping("request_time", "REQUEST_TIME"),
    FieldMapping("short_description", "SHORT_DESCRIPTION"),
    FieldMapping("detail_description", "DETAIL_DESCRIPTION"),
    FieldMapping("current_status", "CURRENT_STATUS", transform="char"),
    FieldMapping("is_success", "IS_SUCCESS", transform="char"),
    FieldMapping("is_old", "IS_OLD", transform="char"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
    FieldMapping("firstor", "FIRSTOR", transform="char"),
    FieldMapping("first_time", "FIRST_TIME"),
    FieldMapping("leave_time", "LEAVE_TIME"),
    FieldMapping("close_time", "CLOSE_TIME"),
    FieldMapping("revisit_time", "REVISIT_TIME"),
], batch=3)

_m("TIT17_CUST_POS_DAILY", "tit17_cust_pos_daily", [
    FieldMapping("daily_maintenance_id", "DAILY_MAINTENANCE_ID"),
    FieldMapping("business_operation_id", "BUSINESS_OPERATION_ID"),
    FieldMapping("custcd", "CUSTCD", transform="char"),
    FieldMapping("eid", "EID", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("startdate", "STARTDATE"),
    FieldMapping("sysinfo", "SYSINFO"),
    FieldMapping("softinfo", "SOFTINFO"),
    FieldMapping("posupddate", "POSUPDDATE"),
    FieldMapping("posinfo", "POSINFO"),
    FieldMapping("area", "AREA", transform="char"),
    FieldMapping("status", "STATUS", transform="char"),
    FieldMapping("typflg", "TYPFLG", transform="char"),
    FieldMapping("maintenancedate", "MAINTENANCEDATE"),
    FieldMapping("maintenancetyp", "MAINTENANCETYP", transform="char"),
    FieldMapping("request_engineer_id", "REQUEST_ENGINNER_ID", transform="char"),
    FieldMapping("request_time", "REQUEST_TIME"),
    FieldMapping("short_description", "SHORT_DESCRIPTION"),
    FieldMapping("detail_description", "DETAIL_DESCRIPTION"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=3)

_m("TIT17_MAINTENANCE_PLAN", "tit17_maintenance_plan", [
    FieldMapping("plan_y", "PLAN_Y"),
    FieldMapping("plan_yymm", "PLAN_YYMM"),
    FieldMapping("area_id", "AREA_ID"),
    FieldMapping("plan_qty", "PLAN_QTY"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
], batch=3)

_m("TIT21_MAINTENANCE_DISPATCH", "tit21_maintenance_dispatch", [
    FieldMapping("maintenance_id", "MAINTENANCE_ID"),
    FieldMapping("business_operation_id", "BUSINESS_OPERATION_ID"),
    FieldMapping("maintenance_type", "MAINTENANCE_TYPE", transform="char"),
    FieldMapping("operator", "OPERATOR", transform="char"),
    FieldMapping("accpectd_group", "ACCPECTD_GROUP", transform="char"),
    FieldMapping("accpectder", "ACCPECTDER", transform="char"),
    FieldMapping("dispatch_time", "DISPATCH_TIME"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
], batch=3)

_m("TIT23_MAINTENANCE_D2D", "tit23_maintenance_d2d", [
    FieldMapping("maintenance_id", "MAINTENANCE_ID"),
    FieldMapping("business_operation_id", "BUSINESS_OPERATION_ID"),
    FieldMapping("d2d_engineer", "D2D_ENGINEER", transform="char"),
    FieldMapping("arrive_time", "ARRIVE_TIME"),
    FieldMapping("leave_time", "LEAVE_TIME"),
    FieldMapping("jjbz", "JJBZ", transform="char"),
    FieldMapping("d2d_description", "D2D_DESCRIPITON"),
    FieldMapping("d2d_phone", "D2D_PHONE"),
    FieldMapping("old_business_id", "OLD_BUSINESS_ID"),
    FieldMapping("d2d_group", "D2D_GROUP"),
    FieldMapping("d2d_type", "D2D_TYPE", transform="char"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("posstatus", "POSSTATUS"),
    FieldMapping("posstatus1", "POSSTATUS1"),
], batch=3)

_m("TIT24_MAINTENANCE_RV", "tit24_maintenance_rv", [
    FieldMapping("maintenance_id", "MAINTENANCE_ID"),
    FieldMapping("business_operation_id", "BUSINESS_OPERATION_ID"),
    FieldMapping("rv_time", "RV_TIME"),
    FieldMapping("rv_operator", "RV_OPERATOR"),
    FieldMapping("feedback", "FEEDBACK"),
    FieldMapping("satisfaction", "SATISFACTION", transform="char"),
    FieldMapping("create_time", "CREATE_TIME"),
    FieldMapping("creator", "CREATOR", transform="char"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
], batch=3)


# ---------- 第4批：仓储/采购/销售 ----------

_m("TWH11_DETAIL", "twh11_detail", [
    FieldMapping("seqno", "SEQNO"),
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("itemtyp", "ITEMTYP", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("prddate", "PRDDATE"),
    FieldMapping("itemqty", "ITEMQTY"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=4)

_m("TWH12_DETAILDT", "twh12_detaildt", [
    FieldMapping("seqno", "SEQNO"),
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("itemtyp", "ITEMTYP", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("prddate", "PRDDATE"),
    FieldMapping("billid", "BILLID", transform="char"),
    FieldMapping("invdate", "INVDATE"),
    FieldMapping("invtyp", "INVTYP", transform="char"),
    FieldMapping("itemqty", "ITEMQTY"),
    FieldMapping("storeqty", "STOREQTY"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("iotyp", "IOTYP", transform="char"),
], batch=4)

_m("TWH13_IN", "twh13_in", [
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("indate", "INDATE"),
    FieldMapping("inbillid", "INBILLID", transform="char"),
    FieldMapping("invtyp", "INVTYP", transform="char"),
    FieldMapping("refbillid", "REFBILLID", transform="char"),
    FieldMapping("ptimes", "PTIMES"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("auditflg", "AUDITFLG", transform="char"),
    FieldMapping("auditman", "AUDITMAN", transform="char"),
    FieldMapping("auditdate", "AUDITDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("optyp", "OPTYP", transform="char"),
    FieldMapping("suppcd", "SUPPCD", transform="char"),
], batch=4)

_m("TWH14_CHECKINDT", "twh14_checkindt", [
    FieldMapping("inbillid", "INBILLID", transform="char"),
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("lineno", "LINENO"),
    FieldMapping("itemtyp", "ITEMTYP", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("prddate", "PRDDATE"),
    FieldMapping("batchid", "BATCHID"),
    FieldMapping("inqty", "INQTY"),
    FieldMapping("reflineno", "REFLINENO"),
    FieldMapping("s_money", "S_MONEY"),
], batch=4)

_m("TWH15_OUT", "twh15_out", [
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("outdate", "OUTDATE"),
    FieldMapping("outbillid", "OUTBILLID", transform="char"),
    FieldMapping("invtyp", "INVTYP", transform="char"),
    FieldMapping("ptimes", "PTIMES"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("auditflg", "AUDITFLG", transform="char"),
    FieldMapping("auditman", "AUDITMAN", transform="char"),
    FieldMapping("auditdate", "AUDITDATE"),
    FieldMapping("optyp", "OPTYP", transform="char"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("targetwhcd", "TARGETWHCD", transform="char"),
    FieldMapping("suppcd", "SUPPCD", transform="char"),
], batch=4)

_m("TWH16_OUTDTEID", "twh16_outdteid", [
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("outbillid", "OUTBILLID", transform="char"),
    FieldMapping("lineno", "LINENO"),
    FieldMapping("itemtyp", "ITEMTYP", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("prddate", "PRDDATE"),
    FieldMapping("eid", "EID", transform="char"),
    FieldMapping("outqty", "OUTQTY"),
    FieldMapping("qcqty", "QCQTY"),
    FieldMapping("reflineno", "REFLINENO"),
    FieldMapping("s_money", "S_MONEY"),
], batch=4)

_m("TWH16_OUTDTPRD", "twh16_outdtprd", [
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("outbillid", "OUTBILLID", transform="char"),
    FieldMapping("lineno", "LINENO"),
    FieldMapping("itemtyp", "ITEMTYP", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("prddate", "PRDDATE"),
    FieldMapping("outqty", "OUTQTY"),
    FieldMapping("qcqty", "QCQTY"),
    FieldMapping("reflineno", "REFLINENO"),
    FieldMapping("s_money", "S_MONEY"),
], batch=4)

_m("TPC01_PCPLAN", "tpc01_pcplan", [
    FieldMapping("pcplanid", "PCPLANID", transform="char"),
    FieldMapping("slbillid", "SLBILLID", transform="char"),
    FieldMapping("pctyp", "PCTYP", transform="char"),
    FieldMapping("ptimes", "PTIMES"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("plandate", "PLANDATE"),
    FieldMapping("auditman", "AUDITMAN", transform="char"),
    FieldMapping("auditdate", "AUDITDATE"),
    FieldMapping("checkmemo", "CHECKMEMO"),
    FieldMapping("auditflg", "AUDITFLG", transform="char"),
    FieldMapping("type", "TYPE", transform="char"),
], batch=4)

_m("TPC02_PCPLANDT", "tpc02_pcplandt", [
    FieldMapping("pcplanid", "PCPLANID", transform="char"),
    FieldMapping("lineno", "LINENO"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("rgstqty", "RGSTQTY"),
    FieldMapping("units", "UNITS"),
    FieldMapping("storeqty", "STOREQTY"),
    FieldMapping("lowlimit", "LOWLIMIT"),
    FieldMapping("upperlimit", "UPPERLIMIT"),
    FieldMapping("auditqty", "AUDITQTY"),
], batch=4)

_m("TPC12_REGISTER", "tpc12_register", [
    FieldMapping("rgstbillid", "RGSTBILLID", transform="char"),
    FieldMapping("suppliercd", "SUPPLIERCD", transform="char"),
    FieldMapping("pcrep", "PCREP", transform="char"),
    FieldMapping("ptimes", "PTIMES"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("auditman", "AUDITMAN", transform="char"),
    FieldMapping("auditdate", "AUDITDATE"),
    FieldMapping("checkmemo", "CHECKMEMO"),
    FieldMapping("auditflg", "AUDITFLG", transform="char"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("rgstdate", "RGSTDATE"),
    FieldMapping("rgstamt", "RGSTAMT"),
], batch=4)

_m("TPC13_REGISTERDT", "tpc13_registerdt", [
    FieldMapping("rgstbillid", "RGSTBILLID", transform="char"),
    FieldMapping("lineno", "LINENO"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("rgsqty", "RGSQTY"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("units", "UNITS"),
    FieldMapping("rgstprice", "RGSTPRICE"),
    FieldMapping("deliverdate", "DELIVERDATE"),
    FieldMapping("inqty", "INQTY"),
    FieldMapping("auditqty", "AUDITQTY"),
], batch=4)

_m("TSL01_EXTEND", "tsl01_extend", [
    FieldMapping("opbillid", "OPBILLID", transform="char"),
    FieldMapping("slbillid", "SLBILLID", transform="char"),
    FieldMapping("custcd", "CUSTCD", transform="char"),
    FieldMapping("impdate", "IMPDATE", transform="char"),
    FieldMapping("traindate", "TRAINDATE", transform="char"),
    FieldMapping("busityp", "BUSITYP", transform="char"),
    FieldMapping("sltyp", "SLTYP", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("backup", "BACKUP"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("auditflg", "AUDITFLG", transform="char"),
    FieldMapping("auditman", "AUDITMAN", transform="char"),
    FieldMapping("auditdate", "AUDITDATE"),
], batch=4)

_m("TSL10_SLBILL", "tsl10_slbill", [
    FieldMapping("slbillid", "SLBILLID", transform="char"),
    FieldMapping("custbillid", "CUSTBILLID"),
    FieldMapping("sltyp", "SLTYP", transform="char"),
    FieldMapping("custcd", "CUSTCD", transform="char"),
    FieldMapping("rgsdate", "RGSDATE"),
    FieldMapping("senddate", "SENDDATE"),
    FieldMapping("busityp", "BUSITYP", transform="char"),
    FieldMapping("ptimes", "PTIMES"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("memo", "MEMO"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("auditman", "AUDITMAN", transform="char"),
    FieldMapping("auditdate", "AUDITDATE"),
    FieldMapping("checkmemo", "CHECKMEMO"),
    FieldMapping("auditflg", "AUDITFLG", transform="char"),
    FieldMapping("pcplanflg", "PCPLANFLG", transform="char"),
    FieldMapping("rfpcplanid", "RFPCPLANID", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("rgsqty", "RGSQTY"),
    FieldMapping("planqty", "PLANQTY"),
    FieldMapping("openqty", "OPENQTY"),
    FieldMapping("clqty", "CLQTY"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=4)


# ---------- 第5批：其他 ----------

_m("TMM61_DEPOSIT", "tmm61_deposit", [
    FieldMapping("custcd", "CUSTCD"),
    FieldMapping("amount_money", "AMOUNT_MONEY"),
    FieldMapping("updatetime", "UPDATETIME"),
    FieldMapping("rbillid", "R_BILLID"),
    FieldMapping("modelcd", "MODELCD"),
    FieldMapping("modelnm", "MODELNM"),
], batch=5)

_m("TMM41_BOM", "tmm41_bom", [
    FieldMapping("bomcd", "BOMCD", transform="char"),
    FieldMapping("bomnm", "BOMNM"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=5)

_m("TMM42_BOMDT", "tmm42_bomdt", [
    FieldMapping("bomcd", "BOMCD", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("bomqty", "BOMQTY"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("itemtyp", "ITEMTYP"),
], batch=5)

_m("TMM43_EID", "tmm43_eid", [
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("eid", "EID", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("etyp", "ETYP", transform="char"),
    FieldMapping("sflg", "SFLG", transform="char"),
    FieldMapping("refid", "REFID", transform="char"),
    FieldMapping("qcflg", "QCFLG", transform="char"),
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("prddate", "PRDDATE"),
    FieldMapping("itemtyp", "ITEMTYP", transform="char"),
    FieldMapping("new_old", "NEW_OLD", transform="char"),
    FieldMapping("remark", "REMARK"),
    FieldMapping("manufseq", "MANUF_SEQ"),
    FieldMapping("old_degree", "OLD_DEGREE"),
    FieldMapping("isunit", "ISUNIT", transform="char"),
], batch=5)

_m("TMM43_EID_TRACK", "tmm43_eid_track", [
    FieldMapping("seqno", "SEQNO"),
    FieldMapping("type", "TYPE", transform="char"),
    FieldMapping("change_date", "CHANGE_DATE"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("eid", "EID", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("etyp", "ETYP", transform="char"),
    FieldMapping("sflg", "SFLG", transform="char"),
    FieldMapping("refid", "REFID", transform="char"),
    FieldMapping("qcflg", "QCFLG", transform="char"),
    FieldMapping("whcd", "WHCD", transform="char"),
    FieldMapping("prddate", "PRDDATE"),
    FieldMapping("itemtyp", "ITEMTYP", transform="char"),
    FieldMapping("new_old", "NEW_OLD", transform="char"),
    FieldMapping("nsflg", "N_SFLG", transform="char"),
    FieldMapping("nrefid", "N_REFID", transform="char"),
    FieldMapping("nqcflg", "N_QCFLG", transform="char"),
    FieldMapping("nwhcd", "N_WHCD", transform="char"),
    FieldMapping("nprddate", "N_PRDDATE"),
    FieldMapping("nitemtyp", "N_ITEMTYP", transform="char"),
    FieldMapping("nnew_old", "N_NEW_OLD", transform="char"),
    FieldMapping("nitemcd", "N_ITEMCD", transform="char"),
    FieldMapping("netyp", "N_ETYP", transform="char"),
    FieldMapping("remark", "REMARK"),
    FieldMapping("nremark", "N_REMARK"),
    FieldMapping("manufseq", "MANUF_SEQ"),
    FieldMapping("nmanfseq", "N_MANF_SEQ"),
    FieldMapping("old_degree", "OLD_DEGREE"),
    FieldMapping("nold_degree", "N_OLD_DEGREE"),
], batch=5)

_m("TQC10_RESULT", "tqc10_result", [
    FieldMapping("qcbillid", "QCBILLID", transform="char"),
    FieldMapping("optyp", "OPTYP", transform="char"),
    FieldMapping("refbillid", "REFBILLID", transform="char"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("eid", "EID", transform="char"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("auditman", "AUDITMAN", transform="char"),
    FieldMapping("auditflg", "AUDITFLG", transform="char"),
    FieldMapping("auditdate", "AUDITDATE"),
    FieldMapping("qcstatus", "QCSTATUS", transform="char"),
], batch=5)

_m("TKQ01_ATTENDANCE", "tkq01_attendance", [
    FieldMapping("amonth", "AMONTH"),
    FieldMapping("adate", "ADATE"),
    FieldMapping("operid", "OPERID", transform="char"),
    FieldMapping("opernm", "OPERNNM"),
    FieldMapping("arrtime", "ARR_TIME"),
    FieldMapping("leavetime", "LEAVE_TIME"),
    FieldMapping("latecount", "LATECOUNT"),
    FieldMapping("leavecount", "LEAVECOUNT"),
    FieldMapping("punchnum", "PUNCHNUM"),
    FieldMapping("punchdetail", "PUNCHDETAIL"),
    FieldMapping("impnum", "IMP_NUM"),
    FieldMapping("week", "WEEK"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("impdate", "IMP_DATE"),
    FieldMapping("update_time", "UPDATE_TIME"),
    FieldMapping("updator", "UPDATOR", transform="char"),
], batch=5)

_m("TIP01_PRICE", "tip01_price", [
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("busityp", "BUSITYP", transform="char"),
    FieldMapping("unitcd", "UNITCD"),
    FieldMapping("itemprice", "ITEMPRICE"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
    FieldMapping("whtransflg", "WHTRANSFLG", transform="char"),
    FieldMapping("sttransflg", "STTRANSFLG", transform="char"),
], batch=5)

_m("TIP03_ADJPRICE", "tip03_adjprice", [
    FieldMapping("pabillid", "PABILLID", transform="char"),
    FieldMapping("lineno", "LINENO"),
    FieldMapping("itemcd", "ITEMCD", transform="char"),
    FieldMapping("busityp", "BUSITYP", transform="char"),
    FieldMapping("oldprice", "OLDPRICE"),
    FieldMapping("newprice", "NEWPRICE"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("gendate", "GENDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=5)

_m("THT01_HTGL", "tht01_htgl", [
    FieldMapping("htbh", "HTBH"),
    FieldMapping("years", "YEARS", transform="char"),
    FieldMapping("classcd", "CLASSCD"),
    FieldMapping("busityp", "BUSITYP", transform="char"),
    FieldMapping("feetyp", "FEETYP", transform="char"),
    FieldMapping("qdis", "QDIS", transform="char"),
    FieldMapping("qddate", "QDDATE"),
    FieldMapping("htbgr", "HTBGR"),
    FieldMapping("remark", "REMARK"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("yxqfrom", "YXQFROM"),
    FieldMapping("yxqto", "YXQTO"),
    FieldMapping("htamount", "HTAMOUNT"),
], batch=5)

_m("TAC01_FPSK", "tac01_fpsk", [
    FieldMapping("fpbh", "FPBH"),
    FieldMapping("years", "YEARS", transform="char"),
    FieldMapping("classcd", "CLASSCD"),
    FieldMapping("busityp", "BUSITYP", transform="char"),
    FieldMapping("feetyp", "FEETYP", transform="char"),
    FieldMapping("htbh", "HTBH"),
    FieldMapping("htq", "HTQ", transform="char"),
    FieldMapping("qsr", "QSR"),
    FieldMapping("lsh", "LSH"),
    FieldMapping("kpdate", "KPDATE"),
    FieldMapping("kpamount", "KPAMOUNT"),
    FieldMapping("hkdate", "HKDATE"),
    FieldMapping("hkamount", "HKAMOUNT"),
    FieldMapping("sptype", "SPTYPE", transform="char"),
    FieldMapping("spr", "SPR", transform="char"),
    FieldMapping("htqdis", "HTQDIS", transform="char"),
    FieldMapping("htamount", "HTAMOUNT"),
    FieldMapping("remark", "REMARK"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("upddate", "UPDDATE"),
], batch=5)

_m("TTX01_TXKMG", "ttx01_txkmg", [
    FieldMapping("txkno", "TXKNO"),
    FieldMapping("commmode", "COMMMODE"),
    FieldMapping("remark", "REMARK"),
    FieldMapping("by1", "BY1"),
    FieldMapping("by2", "BY2"),
    FieldMapping("operatecd", "OPERCD", transform="char"),
    FieldMapping("upddate", "UPDDATE"),
    FieldMapping("useflg", "USEFLG", transform="char"),
], batch=5)


def get_mappings_by_batch(batch: int) -> list[TableMapping]:
    """获取指定批次的全部映射。"""
    return [m for m in MAPPINGS if m.batch == batch]


def get_batch_order() -> list[int]:
    """返回排好序的批次号列表。"""
    return sorted({m.batch for m in MAPPINGS})
