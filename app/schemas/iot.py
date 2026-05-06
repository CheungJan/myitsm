"""IoT数据监控模块请求/响应 Schema（Tier-3 G8）。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 设备接入
# ---------------------------------------------------------------------------


class DeviceConnCreate(BaseModel):
    """创建设备接入。"""

    conn_id: str = Field(..., max_length=20, description="接入编号")
    eid: str = Field(..., max_length=50, description="设备序列号")
    protocol: str | None = Field("MQTT", max_length=10, description="协议")
    topic: str | None = Field(None, max_length=200, description="MQTT主题")
    endpoint: str | None = Field(None, max_length=200, description="接入端点")
    heartbeat_interval: int | None = Field(60, description="心跳间隔秒")


class DeviceConnUpdate(BaseModel):
    """更新设备接入。"""

    protocol: str | None = Field(None, max_length=10, description="协议")
    topic: str | None = Field(None, max_length=200, description="MQTT主题")
    endpoint: str | None = Field(None, max_length=200, description="接入端点")
    heartbeat_interval: int | None = Field(None, description="心跳间隔秒")
    online_status: str | None = Field(None, max_length=10, description="在线状态")
    useflg: str | None = Field(None, max_length=1, description="有效标志")


# ---------------------------------------------------------------------------
# 设备数据
# ---------------------------------------------------------------------------


class DeviceDataCreate(BaseModel):
    """上报设备数据。"""

    eid: str = Field(..., max_length=50, description="设备序列号")
    data_type: str = Field(..., max_length=20, description="数据类型")
    data_value: str | None = Field(None, max_length=100, description="数据值")
    data_unit: str | None = Field(None, max_length=20, description="数据单位")
    report_time: datetime = Field(..., description="上报时间")
    quality: str | None = Field("GOOD", max_length=10, description="数据质量")


# ---------------------------------------------------------------------------
# 报警规则
# ---------------------------------------------------------------------------


class AlertRuleCreate(BaseModel):
    """创建报警规则。"""

    rule_id: str = Field(..., max_length=20, description="规则编号")
    rule_name: str = Field(..., max_length=100, description="规则名称")
    data_type: str = Field(..., max_length=20, description="监控数据类型")
    condition_type: str = Field(..., max_length=10, description="条件类型")
    threshold_min: Decimal | None = Field(None, description="下限阈值")
    threshold_max: Decimal | None = Field(None, description="上限阈值")
    severity: str | None = Field("WARNING", max_length=10, description="严重度")
    notify_method: str | None = Field(None, max_length=20, description="通知方式")


class AlertRuleUpdate(BaseModel):
    """更新报警规则。"""

    rule_name: str | None = Field(None, max_length=100, description="规则名称")
    threshold_min: Decimal | None = Field(None, description="下限阈值")
    threshold_max: Decimal | None = Field(None, description="上限阈值")
    severity: str | None = Field(None, max_length=10, description="严重度")
    notify_method: str | None = Field(None, max_length=20, description="通知方式")
    useflg: str | None = Field(None, max_length=1, description="有效标志")


# ---------------------------------------------------------------------------
# 报警确认
# ---------------------------------------------------------------------------


class AlertAcknowledge(BaseModel):
    """报警确认。"""

    status: str = Field(..., max_length=10, description="状态")
    ack_time: datetime | None = Field(None, description="确认时间")
    ack_user: str | None = Field(None, max_length=20, description="确认人")
    resolve_time: datetime | None = Field(None, description="解决时间")
    remark: str | None = Field(None, max_length=200, description="备注")
