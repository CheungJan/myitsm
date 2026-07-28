"""钉钉群机器人网关。

通过 Webhook URL 发送文本/Markdown 消息到钉钉群。

配置项：
    DINGTALK_WEBHOOK_URL: 钉钉群机器人 Webhook URL

注意：若机器人配置了"自定义关键词"安全设置，消息内容必须包含该关键词。
"""

from __future__ import annotations

import os
import urllib.request
import urllib.error
import json
import logging

from app.services.gateways.base import BaseGateway

logger = logging.getLogger(__name__)


class DingtalkGateway(BaseGateway):
    """钉钉群机器人网关。"""

    def send(self, recipient: str, subject: str, body: str) -> tuple[bool, str]:
        """发送钉钉群消息。

        Args:
            recipient: 未使用（消息发到 Webhook 对应的群）
            subject: 消息标题（Markdown 一级标题）
            body: 消息正文
        """
        webhook = os.getenv("DINGTALK_WEBHOOK_URL", "").strip()
        if not webhook:
            return False, "DINGTALK_WEBHOOK_URL 未配置"
        # 使用 Markdown 消息类型，支持标题+正文
        content = f"**{subject or 'ITSM 通知'}**\n\n{body or ''}"
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": subject or "ITSM 通知",
                "text": content,
            },
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            webhook,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                if resp_data.get("errcode") == 0:
                    return True, ""
                return False, f"钉钉返回错误: {resp_data.get('errmsg', '未知')}"
        except urllib.error.HTTPError as e:
            return False, f"钉钉 HTTP {e.code}: {e.reason}"
        except Exception as e:
            return False, f"钉钉请求异常: {e}"
