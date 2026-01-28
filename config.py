"""
配置管理模块
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent

# 数据库路径
DATABASE_PATH = BASE_DIR / "data" / "3bros.db"

# Server酱配置 (可通过环境变量或设置页面配置)
SERVERCHAN_KEY = os.getenv("SERVERCHAN_KEY", "")

# 默认推送时间
DEFAULT_PUSH_TIME = "15:30"

# 数据获取配置
DATA_CONFIG = {
    "default_period": 60,  # 默认获取60天数据
    "volume_ma_period": 5,  # 成交量均线周期
    "volume_ratio_threshold": 1.5,  # 放量阈值
}

# 信号检测配置
SIGNAL_CONFIG = {
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "hammer_shadow_ratio": 2.0,  # 锤子线下影线/实体比例
    "doji_body_ratio": 0.1,  # 十字星实体/振幅比例
    "engulfing_volume_ratio": 1.2,  # 吞没形态放量要求
}

# 大盘指数代码
INDEX_CODES = {
    "上证指数": "000001",
    "深证成指": "399001",
    "创业板指": "399006",
    "科创50": "000688",
}
