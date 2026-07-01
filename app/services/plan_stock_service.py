"""预计划库存校验与采购需求触发服务。

按 `docs/core/预计划机型联动与采购触发技术方案.md` 实现:
- check_stock: 查询机型对应成品的库存汇总（TWH11 批次库存，回答"够不够"）
- list_available_eids: 查询机型可用设备列表（TMM43_EID 设备库存，回答"选哪台"）
- expand_bom_and_check: BOM 展开并校验配件齐套
- trigger_procurement: 库存不足时自动生成采购需求(tpc01_pcplan)

关联链路(对齐 PB 语义,Bom.useflg='1' 即在产可选):
  pos_item(机型编码=item_cd) → tmm12_items.item_cd → tmm41_bom.bomcd → tmm42_bomdt 配件明细
  → twh11_detail 库存校验 → 不足则生成采购需求

TWH11_DETAIL 与 TMM43_EID 联动关系:
  TWH11_DETAIL: 仓库×物料×品级 的库存余量（数量维度，无 EID）
  TMM43_EID:    逐台设备的身份与状态（EID 维度，含 asset_type/sflg/qcflg）
  两者通过 (itemcd, whcd) 联动，出入库审核时同步更新。
  - check_stock 查 TWH11 → 回答"成品库有多少台"
  - list_available_eids 查 TMM43_EID → 回答"具体是哪些台、各自什么资产类型"

押金/售价改从 tip01_price 读取(busityp=40 押金/10 销售价),
DepositPosModel 已弃用,仅保留表结构供历史数据迁移参考。
"""
from __future__ import annotations

import logging
from datetime import datetime, UTC
from typing import Any

from app.extensions import db
from app.models.master import Item, Bom, BomDt, Eid, SysCode
from app.models.warehouse import StockDetail, Warehouse
from app.models.procurement import PurchasePlan
from app.services.bom_service import BomService
from app.services.procurement_service import PurchasePlanService

logger = logging.getLogger(__name__)


class PlanStockService:
    """预计划库存校验与采购需求触发。"""

    @staticmethod
    def check_stock(model_cd: str) -> dict[str, Any]:
        """查询机型对应成品的库存汇总。

        Args:
            model_cd: 机型编码(即 item_cd)
        Returns:
            {model_cd, item_cd, total_qty, wh_details: [{whcd, whnm, qty}]}
        """
        item_cd = model_cd.strip() if model_cd else ""
        if not item_cd:
            return {
                "model_cd": model_cd,
                "item_cd": None,
                "total_qty": 0,
                "wh_details": [],
                "message": "机型编码为空,无法查询库存",
            }

        # 查 twh11_detail 汇总库存(仅 useflg=1 且 itemqty>0)
        rows = (
            db.session.query(
                StockDetail.whcd,
                Warehouse.whnm,
                db.func.sum(StockDetail.itemqty),
            )
            .outerjoin(Warehouse, StockDetail.whcd == Warehouse.whcd)
            .filter(
                StockDetail.itemcd == item_cd,
                StockDetail.useflg == "1",
                StockDetail.itemqty > 0,
            )
            .group_by(StockDetail.whcd, Warehouse.whnm)
            .all()
        )
        wh_details = [
            {"whcd": r[0], "whnm": r[1] or "", "qty": int(r[2] or 0)}
            for r in rows
        ]
        total = sum(d["qty"] for d in wh_details)
        return {
            "model_cd": model_cd,
            "item_cd": item_cd,
            "total_qty": total,
            "wh_details": wh_details,
        }

    @staticmethod
    def list_available_eids(
        model_cd: str,
        whtyp: str | None = "03",
        asset_types: list[str] | None = None,
        itemtyp: list[str] | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """查询机型可用设备列表（TMM43_EID 设备维度，供预计划设备选择）。

        与 check_stock 的区别:
        - check_stock 查 TWH11_DETAIL（批次库存余量），回答"够不够"
        - list_available_eids 查 TMM43_EID（逐台设备），回答"选哪台"

        Args:
            model_cd: 机型编码(即 item_cd)
            whtyp: 仓库类型过滤(WT 字典，默认 '03' 成品库；None=不限)
            asset_types: 资产类型过滤(AT 字典，默认 ['01','02','03'] 新机+旧机+翻新机；None=不限)
            itemtyp: 物料类型过滤(QC 字典，默认 ['GA','GB','GC'] 合格+让步+降级；
                     None=不限；传单个值时按单值过滤)
            page: 页码
            per_page: 每页条数
        Returns:
            {model_cd, item_cd, total, items: [{eid, itemcd, whcd, whnm,
              asset_type, asset_type_nm, itemtyp, itemtyp_nm, sflg, qcflg}]}
        """
        item_cd = model_cd.strip() if model_cd else ""
        if not item_cd:
            return {
                "model_cd": model_cd, "item_cd": None,
                "total": 0, "items": [],
                "message": "机型编码为空,无法查询可用设备",
            }

        # 默认资产类型：新机 + 旧机 + 翻新机（旧机只要可用也可租赁或临时给客户使用）
        if asset_types is None:
            asset_types = ["01", "02", "03"]
        # 默认物料类型：合格 + 让步 + 降级（排除 BF 报废、BH 返修、DJ 待检、QA 质检中）
        if itemtyp is None:
            itemtyp = ["GA", "GB", "GC"]
        elif isinstance(itemtyp, str):
            itemtyp = [itemtyp]

        # AT 字典（资产类型名称）
        at_map = {
            r[0]: r[1] for r in db.session.query(SysCode.code_cd, SysCode.code_nm)
            .filter(SysCode.code_typ == "AT", SysCode.useflg == "1").all()
        }
        # QC 字典（物料类型名称）
        qc_map = {
            r[0]: r[1] for r in db.session.query(SysCode.code_cd, SysCode.code_nm)
            .filter(SysCode.code_typ == "QC", SysCode.useflg == "1").all()
        }

        q = (
            db.session.query(Eid, Warehouse.whnm)
            .outerjoin(Warehouse, Eid.whcd == Warehouse.whcd)
            .filter(
                Eid.itemcd == item_cd,
                Eid.useflg == "1",
                Eid.sflg == "8",  # 在库
            )
        )
        # 仓库类型过滤（通过 Warehouse.whtyp 间接过滤）
        if whtyp is not None:
            q = q.filter(Warehouse.whtyp == whtyp)
        # 资产类型过滤
        if asset_types:
            q = q.filter(Eid.asset_type.in_(asset_types))
        # 物料类型过滤
        if itemtyp:
            q = q.filter(Eid.itemtyp.in_(itemtyp))

        total = q.count()
        rows = (
            q.order_by(Eid.asset_type, Eid.eid)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        items = []
        for eid_rec, whnm in rows:
            at = eid_rec.asset_type or ""
            it = eid_rec.itemtyp or ""
            items.append({
                "eid": eid_rec.eid,
                "itemcd": eid_rec.itemcd,
                "whcd": eid_rec.whcd or "",
                "whnm": whnm or "",
                "asset_type": at,
                "asset_type_nm": at_map.get(at, ""),
                "itemtyp": it,
                "itemtyp_nm": qc_map.get(it, ""),
                "sflg": eid_rec.sflg or "",
                "qcflg": eid_rec.qcflg or "",
            })

        return {
            "model_cd": model_cd,
            "item_cd": item_cd,
            "total": total,
            "items": items,
        }

    @staticmethod
    def expand_bom_and_check(model_cd: str, qty: int = 1) -> dict[str, Any]:
        """BOM 展开并校验配件齐套。

        Args:
            model_cd: 机型编码
            qty: 需求数量(默认 1 台)
        Returns:
            {model_cd, item_cd, qty, lines: [{itemcd, item_nm, need_qty, stock_qty, enough}], all_enough}
        """
        item_cd = model_cd.strip() if model_cd else ""
        if not item_cd:
            return {
                "model_cd": model_cd,
                "item_cd": None,
                "qty": qty,
                "lines": [],
                "all_enough": False,
                "message": "机型编码为空,无法展开 BOM",
            }

        # 调 BomService.expand(不传 whcd,汇总所有仓库库存)
        expanded = BomService.expand(item_cd, qty, whcd=None)
        if not expanded:
            return {
                "model_cd": model_cd,
                "item_cd": item_cd,
                "qty": qty,
                "lines": [],
                "all_enough": False,
                "message": f"物料 {item_cd} 未配置 BOM",
            }

        # 查各配件库存汇总
        itemcds = [ln["itemcd"] for ln in expanded.get("lines", []) if ln.get("itemcd")]
        stock_map: dict[str, int] = {}
        if itemcds:
            stock_rows = (
                db.session.query(
                    StockDetail.itemcd,
                    db.func.sum(StockDetail.itemqty),
                )
                .filter(
                    StockDetail.itemcd.in_(itemcds),
                    StockDetail.useflg == "1",
                    StockDetail.itemqty > 0,
                )
                .group_by(StockDetail.itemcd)
                .all()
            )
            stock_map = {r[0]: int(r[1] or 0) for r in stock_rows}

        lines = []
        all_enough = True
        for ln in expanded.get("lines", []):
            itemcd = ln.get("itemcd", "")
            need = int(ln.get("need_qty", 0))
            stock = stock_map.get(itemcd, 0)
            enough = stock >= need
            if not enough:
                all_enough = False
            lines.append({
                "itemcd": itemcd,
                "item_nm": ln.get("item_nm", ""),
                "need_qty": need,
                "stock_qty": stock,
                "enough": enough,
            })
        return {
            "model_cd": model_cd,
            "item_cd": item_cd,
            "qty": qty,
            "lines": lines,
            "all_enough": all_enough,
        }

    @staticmethod
    def trigger_procurement(
        planno: str,
        model_cd: str,
        qty: int = 1,
        operator: str = "",
    ) -> dict[str, Any]:
        """库存不足时触发采购需求。

        Args:
            planno: 预计划单号(作为 slbillid)
            model_cd: 机型编码
            qty: 需求数量
            operator: 操作员(采购需求创建者)
        Returns:
            {pcplanid, created_lines, skipped} 或 {error}
        """
        # 重复触发防护: 同一预计划已生成采购需求则跳过
        existing = db.session.query(PurchasePlan).filter(
            PurchasePlan.slbillid == planno,
            PurchasePlan.useflg == "1",
        ).count()
        if existing > 0:
            return {
                "skipped": True,
                "message": f"预计划 {planno} 已生成 {existing} 个采购需求,跳过重复触发",
            }

        bom_result = PlanStockService.expand_bom_and_check(model_cd, qty)
        if bom_result.get("item_cd") is None:
            return {"error": bom_result.get("message", "机型未配置 item_cd")}

        lines = bom_result.get("lines", [])
        if not lines:
            return {"error": bom_result.get("message", "BOM 无配件明细")}

        # 筛选库存不足的配件
        shortage = [ln for ln in lines if not ln["enough"]]
        if not shortage:
            return {
                "skipped": True,
                "message": "配件齐套,无需触发采购需求",
            }

        # 构造采购需求明细
        details = []
        for ln in shortage:
            need_qty = ln["need_qty"] - ln["stock_qty"]
            if need_qty <= 0:
                continue
            details.append({
                "itemcd": ln["itemcd"],
                "rgstqty": need_qty,
                "storeqty": ln["stock_qty"],
                "item_usage": "sale",
            })

        if not details:
            return {"skipped": True, "message": "计算后无需采购"}

        # 创建采购需求
        plan_data = {
            "slbillid": planno,
            "pctyp": "12",  # 订单采购(与预计划强关联)
            "plandate": datetime.now(UTC),
            "memo": f"预计划 {planno} 机型 {model_cd} 库存不足自动触发",
        }
        try:
            result = PurchasePlanService.create(
                data=plan_data,
                details=details,
                creator=operator or "SYSTEM",
            )
            logger.info(
                "预计划 %s 触发采购需求 %s,共 %d 条配件",
                planno, result.get("pcplanid"), len(details),
            )
            return {
                "pcplanid": result.get("pcplanid"),
                "created_lines": details,
                "total": len(details),
            }
        except Exception as e:
            logger.exception("预计划 %s 触发采购需求失败", planno)
            return {"error": str(e)}
