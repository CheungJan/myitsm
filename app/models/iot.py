"""
物联网数据监控模型（Tier-3 G8）。

设备数据采集、实时监控、报警预警、历史数据分析。

对应新增数据库表：
  设备接入：TIO01_DEVICE_CONN
  设备数据：TIO02_DEVICE_DATA
  报警规则：TIO03_ALERT_RULE
  报警记录：TIO04_ALERT_LOG
"""

from __future__ import annotations

from app.extensions import db
from app.models.base import BaseModel

# ---------------------------------------------------------------------------
# 设备接入
# ---------------------------------------------------------------------------


class DeviceConn(BaseModel):
    """设备接入配置（TIO01_DEVICE_CONN）。"""

    __tablename__ = "tio01_device_conn"

    conn_id = db.Column(db.String(20), primary_key=True, comment="接入编号")
    eid = db.Column(db.String(50), nullable=False, unique=True, comment="设备序列号")
    protocol = db.Column(
        db.String(10),
        default="MQTT",
        comment="接入协议（MQTT/HTTP/TCP）",
    )
    topic = db.Column(db.String(200), comment="MQTT主题")
    endpoint = db.Column(db.String(200), comment="接入端点地址")
    heartbeat_interval = db.Column(db.Integer, default=60, comment="心跳间隔（秒）")
    last_heartbeat = db.Column(db.DateTime, comment="最后心跳时间")
    online_status = db.Column(
        db.String(10),
        default="OFFLINE",
        comment="在线状态（ONLINE/OFFLINE/UNKNOWN）",
    )
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")


# ---------------------------------------------------------------------------
# 设备数据
# ---------------------------------------------------------------------------


class DeviceData(BaseModel):
    """设备上报数据（TIO02_DEVICE_DATA）。"""

    __tablename__ = "tio02_device_data"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    eid = db.Column(db.String(50), nullable=False, comment="设备序列号")
    data_type = db.Column(
        db.String(20),
        nullable=False,
        comment="数据类型（TEMPERATURE/PRESSURE/STATUS/LOCATION/COUNTER等）",
    )
    data_value = db.Column(db.String(100), comment="数据值")
    data_unit = db.Column(db.String(20), comment="数据单位")
    report_time = db.Column(db.DateTime, nullable=False, comment="上报时间")
    quality = db.Column(db.String(10), default="GOOD", comment="数据质量（GOOD/BAD/UNCERTAIN）")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")


# ---------------------------------------------------------------------------
# 报警规则
# ---------------------------------------------------------------------------


class AlertRule(BaseModel):
    """报警规则（TIO03_ALERT_RULE）。"""

    __tablename__ = "tio03_alert_rule"

    rule_id = db.Column(db.String(20), primary_key=True, comment="规则编号")
    rule_name = db.Column(db.String(100), nullable=False, comment="规则名称")
    data_type = db.Column(db.String(20), nullable=False, comment="监控数据类型")
    condition_type = db.Column(
        db.String(10),
        nullable=False,
        comment="条件类型（GT/LT/EQ/RANGE/OFFLINE）",
    )
    threshold_min = db.Column(db.Numeric(10, 2), comment="下限阈值")
    threshold_max = db.Column(db.Numeric(10, 2), comment="上限阈值")
    severity = db.Column(
        db.String(10),
        default="WARNING",
        comment="严重度（INFO/WARNING/CRITICAL）",
    )
    notify_method = db.Column(db.String(20), comment="通知方式（SMS/EMAIL/APP/ALL）")
    useflg = db.Column(db.String(1), default="1", comment="有效标志")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")


# ---------------------------------------------------------------------------
# 报警记录
# ---------------------------------------------------------------------------


class AlertLog(BaseModel):
    """报警记录（TIO04_ALERT_LOG）。"""

    __tablename__ = "tio04_alert_log"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rule_id = db.Column(db.String(20), nullable=False, comment="规则编号")
    eid = db.Column(db.String(50), nullable=False, comment="设备序列号")
    alert_time = db.Column(db.DateTime, nullable=False, comment="报警时间")
    data_type = db.Column(db.String(20), comment="数据类型")
    data_value = db.Column(db.String(100), comment="触发值")
    severity = db.Column(db.String(10), comment="严重度")
    status = db.Column(
        db.String(10),
        default="ACTIVE",
        comment="状态（ACTIVE/ACKNOWLEDGED/RESOLVED）",
    )
    ack_time = db.Column(db.DateTime, comment="确认时间")
    ack_user = db.Column(db.String(20), comment="确认人")
    resolve_time = db.Column(db.DateTime, comment="解决时间")
    remark = db.Column(db.String(200), comment="备注")
    opercd = db.Column(db.String(6), comment="操作人")
    upddate = db.Column(db.DateTime, comment="更新日期")
