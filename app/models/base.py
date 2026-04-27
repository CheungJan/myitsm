"""模型基类。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.extensions import db


class TimestampMixin:
    """时间戳混入。"""

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class BaseModel(db.Model, TimestampMixin):  # type: ignore[name-defined]
    """抽象基类，提供 to_dict 方法。"""

    __abstract__ = True

    def to_dict(self) -> dict[str, Any]:
        """将模型转为字典。"""
        result: dict[str, Any] = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
