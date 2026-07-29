"""服务权益判定模型（P2 Entitlement 完整化）。

对应数据库表：
  特殊客户协议：tit71_special_agreement
  维保合同：tit72_service_contract

用于 entitlement_service.resolve_entitlement() 优先级 1-2 判定。
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel


class SpecialAgreement(BaseModel):
    """特殊客户协议（TIT71_SPECIAL_AGREEMENT）。

    优先级 1：按 cust_cd 匹配，有效期内的特殊免费/收费协议。
    """

    __tablename__ = "tit71_special_agreement"

    agreement_id = db.Column(db.String(20), primary_key=True, comment="协议ID")
    cust_cd = db.Column(db.String(8), nullable=False, index=True, comment="客户编码")
    agreement_nm = db.Column(db.String(100), comment="协议名称")
    is_free = db.Column(db.String(1), default="1", comment="是否免费: 1=免费 0=收费")
    effective_date = db.Column(db.Date, nullable=False, comment="生效日期")
    expire_date = db.Column(db.Date, comment="失效日期（空=长期有效）")
    remark = db.Column(db.String(200), comment="备注")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    creator = db.Column(db.String(20), comment="创建人")
    updator = db.Column(db.String(20), comment="更新人")


class ServiceContract(BaseModel):
    """维保合同（TIT72_SERVICE_CONTRACT）。

    优先级 2：按 eid 或 cust_cd 匹配，有效期内的维保合同。
    """

    __tablename__ = "tit72_service_contract"

    contract_id = db.Column(db.String(20), primary_key=True, comment="合同ID")
    contract_no = db.Column(db.String(30), comment="合同编号")
    cust_cd = db.Column(db.String(8), index=True, comment="客户编码")
    eid = db.Column(db.String(13), index=True, comment="设备ID")
    contract_nm = db.Column(db.String(100), comment="合同名称")
    is_free = db.Column(db.String(1), default="1", comment="是否免费: 1=免费 0=收费")
    effective_date = db.Column(db.Date, nullable=False, comment="生效日期")
    expire_date = db.Column(db.Date, nullable=False, comment="失效日期")
    remark = db.Column(db.String(200), comment="备注")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    creator = db.Column(db.String(20), comment="创建人")
    updator = db.Column(db.String(20), comment="更新人")
