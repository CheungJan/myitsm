"""通知网关抽象基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseGateway(ABC):
    """通知网关抽象基类。

    所有渠道网关（ntfy/钉钉/邮件/短信等）需继承此类并实现 send 方法。
    """

    @abstractmethod
    def send(self, recipient: str, subject: str, body: str) -> tuple[bool, str]:
        """发送通知。

        Args:
            recipient: 接收方（手机号/邮箱/主题/Webhook URL 等）
            subject: 通知标题
            body: 通知正文

        Returns:
            (是否成功, 错误信息) — 成功时错误信息为空字符串
        """
        raise NotImplementedError
