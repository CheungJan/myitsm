"""认证相关请求/响应 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求。"""

    user_id: str = Field(..., min_length=1, description="用户编码")
    password: str = Field(..., min_length=1, description="密码")
