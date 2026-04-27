"""应用配置。"""

from __future__ import annotations

import os


class Config:
    """基础配置。"""

    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL",
        "postgresql://itsm:itsm@localhost:5432/itsm",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict[str, object] = {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    }

    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_SECONDS: int = 8 * 3600  # 8小时


class DevelopmentConfig(Config):
    """开发环境配置。"""

    DEBUG: bool = True


class ProductionConfig(Config):
    """生产环境配置。"""

    DEBUG: bool = False


class TestingConfig(Config):
    """测试环境配置（默认使用 SQLite 内存库，无需外部数据库）。"""

    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "TEST_DATABASE_URL",
        "sqlite:///:memory:",
    )
    SQLALCHEMY_ENGINE_OPTIONS: dict[str, object] = {}


config_map: dict[str, type[Config]] = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
