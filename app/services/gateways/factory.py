"""通知网关工厂：按 channel 分发到对应 Gateway 实例。

通过环境变量 `NOTIFICATION_ENABLED_CHANNELS` 控制启用的渠道（逗号分隔），
未配置时默认全部已实现渠道启用。

示例：
    NOTIFICATION_ENABLED_CHANNELS=internal,dingtalk,email
"""

from __future__ import annotations

import os

from app.services.gateways.base import BaseGateway
from app.services.gateways.ntfy_gateway import NtfyGateway
from app.services.gateways.dingtalk_gateway import DingtalkGateway
from app.services.gateways.email_gateway import EmailGateway


# 渠道元数据：label 用于前端展示，require_config 标识需要外部配置
_CHANNEL_META: dict[str, dict[str, str]] = {
    "internal": {"label": "站内通知", "require_config": "否"},
    "ntfy": {"label": "移动推送(ntfy)", "require_config": "NTFY_TOPIC"},
    "dingtalk": {"label": "钉钉群机器人", "require_config": "DINGTALK_WEBHOOK_URL"},
    "feishu": {"label": "飞书群机器人", "require_config": "FEISHU_WEBHOOK_URL"},
    "wecom": {"label": "企业微信群机器人", "require_config": "WECOM_WEBHOOK_URL"},
    "email": {"label": "邮件(SMTP)", "require_config": "SMTP_HOST/USER/PASSWORD"},
    "sms": {"label": "短信", "require_config": "需企业资质+签名报备"},
}


class GatewayFactory:
    """通知网关工厂。

    按 channel 返回对应网关实例；internal 渠道无需网关（已落库），
    返回 None 由调用方处理。
    """

    _registry: dict[str, type[BaseGateway]] = {
        "ntfy": NtfyGateway,
        "dingtalk": DingtalkGateway,
        "email": EmailGateway,
    }

    @classmethod
    def get(cls, channel: str | None) -> BaseGateway | None:
        """按渠道返回网关实例。

        Args:
            channel: 通知渠道（internal/sms/email/dingtalk/feishu/wecom/ntfy）

        Returns:
            网关实例；internal 返回 None（已落库）；未启用或未知渠道返回 None
        """
        if channel is None or channel == "internal":
            return None
        # 检查渠道是否启用
        if not cls.is_enabled(channel):
            return None
        gateway_cls = cls._registry.get(channel)
        if gateway_cls is None:
            return None
        return gateway_cls()

    @classmethod
    def supported_channels(cls) -> list[str]:
        """返回已实现的渠道列表（含 internal）。"""
        return ["internal"] + list(cls._registry.keys())

    @classmethod
    def enabled_channels(cls) -> list[str]:
        """返回启用的渠道列表（受 NOTIFICATION_ENABLED_CHANNELS 环境变量控制）。

        未配置环境变量时，默认全部已实现渠道启用。
        """
        env_value = os.getenv("NOTIFICATION_ENABLED_CHANNELS", "").strip()
        if not env_value:
            return cls.supported_channels()
        configured = [c.strip() for c in env_value.split(",") if c.strip()]
        # 只返回已实现 + 已配置的渠道
        implemented = set(cls.supported_channels())
        return [c for c in configured if c in implemented]

    @classmethod
    def is_enabled(cls, channel: str) -> bool:
        """判断渠道是否启用。"""
        return channel in cls.enabled_channels()

    @classmethod
    def channel_meta(cls, channel: str) -> dict[str, str] | None:
        """返回渠道元数据（label/require_config）。"""
        return _CHANNEL_META.get(channel)

    @classmethod
    def channels_info(cls) -> list[dict[str, str]]:
        """返回所有已实现渠道的详情（含启用状态、标签、所需配置），供前端选用。"""
        result = []
        for ch in cls.supported_channels():
            meta = _CHANNEL_META.get(ch, {})
            result.append(
                {
                    "channel": ch,
                    "label": meta.get("label", ch),
                    "require_config": meta.get("require_config", ""),
                    "enabled": cls.is_enabled(ch),
                    "implemented": ch in cls.supported_channels(),
                }
            )
        return result
