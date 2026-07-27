"""服务权益判定服务（1a 阶段，6 级优先级 + SR 默认推导）。

对齐行业 EAM/FSM 六层模型：
  L3 Business Model → cust_pos_rl.business_mode（BM_S 字典）
  L4 Service Responsibility → dispatch.service_responsibility（SR 字典）
  L5 Entitlement → resolve_entitlement() 6 级优先级判定
  L6 Billing Rule → c_type 推荐 + TIP01_PRICE 价格带出

1a 阶段：优先级 1-2（特殊协议/维保合同）写死返回 None，后续建表接入。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.extensions import db
from app.models.master import CustPosRl, Eid


@dataclass
class Entitlement:
    """服务权益判定结果。"""

    free: bool
    reason: str


# BM_S 字典映射（与 tmm31_syscodes code_typ='BM_S' 对齐）
BM_S_DICT = {
    '01': '销售',
    '02': '租赁',
    '03': '借用',
    '04': '代维',
    '05': '寄售',
    '06': '试用',
    '07': '免费投放',
    '08': '合作运营',
}

# SR 字典映射（与 tmm31_syscodes code_typ='SR' 对齐）
SR_INTERNAL = '01'  # 内部
SR_MANUFACTURER = '02'  # 厂商
SR_CONTRACTOR = '03'  # 代维

# OW 字典码值（与 tmm43_eid.asset_owner 对齐）
OW_COMMERCIAL = '01'  # 商用电子
OW_TONGFANG_INFO = '02'  # 通方信息
OW_CUSTOMER = '03'  # 门店资产
OW_HAISHENG = '04'  # 海晟


def get_special_agreement(cust_cd: str) -> Optional[dict]:
    """查询特殊客户协议（1a 阶段返回 None，后续建 special_agreement 表接入）。

    后续实现：
        return db.session.query(SpecialAgreement).filter_by(
            cust_cd=cust_cd, useflg='1'
        ).filter(now() >= effective_date,
                 or_(expire_date.is_(None), now() <= expire_date)).first()
    """
    # 1a 阶段：写死返回 None
    return None


def get_service_contract(eid: str) -> Optional[dict]:
    """查询维保合同（1a 阶段返回 None，后续建 service_contract 表接入）。

    后续实现：
        return db.session.query(ServiceContract).filter(
            or_(eid == eid, cust_cd == cust_cd), useflg='1'
        ).filter(now() >= effective_date, now() <= expire_date).first()
    """
    # 1a 阶段：写死返回 None
    return None


def resolve_entitlement(
    eid: Eid,
    cust_pos_rl: Optional[CustPosRl],
    damage_type: Optional[str] = None,
) -> Entitlement:
    """判定设备当前服务权益（6级优先级 + 人为损坏判定）。

    优先级：
      0. 人为损坏 — 最高优先，直接收费
      1. 特殊客户协议
      2. 维保合同
      3. 租赁/借用/免费投放/合作运营（非人为）→ 公司承担
      3a. 代维 → 按合同
      4. 厂家保修 — warranty_expire 判定
      5. Owner 默认规则 — asset_owner 兜底
      6. 异常兜底 — 默认收费

    damage_type: '1'=非人为 / '2'=人为损坏 / None=未判定
    """
    business_mode = cust_pos_rl.business_mode if cust_pos_rl else None
    asset_owner = eid.asset_owner if eid else None
    now = datetime.now()

    # 0. 人为损坏 → 一律收费（最高优先）
    if damage_type == '2':
        return Entitlement(free=False, reason="人为损坏")

    # 1. 特殊客户协议
    if cust_pos_rl:
        special = get_special_agreement(cust_pos_rl.cust_cd)
        if special:
            return Entitlement(
                free=special.get('is_free', True),
                reason=f"特殊协议: {special.get('name', '')}",
            )

    # 2. 维保合同
    if eid:
        contract = get_service_contract(eid.eid)
        if contract:
            return Entitlement(
                free=contract.get('is_free', True),
                reason=f"维保合同: {contract.get('name', '')}",
            )

    # 3. 代维 → 按合同
    if business_mode == '04':
        return Entitlement(free=False, reason="代维，按合同（无合同默认收费）")

    # 4. 租赁/借用/免费投放/合作运营 → 非人为则公司承担
    if business_mode in ('02', '03', '07', '08'):
        return Entitlement(free=True, reason=f"{BM_S_DICT.get(business_mode, '未知')}，公司承担")

    # 5. 厂家保修（销售/寄售/试用模式按保修期判定）
    if business_mode in ('01', '05', '06'):
        if eid and eid.warranty_expire and now <= eid.warranty_expire:
            return Entitlement(free=True, reason="保内")
        return Entitlement(free=False, reason="过保")

    # 6. Owner 默认规则（存量数据无 business_mode 时兜底）
    if asset_owner == OW_COMMERCIAL:  # 商用电子
        return Entitlement(free=True, reason="商用电子（默认免费）")
    if asset_owner == OW_HAISHENG:  # 海晟
        return Entitlement(free=False, reason="海晟（按合同，无合同默认收费）")

    # 7. 异常兜底
    return Entitlement(free=False, reason="门店资产（默认收费）")


def resolve_service_responsibility(eid: Optional[Eid]) -> str:
    """派工默认服务责任方（SR 字典）。

    推导规则：
      - 商用电子/通方信息/门店资产 → '01' 内部（我们自己的工程师团队维护）
      - 海晟设备（asset_owner='04'）→ '03' 代维（第三方设备，按代维合同）
      - '02' 厂商仅用于非我方设备且存在原厂保修的场景，需手动选择

    前端集成：派工 Tab 表单打开时调用此函数自动设默认值，操作人员可手动覆盖。
    """

    # 海晟设备 → 代维
    if eid and eid.asset_owner == OW_HAISHENG:
        return SR_CONTRACTOR

    # 其他 → 内部（商用电子/通方信息/门店资产均我们自己的团队维护）
    return SR_INTERNAL


# 旧件处理策略码值
DISPOSAL_RECYCLE = 'recycle'  # 入库回收
DISPOSAL_SCRAP = 'scrap'  # 报废（in_wh='2'）
DISPOSAL_CONTRACT = 'contract'  # 按代维合同


def resolve_old_part_disposal(eid: Optional[Eid], entitlement: Entitlement) -> str:
    """旧件处理策略（基于 Entitlement + Ownership 双维度）。

    返回值：'recycle' 入库回收 / 'scrap' 报废 / 'contract' 按代维合同

    规则：
      - 保内（entitlement.free=True 且 reason 含"保内"）→ 入库回收（厂商/公司赔付）
      - 过保按 asset_owner 判定：
        - 01 商用电子 → 入库回收（公司承担）
        - 03 门店资产 → 报废（客户承担，in_wh='2'）
        - 04 海晟 → 按代维合同
        - 其他 → 报废（默认）
    """
    asset_owner = eid.asset_owner if eid else None

    # 保内 → 入库回收（厂商/公司赔付）
    if entitlement.free and '保内' in entitlement.reason:
        return DISPOSAL_RECYCLE

    # 过保按 asset_owner 判定
    if asset_owner == OW_COMMERCIAL:  # 商用电子
        return DISPOSAL_RECYCLE  # 公司承担
    if asset_owner == OW_CUSTOMER:  # 门店资产
        return DISPOSAL_SCRAP  # 客户承担，in_wh='2'
    if asset_owner == OW_HAISHENG:  # 海晟
        return DISPOSAL_CONTRACT  # 按代维合同

    # 默认报废
    return DISPOSAL_SCRAP


# tip01_price.busityp 码值
BUSITYP_SALE = '10'  # 销售价
BUSITYP_COST = '20'  # 采购价（成本价）
BUSITYP_MAINTENANCE = '30'  # 维护品价格
BUSITYP_DEPOSIT = '40'  # 押金


def resolve_price(cust_cd: str, itemcd: str) -> Optional[float]:
    """价格带出规则（按客户分类取销售价/成本价）。

    tip01_price.busityp:
      '10' = 销售价
      '20' = 采购价（成本价）
      '30' = 维护品价格
      '40' = 押金

    Customer 无 pricetyp 字段（PB 原系统未迁移），暂按 class_cd 判断。
    后续可加 pricetyp 字段或演进为规则表。

    调用示例（配件更换时）：
        price = resolve_price(record.store_id, accessories_update.itemcd)
        if price is not None:
            accessories_update.price = price
            if accessories_update.c_type in ('1', '2', '4'):
                accessories_update.payje = price
    """
    from app.models.master import Customer
    from app.models.inventory import Price

    customer = db.session.get(Customer, cust_cd)
    if not customer:
        return None

    # 按客户分类决定取哪个价格
    # class_cd='24' 或特定分类 → 成本价（busityp='20'）
    # 其他 → 销售价（busityp='10'）
    # TODO: 后续加 pricetyp 字段或规则表，当前简化为销售价
    busityp = BUSITYP_SALE

    price = (
        db.session.query(Price)
        .filter_by(itemcd=itemcd, busityp=busityp, useflg='1')
        .filter(Price.is_current.is_(True))
        .first()
    )

    return float(price.itemprice) if price and price.itemprice is not None else None
