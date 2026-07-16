"""ntfy.sh 移动推送网关。

通过 HTTP POST 到 https://ntfy.sh/<topic> 发送推送消息，
手机端安装 ntfy App 订阅对应主题即可收到推送。

配置项：
    NTFY_TOPIC: ntfy 主题名（如 myitsm-dispatch）
"""

from __future__ import annotations

import os
import urllib.request
import urllib.error
import email.header
import logging

from app.services.gateways.base import BaseGateway

logger = logging.getLogger(__name__)


def _encode_header(value: str) -> str:
    """RFC 2047 编码 header 值，支持非 ASCII 字符。"""
    if not value:
        return ""
    try:
        value.encode("latin-1")
        return value
    except UnicodeEncodeError:
        return email.header.Header(value, "utf-8").encode()


class NtfyGateway(BaseGateway):
    """ntfy.sh 移动推送网关。"""

    def send(self, recipient: str, subject: str, body: str) -> tuple[bool, str]:
        """发送 ntfy 推送。

        Args:
            recipient: 未使用（ntfy 按主题广播，主题从环境变量读取）
            subject: 推送标题（作为 Title header）
            body: 推送正文
        """
        topic = os.getenv("NTFY_TOPIC", "").strip()
        if not topic:
            return False, "NTFY_TOPIC 未配置"
        url = f"https://ntfy.sh/{topic}"
        data = body.encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Title": _encode_header(subject or "ITSM 通知"),
                "Content-Type": "text/plain; charset=utf-8",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if 200 <= resp.status < 300:
                    return True, ""
                return False, f"ntfy 返回 HTTP {resp.status}"
        except urllib.error.HTTPError as e:
            return False, f"ntfy HTTP {e.code}: {e.reason}"
        except Exception as e:
            return False, f"ntfy 请求异常: {e}"
