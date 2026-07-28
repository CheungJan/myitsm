"""邮件网关（SMTP，默认 QQ 邮箱）。

通过 SMTP 发送邮件，免费，每日 500 封（QQ 邮箱限制）。

配置项：
    SMTP_HOST: SMTP 服务器地址（默认 smtp.qq.com）
    SMTP_PORT: SMTP 端口（默认 465，SSL；587 为 STARTTLS）
    SMTP_USER: 发件人邮箱（如 cheungjan@qq.com）
    SMTP_PASSWORD: SMTP 授权码（非邮箱密码，QQ 邮箱设置→账户→开启 POP3/SMTP 获取）
    EMAIL_FROM: 发件人地址（默认同 SMTP_USER）
"""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.services.gateways.base import BaseGateway

logger = logging.getLogger(__name__)


class EmailGateway(BaseGateway):
    """SMTP 邮件网关。"""

    def send(self, recipient: str, subject: str, body: str) -> tuple[bool, str]:
        """发送邮件。"""
        host = os.getenv("SMTP_HOST", "smtp.qq.com").strip()
        port = int(os.getenv("SMTP_PORT", "465"))
        user = os.getenv("SMTP_USER", "").strip()
        password = os.getenv("SMTP_PASSWORD", "").strip()
        from_addr = os.getenv("EMAIL_FROM", user).strip()

        if not user or not password:
            return False, "SMTP_USER 或 SMTP_PASSWORD 未配置"
        if not recipient or "@" not in recipient:
            return False, f"收件人邮箱无效: {recipient}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject or "ITSM 通知"
        msg["From"] = from_addr
        msg["To"] = recipient
        msg.attach(MIMEText(body, "html", "utf-8"))

        try:
            # 465 端口用 SMTP_SSL（直接 SSL），587/25 用 SMTP + STARTTLS
            if port == 465:
                with smtplib.SMTP_SSL(host, port, timeout=15) as server:
                    server.login(user, password)
                    server.sendmail(from_addr, [recipient], msg.as_string())
            else:
                with smtplib.SMTP(host, port, timeout=15) as server:
                    server.starttls()
                    server.login(user, password)
                    server.sendmail(from_addr, [recipient], msg.as_string())
            return True, ""
        except smtplib.SMTPAuthenticationError as e:
            return False, f"SMTP 认证失败: {e.smtp_error.decode('utf-8', errors='replace') if e.smtp_error else '授权码无效或SMTP服务未开启'}"
        except smtplib.SMTPServerDisconnected as e:
            # QQ 在 AUTH 失败后会关闭连接，真实错误可能是 535 认证失败
            return False, f"SMTP 连接断开（可能是授权码无效或SMTP服务未开启）: {e}"
        except Exception as e:
            logger.error("邮件发送失败: %s", e)
            return False, str(e)[:200]
