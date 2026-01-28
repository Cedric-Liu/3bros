"""
信号检测引擎 - 整合形态和技术指标
"""
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from .patterns import PatternRecognizer, PatternResult, SignalType
from utils.indicators import (
    calculate_macd,
    calculate_volume_ratio,
    check_macd_cross,
    calculate_ma
)
from config import SIGNAL_CONFIG


@dataclass
class Signal:
    """交易信号"""
    code: str  # 股票代码
    name: str  # 股票名称
    signal_type: SignalType  # 信号类型
    pattern_name: str  # 形态名称
    strength: float  # 信号强度 0-1
    price: float  # 当前价格
    description: str  # 描述
    confirmations: List[str] = field(default_factory=list)  # 确认因素
    date: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "signal_type": self.signal_type.value,
            "pattern_name": self.pattern_name,
            "strength": self.strength,
            "price": self.price,
            "description": self.description,
            "confirmations": self.confirmations,
            "date": self.date.strftime("%Y-%m-%d %H:%M")
        }


class SignalDetector:
    """信号检测器"""

    def __init__(self):
        self.pattern_recognizer = PatternRecognizer(
            hammer_shadow_ratio=SIGNAL_CONFIG["hammer_shadow_ratio"],
            doji_body_ratio=SIGNAL_CONFIG["doji_body_ratio"],
            engulfing_volume_ratio=SIGNAL_CONFIG["engulfing_volume_ratio"]
        )

    def detect_signals(
        self,
        df: pd.DataFrame,
        code: str,
        name: str
    ) -> List[Signal]:
        """
        检测股票的所有信号

        Args:
            df: 股票数据 DataFrame
            code: 股票代码
            name: 股票名称

        Returns:
            检测到的信号列表
        """
        if df is None or len(df) < 10:
            return []

        signals = []

        # 计算技术指标
        dif, dea, macd_hist = calculate_macd(
            df["close"],
            SIGNAL_CONFIG["macd_fast"],
            SIGNAL_CONFIG["macd_slow"],
            SIGNAL_CONFIG["macd_signal"]
        )

        volume_ratio = calculate_volume_ratio(df["volume"]).iloc[-1] if len(df) > 5 else 1.0

        # 检查MACD金叉/死叉
        is_golden_cross, is_death_cross = check_macd_cross(dif, dea)

        # 判断趋势
        trend = self.pattern_recognizer.detect_trend(df)

        # 当前价格
        current_price = df["close"].iloc[-1]

        # 检测各种形态
        patterns_to_check = [
            ("bullish_engulfing", self.pattern_recognizer.check_bullish_engulfing(df, volume_ratio)),
            ("bearish_engulfing", self.pattern_recognizer.check_bearish_engulfing(df, volume_ratio)),
            ("dark_cloud", self.pattern_recognizer.check_dark_cloud_cover(df)),
            ("piercing", self.pattern_recognizer.check_piercing_line(df)),
            ("hammer", self.pattern_recognizer.check_hammer(df, trend)),
            ("hanging_man", self.pattern_recognizer.check_hanging_man(df, trend)),
            ("doji", self.pattern_recognizer.check_doji(df)),
            ("morning_star", self.pattern_recognizer.check_morning_star(df)),
            ("evening_star", self.pattern_recognizer.check_evening_star(df)),
        ]

        for pattern_id, result in patterns_to_check:
            if result is not None:
                # 跳过中性信号（如普通十字星）
                if result.signal_type == SignalType.NEUTRAL:
                    continue

                confirmations = []
                adjusted_strength = result.strength

                # 添加MACD确认
                if result.signal_type == SignalType.BULLISH and is_golden_cross:
                    confirmations.append("MACD金叉")
                    adjusted_strength = min(adjusted_strength + 0.1, 1.0)
                elif result.signal_type == SignalType.BEARISH and is_death_cross:
                    confirmations.append("MACD死叉")
                    adjusted_strength = min(adjusted_strength + 0.1, 1.0)

                # 添加成交量确认
                if volume_ratio > 1.5:
                    confirmations.append(f"放量{volume_ratio:.1f}倍")
                    adjusted_strength = min(adjusted_strength + 0.05, 1.0)

                # 添加趋势确认
                if result.signal_type == SignalType.BULLISH and trend == "down":
                    confirmations.append("下跌趋势底部")
                elif result.signal_type == SignalType.BEARISH and trend == "up":
                    confirmations.append("上涨趋势顶部")

                # 检查均线支撑/压力
                ma20 = calculate_ma(df["close"], 20)
                if len(ma20) > 0 and not pd.isna(ma20.iloc[-1]):
                    ma20_value = ma20.iloc[-1]
                    price_to_ma = (current_price - ma20_value) / ma20_value

                    if result.signal_type == SignalType.BULLISH and -0.02 < price_to_ma < 0.02:
                        confirmations.append("接近MA20支撑")
                    elif result.signal_type == SignalType.BEARISH and -0.02 < price_to_ma < 0.02:
                        confirmations.append("接近MA20压力")

                signal = Signal(
                    code=code,
                    name=name,
                    signal_type=result.signal_type,
                    pattern_name=result.name,
                    strength=adjusted_strength,
                    price=current_price,
                    description=result.description,
                    confirmations=confirmations
                )
                signals.append(signal)

        return signals

    def detect_latest_signal(
        self,
        df: pd.DataFrame,
        code: str,
        name: str
    ) -> Optional[Signal]:
        """
        获取最强的信号

        Returns:
            最强的信号，如果没有则返回None
        """
        signals = self.detect_signals(df, code, name)

        if not signals:
            return None

        # 按信号强度排序，返回最强的
        signals.sort(key=lambda s: s.strength, reverse=True)
        return signals[0]

    def get_signal_summary(self, signal: Signal) -> str:
        """
        生成信号的文字摘要

        Args:
            signal: 信号对象

        Returns:
            格式化的信号摘要
        """
        emoji = "🟢" if signal.signal_type == SignalType.BULLISH else "🔴"
        action = signal.signal_type.value

        confirmations_str = ""
        if signal.confirmations:
            confirmations_str = f" ({', '.join(signal.confirmations)})"

        return (
            f"{emoji} {action} | {signal.code} {signal.name} | "
            f"{signal.pattern_name}{confirmations_str} | "
            f"强度: {signal.strength:.0%}"
        )
