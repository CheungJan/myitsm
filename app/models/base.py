"""模型基类。"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
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


class BaseModel(db.Model, TimestampMixin):  # type: ignore[misc, name-defined]
    """抽象基类，提供 to_dict 方法。"""

    __abstract__ = True

    _hidden_fields: set[str] = set()

    def to_dict(self) -> dict[str, Any]:
        """将模型转为字典，自动排除 _hidden_fields 中声明的敏感字段。"""
        result: dict[str, Any] = {}
        for column in self.__table__.columns:
            if column.name in self._hidden_fields:
                continue
            value = getattr(self, column.name)
            if isinstance(value, (datetime, date)):
                value = value.isoformat()
            elif isinstance(value, Decimal):
                value = float(value)
            elif isinstance(value, bytes):
                value = None
            result[column.name] = value
        return result
