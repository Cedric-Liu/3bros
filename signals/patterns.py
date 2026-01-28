"""
K线形态识别模块 - 反转三兄弟核心形态
"""
import pandas as pd
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class SignalType(Enum):
    """信号类型"""
    BULLISH = "买入"
    BEARISH = "卖出"
    NEUTRAL = "观望"


@dataclass
class PatternResult:
    """形态识别结果"""
    name: str  # 形态名称
    signal_type: SignalType  # 信号类型
    strength: float  # 信号强度 0-1
    description: str  # 描述


class PatternRecognizer:
    """K线形态识别器"""

    def __init__(
        self,
        hammer_shadow_ratio: float = 2.0,
        doji_body_ratio: float = 0.1,
        engulfing_volume_ratio: float = 1.2
    ):
        """
        Args:
            hammer_shadow_ratio: 锤子线下影线/实体比例阈值
            doji_body_ratio: 十字星实体/振幅比例阈值
            engulfing_volume_ratio: 吞没形态放量要求
        """
        self.hammer_shadow_ratio = hammer_shadow_ratio
        self.doji_body_ratio = doji_body_ratio
        self.engulfing_volume_ratio = engulfing_volume_ratio

    @staticmethod
    def _is_bullish(open_price: float, close_price: float) -> bool:
        """判断是否为阳线"""
        return close_price > open_price

    @staticmethod
    def _is_bearish(open_price: float, close_price: float) -> bool:
        """判断是否为阴线"""
        return close_price < open_price

    @staticmethod
    def _body_size(open_price: float, close_price: float) -> float:
        """计算实体大小"""
        return abs(close_price - open_price)

    @staticmethod
    def _upper_shadow(open_price: float, close_price: float, high: float) -> float:
        """计算上影线长度"""
        return high - max(open_price, close_price)

    @staticmethod
    def _lower_shadow(open_price: float, close_price: float, low: float) -> float:
        """计算下影线长度"""
        return min(open_price, close_price) - low

    def check_bullish_engulfing(
        self,
        df: pd.DataFrame,
        volume_ratio: Optional[float] = None
    ) -> Optional[PatternResult]:
        """
        检测阳吞阴 (看涨吞没形态)

        条件:
        1. 前一根是阴线
        2. 当前是阳线
        3. 当前阳线实体完全包含前一根阴线实体
        4. 成交量放大 (可选)
        """
        if len(df) < 2:
            return None

        prev = df.iloc[-2]
        curr = df.iloc[-1]

        # 前一根是阴线
        if not self._is_bearish(prev["open"], prev["close"]):
            return None

        # 当前是阳线
        if not self._is_bullish(curr["open"], curr["close"]):
            return None

        # 阳线开盘低于阴线收盘，阳线收盘高于阴线开盘
        if curr["open"] < prev["close"] and curr["close"] > prev["open"]:
            strength = 0.7

            # 放量增强信号
            if volume_ratio and volume_ratio > self.engulfing_volume_ratio:
                strength = 0.9

            return PatternResult(
                name="阳吞阴",
                signal_type=SignalType.BULLISH,
                strength=strength,
                description="阳线实体完全包含前一根阴线，看涨信号"
            )

        return None

    def check_bearish_engulfing(
        self,
        df: pd.DataFrame,
        volume_ratio: Optional[float] = None
    ) -> Optional[PatternResult]:
        """
        检测阴吞阳 (看跌吞没形态)

        条件:
        1. 前一根是阳线
        2. 当前是阴线
        3. 当前阴线实体完全包含前一根阳线实体
        """
        if len(df) < 2:
            return None

        prev = df.iloc[-2]
        curr = df.iloc[-1]

        # 前一根是阳线
        if not self._is_bullish(prev["open"], prev["close"]):
            return None

        # 当前是阴线
        if not self._is_bearish(curr["open"], curr["close"]):
            return None

        # 阴线开盘高于阳线收盘，阴线收盘低于阳线开盘
        if curr["open"] > prev["close"] and curr["close"] < prev["open"]:
            strength = 0.7

            if volume_ratio and volume_ratio > self.engulfing_volume_ratio:
                strength = 0.9

            return PatternResult(
                name="阴吞阳",
                signal_type=SignalType.BEARISH,
                strength=strength,
                description="阴线实体完全包含前一根阳线，看跌信号"
            )

        return None

    def check_dark_cloud_cover(self, df: pd.DataFrame) -> Optional[PatternResult]:
        """
        检测乌云盖顶

        条件:
        1. 前一根是大阳线
        2. 当前阴线高开（开盘价高于前阳线最高价）
        3. 收盘价深入前阳线实体50%以下
        """
        if len(df) < 2:
            return None

        prev = df.iloc[-2]
        curr = df.iloc[-1]

        # 前一根是阳线
        if not self._is_bullish(prev["open"], prev["close"]):
            return None

        # 当前是阴线
        if not self._is_bearish(curr["open"], curr["close"]):
            return None

        # 高开：开盘价高于前阳线收盘价
        if curr["open"] <= prev["close"]:
            return None

        # 收盘价插入前阳线实体50%以下
        prev_midpoint = (prev["open"] + prev["close"]) / 2
        if curr["close"] < prev_midpoint and curr["close"] > prev["open"]:
            penetration = (prev["close"] - curr["close"]) / (prev["close"] - prev["open"])
            strength = min(0.6 + penetration * 0.3, 0.9)

            return PatternResult(
                name="乌云盖顶",
                signal_type=SignalType.BEARISH,
                strength=strength,
                description="跳空高开后阴线深入前阳线实体，强烈看跌信号"
            )

        return None

    def check_piercing_line(self, df: pd.DataFrame) -> Optional[PatternResult]:
        """
        检测刺透形态 (穿透形态)

        条件:
        1. 前一根是大阴线
        2. 当前阳线低开（开盘价低于前阴线最低价）
        3. 收盘价穿透前阴线实体50%以上
        """
        if len(df) < 2:
            return None

        prev = df.iloc[-2]
        curr = df.iloc[-1]

        # 前一根是阴线
        if not self._is_bearish(prev["open"], prev["close"]):
            return None

        # 当前是阳线
        if not self._is_bullish(curr["open"], curr["close"]):
            return None

        # 低开：开盘价低于前阴线收盘价
        if curr["open"] >= prev["close"]:
            return None

        # 收盘价穿透前阴线实体50%以上
        prev_midpoint = (prev["open"] + prev["close"]) / 2
        if curr["close"] > prev_midpoint and curr["close"] < prev["open"]:
            penetration = (curr["close"] - prev["close"]) / (prev["open"] - prev["close"])
            strength = min(0.6 + penetration * 0.3, 0.9)

            return PatternResult(
                name="刺透形态",
                signal_type=SignalType.BULLISH,
                strength=strength,
                description="跳空低开后阳线穿透前阴线实体，看涨信号"
            )

        return None

    def check_hammer(self, df: pd.DataFrame, trend: str = "down") -> Optional[PatternResult]:
        """
        检测锤子线

        条件:
        1. 出现在下跌趋势底部
        2. 下影线长度 >= 实体长度 * 2
        3. 上影线很短或没有
        """
        if len(df) < 1:
            return None

        curr = df.iloc[-1]

        body = self._body_size(curr["open"], curr["close"])
        lower_shadow = self._lower_shadow(curr["open"], curr["close"], curr["low"])
        upper_shadow = self._upper_shadow(curr["open"], curr["close"], curr["high"])

        # 避免除以0
        if body < 0.0001:
            return None

        # 下影线 >= 实体 * 2
        if lower_shadow < body * self.hammer_shadow_ratio:
            return None

        # 上影线很短
        if upper_shadow > body * 0.5:
            return None

        # 在下跌趋势中更有意义
        if trend == "down":
            return PatternResult(
                name="锤子线",
                signal_type=SignalType.BULLISH,
                strength=0.7,
                description="底部出现锤子线，可能反转向上"
            )

        return None

    def check_hanging_man(self, df: pd.DataFrame, trend: str = "up") -> Optional[PatternResult]:
        """
        检测上吊线

        条件:
        1. 出现在上涨趋势顶部
        2. 下影线长度 >= 实体长度 * 2
        3. 上影线很短或没有
        """
        if len(df) < 1:
            return None

        curr = df.iloc[-1]

        body = self._body_size(curr["open"], curr["close"])
        lower_shadow = self._lower_shadow(curr["open"], curr["close"], curr["low"])
        upper_shadow = self._upper_shadow(curr["open"], curr["close"], curr["high"])

        if body < 0.0001:
            return None

        if lower_shadow < body * self.hammer_shadow_ratio:
            return None

        if upper_shadow > body * 0.5:
            return None

        if trend == "up":
            return PatternResult(
                name="上吊线",
                signal_type=SignalType.BEARISH,
                strength=0.7,
                description="顶部出现上吊线，可能反转向下"
            )

        return None

    def check_doji(self, df: pd.DataFrame) -> Optional[PatternResult]:
        """
        检测十字星

        条件:
        开盘价约等于收盘价（实体非常小）
        """
        if len(df) < 1:
            return None

        curr = df.iloc[-1]

        body = self._body_size(curr["open"], curr["close"])
        total_range = curr["high"] - curr["low"]

        if total_range < 0.0001:
            return None

        # 实体占振幅比例很小
        if body / total_range < self.doji_body_ratio:
            return PatternResult(
                name="十字星",
                signal_type=SignalType.NEUTRAL,
                strength=0.5,
                description="十字星出现，市场犹豫不决，需结合位置判断"
            )

        return None

    def check_morning_star(self, df: pd.DataFrame) -> Optional[PatternResult]:
        """
        检测启明星 (早晨之星)

        条件:
        1. 第一天大阴线
        2. 第二天小实体（跳空低开）
        3. 第三天大阳线，收盘价进入第一天阴线实体
        """
        if len(df) < 3:
            return None

        day1 = df.iloc[-3]
        day2 = df.iloc[-2]
        day3 = df.iloc[-1]

        # 第一天大阴线
        if not self._is_bearish(day1["open"], day1["close"]):
            return None

        body1 = self._body_size(day1["open"], day1["close"])

        # 第二天小实体
        body2 = self._body_size(day2["open"], day2["close"])
        if body2 > body1 * 0.5:
            return None

        # 第三天大阳线
        if not self._is_bullish(day3["open"], day3["close"]):
            return None

        body3 = self._body_size(day3["open"], day3["close"])
        if body3 < body1 * 0.5:
            return None

        # 第三天收盘价进入第一天实体
        if day3["close"] > (day1["open"] + day1["close"]) / 2:
            return PatternResult(
                name="启明星",
                signal_type=SignalType.BULLISH,
                strength=0.85,
                description="底部启明星形态，强烈看涨信号"
            )

        return None

    def check_evening_star(self, df: pd.DataFrame) -> Optional[PatternResult]:
        """
        检测黄昏星 (暮星)

        条件:
        1. 第一天大阳线
        2. 第二天小实体（跳空高开）
        3. 第三天大阴线，收盘价进入第一天阳线实体
        """
        if len(df) < 3:
            return None

        day1 = df.iloc[-3]
        day2 = df.iloc[-2]
        day3 = df.iloc[-1]

        # 第一天大阳线
        if not self._is_bullish(day1["open"], day1["close"]):
            return None

        body1 = self._body_size(day1["open"], day1["close"])

        # 第二天小实体
        body2 = self._body_size(day2["open"], day2["close"])
        if body2 > body1 * 0.5:
            return None

        # 第三天大阴线
        if not self._is_bearish(day3["open"], day3["close"]):
            return None

        body3 = self._body_size(day3["open"], day3["close"])
        if body3 < body1 * 0.5:
            return None

        # 第三天收盘价进入第一天实体
        if day3["close"] < (day1["open"] + day1["close"]) / 2:
            return PatternResult(
                name="黄昏星",
                signal_type=SignalType.BEARISH,
                strength=0.85,
                description="顶部黄昏星形态，强烈看跌信号"
            )

        return None

    def detect_trend(self, df: pd.DataFrame, period: int = 10) -> str:
        """
        简单趋势判断

        Returns:
            "up", "down", or "sideways"
        """
        if len(df) < period:
            return "sideways"

        closes = df["close"].tail(period)
        first_half = closes.head(period // 2).mean()
        second_half = closes.tail(period // 2).mean()

        change_pct = (second_half - first_half) / first_half

        if change_pct > 0.03:
            return "up"
        elif change_pct < -0.03:
            return "down"
        else:
            return "sideways"
