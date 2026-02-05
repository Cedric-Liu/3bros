"""
配置管理模块 - 使用Pydantic Settings
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # 项目基本信息
    app_name: str = "反转三兄弟 API"
    app_version: str = "1.0.0"
    debug: bool = False

    # 数据库配置
    database_path: str = ""

    # CORS配置
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Server酱配置
    serverchan_key: str = ""

    # 默认推送时间
    default_push_time: str = "15:30"

    # 数据获取配置
    default_period: int = 60  # 默认获取60天数据
    volume_ma_period: int = 5  # 成交量均线周期
    volume_ratio_threshold: float = 1.5  # 放量阈值

    # 信号检测配置
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    hammer_shadow_ratio: float = 2.0  # 锤子线下影线/实体比例
    doji_body_ratio: float = 0.1  # 十字星实体/振幅比例
    engulfing_volume_ratio: float = 1.2  # 吞没形态放量要求

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# 大盘指数代码
INDEX_CODES = {
    "上证指数": "000001",
    "深证成指": "399001",
    "创业板指": "399006",
    "科创50": "000688",
}


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


def get_database_path() -> Path:
    """获取数据库路径"""
    settings = get_settings()
    if settings.database_path:
        return Path(settings.database_path)

    # 默认路径：3bros/data/3bros.db
    # __file__ = backend/app/config.py -> .parent.parent.parent = 3bros/
    base_dir = Path(__file__).parent.parent.parent
    return base_dir / "data" / "3bros.db"
