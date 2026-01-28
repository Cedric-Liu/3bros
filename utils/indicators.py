"""
技术指标计算模块
"""
import pandas as pd
import numpy as np
from typing import Tuple


def calculate_macd(
    close: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算MACD指标

    Args:
        close: 收盘价序列
        fast_period: 快线周期
        slow_period: 慢线周期
        signal_period: 信号线周期

    Returns:
        (dif, dea, macd_hist)
        - dif: 快线与慢线差值
        - dea: 信号线
        - macd_hist: MACD柱状图 (dif - dea) * 2
    """
    # 计算EMA
    ema_fast = close.ewm(span=fast_period, adjust=False).mean()
    ema_slow = close.ewm(span=slow_period, adjust=False).mean()

    # DIF线
    dif = ema_fast - ema_slow

    # DEA线 (信号线)
    dea = dif.ewm(span=signal_period, adjust=False).mean()

    # MACD柱状图
    macd_hist = (dif - dea) * 2

    return dif, dea, macd_hist


def calculate_ma(series: pd.Series, period: int) -> pd.Series:
    """
    计算移动平均线

    Args:
        series: 数据序列
        period: 周期

    Returns:
        移动平均序列
    """
    return series.rolling(window=period).mean()


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """
    计算指数移动平均线

    Args:
        series: 数据序列
        period: 周期

    Returns:
        指数移动平均序列
    """
    return series.ewm(span=period, adjust=False).mean()


def calculate_volume_ratio(volume: pd.Series, period: int = 5) -> pd.Series:
    """
    计算量比 (当前成交量 / 过去N日平均成交量)

    Args:
        volume: 成交量序列
        period: 均量周期

    Returns:
        量比序列
    """
    ma_volume = volume.rolling(window=period).mean().shift(1)
    ratio = volume / ma_volume
    return ratio


def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    计算RSI指标

    Args:
        close: 收盘价序列
        period: 周期

    Returns:
        RSI序列
    """
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_bollinger_bands(
    close: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算布林带

    Args:
        close: 收盘价序列
        period: 周期
        std_dev: 标准差倍数

    Returns:
        (upper, middle, lower) 上轨、中轨、下轨
    """
    middle = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()

    upper = middle + std_dev * std
    lower = middle - std_dev * std

    return upper, middle, lower


def check_macd_cross(dif: pd.Series, dea: pd.Series) -> Tuple[bool, bool]:
    """
    检查MACD金叉/死叉

    Args:
        dif: DIF线
        dea: DEA线

    Returns:
        (is_golden_cross, is_death_cross)
        - is_golden_cross: 今日金叉
        - is_death_cross: 今日死叉
    """
    if len(dif) < 2 or len(dea) < 2:
        return False, False

    # 今日DIF在DEA上方，昨日DIF在DEA下方 => 金叉
    is_golden_cross = (dif.iloc[-1] > dea.iloc[-1]) and (dif.iloc[-2] <= dea.iloc[-2])

    # 今日DIF在DEA下方，昨日DIF在DEA上方 => 死叉
    is_death_cross = (dif.iloc[-1] < dea.iloc[-1]) and (dif.iloc[-2] >= dea.iloc[-2])

    return is_golden_cross, is_death_cross


def check_price_position(
    close: pd.Series,
    ma_periods: list = [5, 10, 20, 60]
) -> dict:
    """
    检查价格相对于均线的位置

    Args:
        close: 收盘价序列
        ma_periods: 均线周期列表

    Returns:
        dict with ma values and position info
    """
    result = {}
    current_price = close.iloc[-1]

    for period in ma_periods:
        if len(close) >= period:
            ma = calculate_ma(close, period).iloc[-1]
            result[f"ma{period}"] = ma
            result[f"above_ma{period}"] = current_price > ma
        else:
            result[f"ma{period}"] = None
            result[f"above_ma{period}"] = None

    return result
