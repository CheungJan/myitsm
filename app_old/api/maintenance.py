"""
维修单管理 API（ITSM核心）。

作者：Cascade
创建时间：2026-04-08
变更时间：2026-04-08

端点列表：
- GET /api/v1/maintenances：维修单列表
- GET /api/v1/maintenances/<id>：维修单详情
- GET /api/v1/maintenances/<id>/pos-details：配件明细
- GET /api/v1/maintenances/<id>/d2d-records：上门服务记录
- POST /api/v1/maintenances：创建维修单
- POST /api/v1/maintenances/<id>/pos-details：新增配件明细
- POST /api/v1/maintenances/<id>/d2d-records：新增上门服务记录
- POST /api/v1/maintenances/<id>/cancel：取消维修单

注意事项：
    - 集成统一状态机（优化2）
    - 对应 itsm.pbl 的维修单管理功能
"""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from app.services.maintenance_service import MaintenanceService
from app.services.maintenance_d2d_service import MaintenanceD2DService

__all__ = ["maintenance_bp"]

maintenance_bp = Blueprint("maintenance", __name__)
_service = MaintenanceService()
_d2d_service = MaintenanceD2DService()


def _bad_request(message: str):
    """生成统一 400 响应。"""
    payload = {
        "code": 400,
        "message": message,
        "data": {"request_id": getattr(g, "request_id", "")},
    }
    return jsonify(payload), 400


@maintenance_bp.get("/maintenances")
def list_maintenances():
    """
    获取维修单列表。

    查询参数：
        - cust_cd: 客户代码
        - status: 状态码（00/01/04/02/05/09）

    返回值：
        Response: 统一结构 JSON 响应
    """
    cust_cd = request.args.get("cust_cd")
    status = request.args.get("status")

    maintenances = _service.list_maintenances(cust_cd=cust_cd, status=status)
    payload = {
        "code": 0,
        "message": "成功",
        "data": maintenances,
    }
    return jsonify(payload), 200


@maintenance_bp.get("/maintenances/<maintenance_id>")
def get_maintenance(maintenance_id: str):
    """
    获取维修单详情。

    参数：
        maintenance_id: 维修单ID

    返回值：
        Response: 统一结构 JSON 响应
    """
    maintenance = _service.get_maintenance_detail(maintenance_id)
    if maintenance is None:
        payload = {
            "code": 404,
            "message": "维修单不存在",
            "data": {"request_id": getattr(g, "request_id", "")},
        }
        return jsonify(payload), 404

    payload = {
        "code": 0,
        "message": "成功",
        "data": maintenance,
    }
    return jsonify(payload), 200


@maintenance_bp.get("/maintenances/<maintenance_id>/transitions")
def get_allowed_transitions(maintenance_id: str):
    """
    获取维修单允许的状态流转。

    参数：
        maintenance_id: 维修单ID

    返回值：
        Response: 统一结构 JSON 响应
    """
    transitions = _service.get_allowed_transitions(maintenance_id)
    payload = {
        "code": 0,
        "message": "成功",
        "data": {
            "maintenance_id": maintenance_id,
            "allowed_transitions": transitions,
        },
    }
    return jsonify(payload), 200


@maintenance_bp.post("/maintenances")
def create_maintenance():
    """
    创建维修单（初始状态：草稿）。

    请求体：
        {
            "company_id": "公司ID",
            "store_id": "门店ID",
            "cust_cd": "客户代码",
            "short_description": "故障简述",
            "detail_description": "详细描述",
            "device_id": "设备ID",
            "oper_cd": "操作员"
        }

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}
    oper_cd = data.get("oper_cd", "").strip()

    if not oper_cd:
        return _bad_request("缺少参数 oper_cd")

    maintenance_info = {
        "company_id": data.get("company_id", ""),
        "store_id": data.get("store_id", ""),
        "cust_cd": data.get("cust_cd", ""),
        "short_description": data.get("short_description", ""),
        "detail_description": data.get("detail_description", ""),
        "device_id": data.get("device_id", ""),
    }

    maintenance = _service.create_maintenance(maintenance_info, oper_cd)
    if maintenance is None:
        payload = {
            "code": 500,
            "message": "创建失败",
            "data": {"request_id": getattr(g, "request_id", "")},
        }
        return jsonify(payload), 500

    payload = {
        "code": 0,
        "message": "维修单创建成功",
        "data": maintenance,
    }
    return jsonify(payload), 201


@maintenance_bp.post("/maintenances/<maintenance_id>/transition")
def transition_state(maintenance_id: str):
    """
    执行状态流转（通用）。

    请求体：
        {
            "to_status": "目标状态码",
            "oper_cd": "操作员",
            "remark": "备注（可选）"
        }

    参数：
        maintenance_id: 维修单ID

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}
    to_status = data.get("to_status", "").strip()
    oper_cd = data.get("oper_cd", "").strip()
    remark = data.get("remark", "").strip()

    if not to_status:
        return _bad_request("缺少参数 to_status")
    if not oper_cd:
        return _bad_request("缺少参数 oper_cd")

    result = _service.transition_state(maintenance_id, to_status, oper_cd, remark)
    if not result["success"]:
        payload = {
            "code": 400,
            "message": result["error"],
            "data": {
                "allowed_transitions": result.get("allowed_transitions", []),
                "request_id": getattr(g, "request_id", ""),
            },
        }
        return jsonify(payload), 400

    payload = {
        "code": 0,
        "message": result["message"],
        "data": result,
    }
    return jsonify(payload), 200


@maintenance_bp.post("/maintenances/<maintenance_id>/dispatch")
def dispatch(maintenance_id: str):
    """
    派工（PLANNED → DISPATCHED）。

    请求体：
        {
            "engineer_id": "工程师ID",
            "oper_cd": "操作员"
        }

    参数：
        maintenance_id: 维修单ID

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}
    engineer_id = data.get("engineer_id", "").strip()
    oper_cd = data.get("oper_cd", "").strip()

    if not engineer_id:
        return _bad_request("缺少参数 engineer_id")
    if not oper_cd:
        return _bad_request("缺少参数 oper_cd")

    result = _service.dispatch(maintenance_id, engineer_id, oper_cd)
    if not result["success"]:
        payload = {
            "code": 400,
            "message": result["error"],
            "data": {"request_id": getattr(g, "request_id", "")},
        }
        return jsonify(payload), 400

    payload = {
        "code": 0,
        "message": "派工成功",
        "data": result,
    }
    return jsonify(payload), 200


@maintenance_bp.post("/maintenances/<maintenance_id>/start")
def start_work(maintenance_id: str):
    """
    开始实施（DISPATCHED → IN_PROGRESS）。

    请求体：
        {
            "oper_cd": "操作员"
        }

    参数：
        maintenance_id: 维修单ID

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}
    oper_cd = data.get("oper_cd", "").strip()

    if not oper_cd:
        return _bad_request("缺少参数 oper_cd")

    result = _service.start_work(maintenance_id, oper_cd)
    if not result["success"]:
        payload = {
            "code": 400,
            "message": result["error"],
            "data": {"request_id": getattr(g, "request_id", "")},
        }
        return jsonify(payload), 400

    payload = {
        "code": 0,
        "message": "开始实施",
        "data": result,
    }
    return jsonify(payload), 200


@maintenance_bp.post("/maintenances/<maintenance_id>/complete")
def complete(maintenance_id: str):
    """
    完成维修（IN_PROGRESS → COMPLETED）。

    请求体：
        {
            "oper_cd": "操作员"
        }

    参数：
        maintenance_id: 维修单ID

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}
    oper_cd = data.get("oper_cd", "").strip()

    if not oper_cd:
        return _bad_request("缺少参数 oper_cd")

    result = _service.complete(maintenance_id, oper_cd)
    if not result["success"]:
        payload = {
            "code": 400,
            "message": result["error"],
            "data": {"request_id": getattr(g, "request_id", "")},
        }
        return jsonify(payload), 400

    payload = {
        "code": 0,
        "message": "维修完成",
        "data": result,
    }
    return jsonify(payload), 200


@maintenance_bp.post("/maintenances/<maintenance_id>/cancel")
def cancel(maintenance_id: str):
    """
    取消维修单。

    请求体：
        {
            "reason": "取消原因",
            "oper_cd": "操作员"
        }

    参数：
        maintenance_id: 维修单ID

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}
    reason = data.get("reason", "").strip()
    oper_cd = data.get("oper_cd", "").strip()

    if not reason:
        return _bad_request("缺少参数 reason")
    if not oper_cd:
        return _bad_request("缺少参数 oper_cd")

    result = _service.cancel(maintenance_id, reason, oper_cd)
    if not result["success"]:
        payload = {
            "code": 400,
            "message": result["error"],
            "data": {"request_id": getattr(g, "request_id", "")},
        }
        return jsonify(payload), 400

    payload = {
        "code": 0,
        "message": "维修单已取消",
        "data": result,
    }
    return jsonify(payload), 200


@maintenance_bp.get("/maintenances/<maintenance_id>/pos-details")
def list_pos_details(maintenance_id: str):
    """
    获取维护单配件明细（TIT10_POS_DETAIL）。

    参数：
        maintenance_id: 维护单ID

    返回值：
        Response: 统一结构 JSON 响应
    """
    details = _service.list_pos_details(maintenance_id)
    payload = {
        "code": 0,
        "message": "成功",
        "data": {
            "maintenance_id": maintenance_id,
            "items": details,
        },
    }
    return jsonify(payload), 200


@maintenance_bp.post("/maintenances/<maintenance_id>/pos-details")
def create_pos_detail(maintenance_id: str):
    """
    新增维护单配件明细（TIT10_POS_DETAIL）。

    请求体：
        {
            "sm_id": 1,
            "device_id": "设备ID",
            "accessories_id": "配件编号",
            "creator": "创建人",
            "item_cd": "配件类型（可选）",
            "noflg": "新旧标记（可选，默认N）",
            "status": "状态（可选，默认1）"
        }

    参数：
        maintenance_id: 维护单ID

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}

    sm_id = data.get("sm_id")
    device_id = str(data.get("device_id", "")).strip()
    accessories_id = str(data.get("accessories_id", "")).strip()
    creator = str(data.get("creator", "")).strip()
    item_cd = str(data.get("item_cd", "")).strip()
    noflg = str(data.get("noflg", "N")).strip() or "N"
    status = str(data.get("status", "1")).strip() or "1"

    if sm_id is None:
        return _bad_request("缺少参数 sm_id")
    if not device_id:
        return _bad_request("缺少参数 device_id")
    if not accessories_id:
        return _bad_request("缺少参数 accessories_id")
    if not creator:
        return _bad_request("缺少参数 creator")

    try:
        sm_id_int = int(sm_id)
    except (TypeError, ValueError):
        return _bad_request("参数 sm_id 必须为整数")

    result = _service.create_pos_detail(
        maintenance_id=maintenance_id,
        sm_id=sm_id_int,
        device_id=device_id,
        accessories_id=accessories_id,
        creator=creator,
        item_cd=item_cd,
        noflg=noflg,
        status=status,
    )
    if not result["success"]:
        payload = {
            "code": 400,
            "message": result["error"],
            "data": {"request_id": getattr(g, "request_id", "")},
        }
        return jsonify(payload), 400

    payload = {
        "code": 0,
        "message": "配件明细新增成功",
        "data": result,
    }
    return jsonify(payload), 201


@maintenance_bp.get("/maintenances/<maintenance_id>/d2d-records")
def list_d2d_records(maintenance_id: str):
    """
    获取上门服务记录列表（TIT23_MAINTENANCE_D2D）。

    查询参数：
        - d2d_type: 上门类型（可选，'1'=维护）

    参数：
        maintenance_id: 维护单ID

    返回值：
        Response: 统一结构 JSON 响应
    """
    d2d_type = request.args.get("d2d_type")

    result = _d2d_service.list_d2d_records(
        maintenance_id=maintenance_id,
        d2d_type=d2d_type,
    )
    if not result["success"]:
        payload = {
            "code": 400,
            "message": result.get("error", "查询失败"),
            "data": {"request_id": getattr(g, "request_id", "")},
        }
        return jsonify(payload), 400

    payload = {
        "code": 0,
        "message": "上门服务记录查询成功",
        "data": result,
    }
    return jsonify(payload), 200


@maintenance_bp.post("/maintenances/<maintenance_id>/d2d-records")
def create_d2d_record(maintenance_id: str):
    """
    新增上门服务记录（TIT23_MAINTENANCE_D2D）。

    请求体：
        {
            "business_operation_id": 1,
            "d2d_engineer": "工程师编码",
            "arrive_time": "2026-04-14 10:00:00",
            "leave_time": "2026-04-14 12:00:00",
            "jjbz": "计价标志",
            "d2d_description": "服务描述",
            "d2d_phone": "联系电话",
            "d2d_type": "1",
            "creator": "创建人"
        }

    参数：
        maintenance_id: 维护单ID

    返回值：
        Response: 统一结构 JSON 响应
    """
    data = request.get_json() or {}

    business_operation_id = data.get("business_operation_id")
    if business_operation_id is None:
        return _bad_request("缺少参数 business_operation_id")

    try:
        business_operation_id_int = int(business_operation_id)
    except (TypeError, ValueError):
        return _bad_request("参数 business_operation_id 必须为整数")

    creator = str(data.get("creator") or getattr(g, "user_cd", "")).strip()
    if not creator:
        return _bad_request("缺少参数 creator")

    result = _d2d_service.create_d2d_record(
        maintenance_id=maintenance_id,
        business_operation_id=business_operation_id_int,
        creator=creator,
        d2d_engineer=data.get("d2d_engineer"),
        arrive_time=data.get("arrive_time"),
        leave_time=data.get("leave_time"),
        jjbz=data.get("jjbz"),
        d2d_description=data.get("d2d_description"),
        d2d_phone=data.get("d2d_phone"),
        old_business_id=data.get("old_business_id"),
        d2d_group=data.get("d2d_group"),
        d2d_type=data.get("d2d_type") or "1",
        pos_status=data.get("pos_status"),
        pos_status1=data.get("pos_status1"),
    )
    if not result["success"]:
        payload = {
            "code": 400,
            "message": result.get("error", "新增失败"),
            "data": {"request_id": getattr(g, "request_id", "")},
        }
        return jsonify(payload), 400

    payload = {
        "code": 0,
        "message": "上门服务记录新增成功",
        "data": result,
    }
    return jsonify(payload), 201
