"""
反转三兄弟策略分析器
基于PPT中的策略要点进行分析
"""
import pandas as pd
from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum

from .indicators import calculate_macd, calculate_ma, check_macd_cross


class ActionType(Enum):
    """操作建议"""
    BUY = "买入"
    SELL = "卖出"
    ADD = "加仓"
    REDUCE = "减仓"
    HOLD = "持有观望"


@dataclass
class StrategyAnalysis:
    """策略分析结果"""
    # 基本信息
    code: str
    name: str
    current_price: float

    # 量价分析
    volume_status: str  # 放量/缩量/平量
    volume_ratio: float  # 量比
    price_new_high: bool  # 是否创新高
    price_new_low: bool  # 是否创新低
    volume_price_conclusion: str  # 量价结论

    # 压力支撑线
    support_lines: List[Dict]  # 支撑线列表
    resistance_lines: List[Dict]  # 压力线列表
    near_support: bool  # 是否接近支撑
    near_resistance: bool  # 是否接近压力
    support_break_status: str  # 支撑线击穿状态
    resistance_break_status: str  # 压力线突破状态

    # 上影线分析
    upper_shadow_ratio: float  # 上影线/实体比例
    upper_shadow_warning: bool  # 上影线预警
    upper_shadow_detail: str  # 上影线计算详情

    # 均线分析
    ma_status: Dict  # 各均线状态
    ma_support: str  # 均线支撑情况

    # MACD分析
    macd_status: str  # MACD状态
    macd_cross: str  # 金叉/死叉/无

    # 反转形态
    patterns: List[Dict]  # 检测到的形态
    pattern_analysis: List[str]  # 形态分析说明（包括为什么没形成）

    # 趋势分析（近期走势）
    trend_5d: str  # 5日趋势
    trend_10d: str  # 10日趋势
    trend_20d: str  # 20日趋势

    # 综合建议
    action: ActionType
    action_reason: str  # 简短原因
    action_detail: str  # 详细分析
    bullish_factors: List[str]  # 看多因素
    bearish_factors: List[str]  # 看空因素
    risk_level: str  # 高/中/低
    position_advice: str  # 仓位建议（如加仓10%、减仓30%等）

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "current_price": self.current_price,
            "volume_status": self.volume_status,
            "volume_ratio": self.volume_ratio,
            "price_new_high": self.price_new_high,
            "price_new_low": self.price_new_low,
            "volume_price_conclusion": self.volume_price_conclusion,
            "support_lines": self.support_lines,
            "resistance_lines": self.resistance_lines,
            "near_support": self.near_support,
            "near_resistance": self.near_resistance,
            "support_break_status": self.support_break_status,
            "resistance_break_status": self.resistance_break_status,
            "upper_shadow_ratio": self.upper_shadow_ratio,
            "upper_shadow_warning": self.upper_shadow_warning,
            "upper_shadow_detail": self.upper_shadow_detail,
            "ma_status": self.ma_status,
            "ma_support": self.ma_support,
            "macd_status": self.macd_status,
            "macd_cross": self.macd_cross,
            "patterns": self.patterns,
            "pattern_analysis": self.pattern_analysis,
            "trend_5d": self.trend_5d,
            "trend_10d": self.trend_10d,
            "trend_20d": self.trend_20d,
            "action": self.action.value,
            "action_reason": self.action_reason,
            "action_detail": self.action_detail,
            "bullish_factors": self.bullish_factors,
            "bearish_factors": self.bearish_factors,
            "risk_level": self.risk_level,
            "position_advice": self.position_advice
        }


class StrategyAnalyzer:
    """反转三兄弟策略分析器"""

    def __init__(self):
        # 均线周期 (按用户要求: 7, 18, 30, 89)
        self.ma_periods = [7, 18, 30, 89]

    def analyze(self, df: pd.DataFrame, code: str, name: str) -> Optional[StrategyAnalysis]:
        """
        对股票进行完整的策略分析
        """
        if df is None or len(df) < 30:
            return None

        current = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else current

        # 1. 量价分析
        volume_status, volume_ratio = self._analyze_volume(df)
        price_new_high = self._is_new_high(df, 20)
        price_new_low = self._is_new_low(df, 20)
        volume_price_conclusion = self._get_volume_price_conclusion(
            volume_status, price_new_high, price_new_low
        )

        # 2. 压力支撑线分析（增强版：判断击穿程度）
        support_lines, resistance_lines = self._calculate_support_resistance(df)
        near_support = self._is_near_level(current["close"], support_lines, "support")
        near_resistance = self._is_near_level(current["close"], resistance_lines, "resistance")
        support_break_status = self._check_support_break(current["close"], support_lines)
        resistance_break_status = self._check_resistance_break(current["close"], resistance_lines, volume_status)

        # 3. 上影线分析
        upper_shadow_ratio, upper_shadow_detail = self._calculate_upper_shadow_ratio(current)
        upper_shadow_warning = bool(upper_shadow_ratio > 0.5)

        # 4. 均线分析
        ma_status = self._analyze_ma(df)
        ma_support = self._get_ma_support_status(df, ma_status)

        # 5. MACD分析
        macd_status, macd_cross = self._analyze_macd(df)

        # 6. 趋势分析（考虑近期走势）- 先计算趋势，用于形态判断
        trend_5d = self._analyze_trend(df, 5)
        trend_10d = self._analyze_trend(df, 10)
        trend_20d = self._analyze_trend(df, 20)

        # 7. 反转形态检测（增强版：结合趋势和确认信号）
        patterns, pattern_analysis = self._detect_patterns_enhanced(df, volume_ratio, trend_5d, trend_10d)

        # 8. 综合判断（详细版）
        action, action_reason, action_detail, bullish_factors, bearish_factors, risk_level, position_advice = \
            self._generate_detailed_recommendation(
                volume_status, volume_ratio, price_new_high, price_new_low,
                near_support, near_resistance, upper_shadow_warning, upper_shadow_ratio,
                ma_status, ma_support, macd_status, macd_cross, patterns,
                trend_5d, trend_10d, trend_20d,
                support_break_status, resistance_break_status
            )

        return StrategyAnalysis(
            code=code,
            name=name,
            current_price=float(current["close"]),
            volume_status=volume_status,
            volume_ratio=float(volume_ratio),
            price_new_high=price_new_high,
            price_new_low=price_new_low,
            volume_price_conclusion=volume_price_conclusion,
            support_lines=support_lines,
            resistance_lines=resistance_lines,
            near_support=near_support,
            near_resistance=near_resistance,
            support_break_status=support_break_status,
            resistance_break_status=resistance_break_status,
            upper_shadow_ratio=upper_shadow_ratio,
            upper_shadow_warning=upper_shadow_warning,
            upper_shadow_detail=upper_shadow_detail,
            ma_status=ma_status,
            ma_support=ma_support,
            macd_status=macd_status,
            macd_cross=macd_cross,
            patterns=patterns,
            pattern_analysis=pattern_analysis,
            trend_5d=trend_5d,
            trend_10d=trend_10d,
            trend_20d=trend_20d,
            action=action,
            action_reason=action_reason,
            action_detail=action_detail,
            bullish_factors=bullish_factors,
            bearish_factors=bearish_factors,
            risk_level=risk_level,
            position_advice=position_advice
        )

    def _analyze_volume(self, df: pd.DataFrame) -> tuple:
        """量能分析"""
        if len(df) < 6:
            return "平量", 1.0

        current_vol = df["volume"].iloc[-1]
        ma5_vol = df["volume"].tail(6).head(5).mean()

        if ma5_vol == 0:
            return "平量", 1.0

        ratio = current_vol / ma5_vol

        if ratio > 1.5:
            return "放量", float(round(ratio, 2))
        elif ratio < 0.7:
            return "缩量", float(round(ratio, 2))
        else:
            return "平量", float(round(ratio, 2))

    def _is_new_high(self, df: pd.DataFrame, period: int) -> bool:
        """是否创近期新高"""
        if len(df) < period:
            return False
        recent_high = df["high"].tail(period).max()
        return bool(df["high"].iloc[-1] >= recent_high * 0.99)

    def _is_new_low(self, df: pd.DataFrame, period: int) -> bool:
        """是否创近期新低"""
        if len(df) < period:
            return False
        recent_low = df["low"].tail(period).min()
        return bool(df["low"].iloc[-1] <= recent_low * 1.01)

    def _get_volume_price_conclusion(self, volume_status: str,
                                      new_high: bool, new_low: bool) -> str:
        """量价结论"""
        if new_high and volume_status == "放量":
            return "放量新高，上攻动能强，看涨"
        elif new_high and volume_status == "缩量":
            return "缩量新高，追高需谨慎"
        elif new_low and volume_status == "放量":
            return "放量新低，恐慌抛售，风险高"
        elif new_low and volume_status == "缩量":
            return "缩量新低，抛压减弱，关注企稳"
        elif volume_status == "放量":
            return "放量震荡，多空分歧大"
        elif volume_status == "缩量":
            return "缩量整理，等待方向选择"
        else:
            return "量价平稳，维持观望"

    def _calculate_support_resistance(self, df: pd.DataFrame) -> tuple:
        """
        计算压力线和支撑线（混合法）

        混合使用：
        1. 近期高低点（20日、60日的高点/低点）
        2. 关键均线（MA30、MA89）

        返回：最多2条支撑线 + 2条压力线，按距离现价远近排序
        """
        supports = []
        resistances = []
        current_price = float(df["close"].iloc[-1])

        # 用于去重的辅助函数
        def is_duplicate(price, existing_prices, threshold=0.02):
            """检查价格是否与已有价格太接近（2%以内）"""
            for p in existing_prices:
                if abs(price - p) / p < threshold:
                    return True
            return False

        # ========== 1. 近期高低点 ==========
        # 20日高低点
        if len(df) >= 20:
            high_20 = float(df["high"].tail(20).max())
            low_20 = float(df["low"].tail(20).min())

            if high_20 > current_price:
                diff_pct = (high_20 - current_price) / current_price * 100
                resistances.append({
                    "price": round(high_20, 2),
                    "name": "20日高点",
                    "type": "strong",
                    "ref_date": "",
                    "days_ago": 0,
                    "ref_open": high_20,
                    "ref_close": high_20,
                    "calculation": "近20日最高价",
                    "vs_current": f"高于现价{diff_pct:.1f}%"
                })

            if low_20 < current_price:
                diff_pct = (current_price - low_20) / current_price * 100
                supports.append({
                    "price": round(low_20, 2),
                    "name": "20日低点",
                    "type": "strong",
                    "ref_date": "",
                    "days_ago": 0,
                    "ref_open": low_20,
                    "ref_close": low_20,
                    "calculation": "近20日最低价",
                    "vs_current": f"低于现价{diff_pct:.1f}%"
                })

        # 60日高低点（如果与20日不重复）
        if len(df) >= 60:
            high_60 = float(df["high"].tail(60).max())
            low_60 = float(df["low"].tail(60).min())

            existing_res_prices = [r["price"] for r in resistances]
            existing_sup_prices = [s["price"] for s in supports]

            if high_60 > current_price and not is_duplicate(high_60, existing_res_prices):
                diff_pct = (high_60 - current_price) / current_price * 100
                resistances.append({
                    "price": round(high_60, 2),
                    "name": "60日高点",
                    "type": "strong",
                    "ref_date": "",
                    "days_ago": 0,
                    "ref_open": high_60,
                    "ref_close": high_60,
                    "calculation": "近60日最高价",
                    "vs_current": f"高于现价{diff_pct:.1f}%"
                })

            if low_60 < current_price and not is_duplicate(low_60, existing_sup_prices):
                diff_pct = (current_price - low_60) / current_price * 100
                supports.append({
                    "price": round(low_60, 2),
                    "name": "60日低点",
                    "type": "strong",
                    "ref_date": "",
                    "days_ago": 0,
                    "ref_open": low_60,
                    "ref_close": low_60,
                    "calculation": "近60日最低价",
                    "vs_current": f"低于现价{diff_pct:.1f}%"
                })

        # ========== 2. 均线支撑压力 ==========
        ma_periods = [30, 89]
        for period in ma_periods:
            if len(df) >= period:
                ma_value = float(df["close"].tail(period).mean())
                existing_res_prices = [r["price"] for r in resistances]
                existing_sup_prices = [s["price"] for s in supports]

                if ma_value > current_price and not is_duplicate(ma_value, existing_res_prices):
                    diff_pct = (ma_value - current_price) / current_price * 100
                    resistances.append({
                        "price": round(ma_value, 2),
                        "name": f"MA{period}",
                        "type": "medium",
                        "ref_date": "",
                        "days_ago": 0,
                        "ref_open": ma_value,
                        "ref_close": ma_value,
                        "calculation": f"{period}日均线",
                        "vs_current": f"高于现价{diff_pct:.1f}%"
                    })
                elif ma_value < current_price and not is_duplicate(ma_value, existing_sup_prices):
                    diff_pct = (current_price - ma_value) / current_price * 100
                    supports.append({
                        "price": round(ma_value, 2),
                        "name": f"MA{period}",
                        "type": "medium",
                        "ref_date": "",
                        "days_ago": 0,
                        "ref_open": ma_value,
                        "ref_close": ma_value,
                        "calculation": f"{period}日均线",
                        "vs_current": f"低于现价{diff_pct:.1f}%"
                    })

        # ========== 3. 排序并限制数量 ==========
        # 压力线：按价格从低到高（离现价近的优先）
        resistances.sort(key=lambda x: x["price"])
        resistances = resistances[:2]

        # 支撑线：按价格从高到低（离现价近的优先）
        supports.sort(key=lambda x: -x["price"])
        supports = supports[:2]

        return supports, resistances

    def _is_near_level(self, price: float, levels: List[Dict], level_type: str) -> bool:
        """是否接近支撑/压力位"""
        for level in levels:
            diff_pct = abs(price - level["price"]) / price * 100
            if diff_pct < 2:  # 2%以内算接近
                return True
        return False

    def _check_support_break(self, price: float, support_lines: List[Dict]) -> str:
        """
        检查支撑线击穿状态
        - 击穿1/2处：建议减仓30-50%
        - 击穿1/3处：建议减仓10-20%
        """
        if not support_lines:
            return ""

        # 找到各个支撑位
        half_support = None
        third_support = None
        open_support = None

        for s in support_lines:
            if "1/2" in s["name"]:
                half_support = s["price"]
            elif "1/3" in s["name"]:
                third_support = s["price"]
            elif "开盘价" in s["name"]:
                open_support = s["price"]

        # 判断击穿程度（价格低于支撑位即为击穿）
        if half_support and price < half_support:
            return "击穿1/2支撑，建议减仓30-50%"
        elif third_support and price < third_support:
            return "击穿1/3支撑，建议减仓10-20%"

        return ""

    def _check_resistance_break(self, price: float, resistance_lines: List[Dict], volume_status: str) -> str:
        """
        检查压力线突破状态
        - 放量突破压力线：有效突破
        - 缩量突破：弱反弹，大概率回落
        """
        if not resistance_lines:
            return ""

        # 找到各个压力位
        half_res = None
        third_res = None
        open_res = None

        for r in resistance_lines:
            if "1/2" in r["name"]:
                half_res = r["price"]
            elif "1/3" in r["name"]:
                third_res = r["price"]
            elif "开盘价" in r["name"]:
                open_res = r["price"]

        # 判断突破程度（价格高于压力位即为突破）
        if open_res and price > open_res:
            if volume_status == "放量":
                return "放量突破全部压力，强势反转"
            else:
                return "缩量突破压力，需确认有效性"
        elif half_res and price > half_res:
            if volume_status == "放量":
                return "放量突破1/2压力，可加仓30%"
            else:
                return "缩量突破1/2，弱反弹概率大"
        elif third_res and price > third_res:
            if volume_status == "放量":
                return "放量突破1/3压力，可加仓10%"
            else:
                return "缩量突破1/3，谨慎观望"

        return ""

    def _calculate_upper_shadow_ratio(self, row: pd.Series) -> tuple:
        """
        计算上影线/实体比例，返回(比例, 详细说明)
        """
        body = abs(row["close"] - row["open"])
        upper_shadow = row["high"] - max(row["close"], row["open"])
        ref_date = row["date"].strftime("%m/%d") if hasattr(row["date"], "strftime") else str(row["date"])[:10]

        if body == 0:
            ratio = 0 if upper_shadow == 0 else 999
            detail = f"今日({ref_date})实体为0，无法计算比例"
        else:
            ratio = round(upper_shadow / body, 2)
            high_price = row["high"]
            body_top = max(row["close"], row["open"])
            detail = (
                f"今日({ref_date})最高价{high_price:.2f}，"
                f"实体顶部{body_top:.2f}，"
                f"上影线={high_price:.2f}-{body_top:.2f}={upper_shadow:.2f}，"
                f"实体={body:.2f}，"
                f"比例={upper_shadow:.2f}/{body:.2f}={ratio:.2f}"
            )
            if ratio > 0.5:
                detail += "。上影线超过实体50%，说明上方抛压重，短期转弱概率大"
            elif ratio > 0.3:
                detail += "。上影线较长，上方有一定压力"
            else:
                detail += "。上影线较短，上方压力不大"

        return float(round(ratio, 2)), detail

    def _analyze_ma(self, df: pd.DataFrame) -> Dict:
        """均线分析"""
        result = {}
        current_price = df["close"].iloc[-1]

        for period in self.ma_periods:
            if len(df) >= period:
                ma_value = float(calculate_ma(df["close"], period).iloc[-1])
                above = bool(current_price > ma_value)
                diff_pct = float((current_price - ma_value) / ma_value * 100)
                result[f"MA{period}"] = {
                    "value": round(ma_value, 2),
                    "above": above,
                    "diff_pct": round(diff_pct, 2)
                }

        return result

    def _get_ma_support_status(self, df: pd.DataFrame, ma_status: Dict) -> str:
        """判断均线支撑状态 (7/18/30/89日均线)"""
        current_price = df["close"].iloc[-1]

        # 检查是否站上各均线
        above_ma7 = ma_status.get("MA7", {}).get("above", False)
        above_ma18 = ma_status.get("MA18", {}).get("above", False)
        above_ma30 = ma_status.get("MA30", {}).get("above", False)
        above_ma89 = ma_status.get("MA89", {}).get("above", False)

        if above_ma7 and above_ma18 and above_ma30 and above_ma89:
            return "多头排列，强势"
        elif above_ma7 and above_ma18 and above_ma30:
            return "站上短中期均线，偏强"
        elif above_ma7 and above_ma18:
            return "短期均线支撑有效"
        elif not above_ma7 and not above_ma18:
            return "跌破短期均线，转弱"
        elif not above_ma7 and not above_ma18 and not above_ma30:
            return "跌破多条均线，弱势"
        else:
            return "均线缠绕，方向不明"

    def _analyze_macd(self, df: pd.DataFrame) -> tuple:
        """MACD分析"""
        dif, dea, macd = calculate_macd(df["close"])

        current_dif = dif.iloc[-1]
        current_dea = dea.iloc[-1]
        current_macd = macd.iloc[-1]

        # MACD状态
        if current_dif > 0 and current_dea > 0:
            status = "零轴上方，多头市场"
        elif current_dif < 0 and current_dea < 0:
            status = "零轴下方，空头市场"
        else:
            status = "零轴附近，转折期"

        # 金叉死叉
        is_golden, is_death = check_macd_cross(dif, dea)
        if is_golden:
            cross = "金叉"
        elif is_death:
            cross = "死叉"
        else:
            cross = "无"

        return status, cross

    def _detect_patterns(self, df: pd.DataFrame, volume_ratio: float) -> tuple:
        """检测反转形态（基础版，保留兼容性）"""
        return self._detect_patterns_enhanced(df, volume_ratio, "", "")

    def _detect_patterns_enhanced(self, df: pd.DataFrame, volume_ratio: float,
                                   trend_5d: str, trend_10d: str) -> tuple:
        """
        检测反转形态（增强版）
        根据用户笔记优化：
        1. 锤子线需在下跌趋势中，隔天大阳确认才有效
        2. 上吊线需在上涨趋势中，隔天阴线确认才有效
        3. 十字星顺趋势方向判断
        4. 刺透形态分级：1/3、1/2、反包

        返回: (patterns, pattern_analysis)
        """
        patterns = []
        pattern_analysis = []  # 分析说明

        if len(df) < 3:
            return patterns, ["数据不足，无法分析反转形态"]

        curr = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3] if len(df) > 2 else prev

        # 判断阴阳线
        curr_bullish = curr["close"] > curr["open"]
        prev_bullish = prev["close"] > prev["open"]
        prev2_bullish = prev2["close"] > prev2["open"]

        curr_body = abs(curr["close"] - curr["open"])
        prev_body = abs(prev["close"] - prev["open"])

        curr_type = "阳线" if curr_bullish else "阴线"
        prev_type = "阳线" if prev_bullish else "阴线"

        # 判断趋势方向
        is_downtrend = "下跌" in trend_5d or "弱势" in trend_5d or "偏弱" in trend_5d
        is_uptrend = "上涨" in trend_5d or "强势" in trend_5d or "偏强" in trend_5d
        trend_desc = "下跌趋势" if is_downtrend else ("上涨趋势" if is_uptrend else "震荡趋势")

        # 1. 阳吞阴 (看涨)
        if curr_bullish and not prev_bullish:
            if curr["open"] < prev["close"] and curr["close"] > prev["open"]:
                strength = "强" if volume_ratio > 1.5 else "中"
                patterns.append({
                    "name": "阳吞阴",
                    "type": "看涨",
                    "strength": strength,
                    "desc": "阳线实体完全包含前阴线，反转信号",
                    "position_advice": "可加仓50%"
                })

        # 2. 阴吞阳 (看跌)
        if not curr_bullish and prev_bullish:
            if curr["open"] > prev["close"] and curr["close"] < prev["open"]:
                strength = "强" if volume_ratio > 1.5 else "中"
                patterns.append({
                    "name": "阴吞阳",
                    "type": "看跌",
                    "strength": strength,
                    "desc": "阴线实体完全包含前阳线，反转信号",
                    "position_advice": "建议减仓30-50%"
                })

        # 3. 乌云盖顶 (看跌)
        if not curr_bullish and prev_bullish:
            if curr["open"] > prev["close"]:  # 跳空高开
                mid_point = (prev["open"] + prev["close"]) / 2
                if curr["close"] < mid_point and curr["close"] > prev["open"]:
                    patterns.append({
                        "name": "乌云盖顶",
                        "type": "看跌",
                        "strength": "强",
                        "desc": "高开后阴线深入前阳线实体50%以上",
                        "position_advice": "建议减仓25-33%"
                    })

        # 4. 刺透形态 (看涨) - 增强版：分级判断
        if curr_bullish and not prev_bullish:
            prev_drop = prev["open"] - prev["close"]  # 前大阴线跌幅
            if prev_drop > 0:
                third_point = prev["close"] + prev_drop / 3  # 1/3处
                half_point = prev["close"] + prev_drop / 2   # 1/2处

                if curr["close"] >= prev["open"]:
                    # 完全反包前阴线
                    strength = "强" if volume_ratio > 1.5 else "中"
                    body_desc = "大实体" if curr_body > prev_body else "实体"
                    vol_desc = "放量" if volume_ratio > 1.5 else ""
                    patterns.append({
                        "name": "刺透反包",
                        "type": "看涨",
                        "strength": "强",
                        "desc": f"{vol_desc}阳线完全反包前阴线，强反转信号",
                        "position_advice": "可加仓50%"
                    })
                elif curr["close"] >= half_point:
                    # 穿过1/2
                    strength = "强" if volume_ratio > 1.5 else "中"
                    patterns.append({
                        "name": "刺透形态",
                        "type": "看涨",
                        "strength": strength,
                        "desc": "低开后阳线穿透前阴线1/2以上",
                        "position_advice": "可加仓30%"
                    })
                elif curr["close"] >= third_point and curr["open"] < prev["close"]:
                    # 穿过1/3
                    patterns.append({
                        "name": "刺透1/3",
                        "type": "看涨",
                        "strength": "中",
                        "desc": "阳线穿透前阴线1/3，初步反弹信号",
                        "position_advice": "可加仓10%"
                    })

        # 5. 锤子线 (底部看涨) - 增强版：需要下跌趋势 + 隔天确认
        lower_shadow = min(curr["open"], curr["close"]) - curr["low"]
        upper_shadow = curr["high"] - max(curr["open"], curr["close"])

        # 检查前一天是否是锤子线形态（用于今天确认）
        prev_lower_shadow = min(prev["open"], prev["close"]) - prev["low"]
        prev_upper_shadow = prev["high"] - max(prev["open"], prev["close"])
        prev_is_hammer = prev_body > 0 and prev_lower_shadow >= prev_body * 2 and prev_upper_shadow < prev_body * 0.3

        if prev_is_hammer and is_downtrend:
            # 昨天出现锤子线，检查今天是否确认
            if curr_bullish and volume_ratio > 1.2:
                # 今天放量阳线确认
                patterns.append({
                    "name": "锤子线确认",
                    "type": "看涨",
                    "strength": "强",
                    "desc": "下跌中锤子线+今日放量阳线确认，底部信号",
                    "position_advice": "可考虑进场"
                })
            elif curr_bullish:
                patterns.append({
                    "name": "锤子线确认",
                    "type": "看涨",
                    "strength": "中",
                    "desc": "下跌中锤子线+今日阳线确认",
                    "position_advice": "可小仓位试探"
                })

        # 今天出现锤子线（待确认）
        if curr_body > 0 and lower_shadow >= curr_body * 2 and upper_shadow < curr_body * 0.3:
            if is_downtrend:
                patterns.append({
                    "name": "锤子线",
                    "type": "看涨",
                    "strength": "弱",
                    "desc": "下跌中出现锤子线，等待明日阳线确认",
                    "position_advice": "观望，等确认信号"
                })
            else:
                patterns.append({
                    "name": "锤子线",
                    "type": "待定",
                    "strength": "弱",
                    "desc": "非下跌趋势的锤子线，信号较弱",
                    "position_advice": "观望"
                })

        # 6. 上吊线 (顶部看跌) - 增强版：需要上涨趋势 + 隔天阴线确认
        prev_is_hanging = prev_body > 0 and prev_lower_shadow >= prev_body * 2 and prev_upper_shadow < prev_body * 0.3

        if prev_is_hanging and is_uptrend:
            # 昨天出现上吊线，检查今天是否确认
            if not curr_bullish and volume_ratio > 1.2:
                # 今天放量阴线确认
                patterns.append({
                    "name": "上吊线确认",
                    "type": "看跌",
                    "strength": "强",
                    "desc": "上涨中上吊线+今日放量阴线确认，顶部信号",
                    "position_advice": "建议减仓25-33%"
                })
            elif not curr_bullish:
                patterns.append({
                    "name": "上吊线确认",
                    "type": "看跌",
                    "strength": "中",
                    "desc": "上涨中上吊线+今日阴线确认",
                    "position_advice": "建议减仓25%"
                })

        # 今天在上涨趋势中出现类似上吊线形态（待确认）
        if is_uptrend and curr_body > 0 and lower_shadow >= curr_body * 2 and upper_shadow < curr_body * 0.3:
            patterns.append({
                "name": "上吊线",
                "type": "看跌",
                "strength": "弱",
                "desc": "上涨中出现上吊线，等待明日阴线确认",
                "position_advice": "观望，注意风险"
            })

        # 7. 十字星 - 增强版：顺趋势方向判断
        total_range = curr["high"] - curr["low"]
        if total_range > 0 and curr_body / total_range < 0.1:
            if is_uptrend:
                patterns.append({
                    "name": "十字星",
                    "type": "看涨",
                    "strength": "弱",
                    "desc": "上涨趋势中十字星，大概率继续向上",
                    "position_advice": "持有观望"
                })
            elif is_downtrend:
                patterns.append({
                    "name": "十字星",
                    "type": "看跌",
                    "strength": "弱",
                    "desc": "下跌趋势中十字星，大概率继续向下",
                    "position_advice": "谨慎持有"
                })
            else:
                patterns.append({
                    "name": "十字星",
                    "type": "待定",
                    "strength": "弱",
                    "desc": "震荡中十字星，等待方向选择",
                    "position_advice": "观望"
                })

        # === 生成形态分析说明（解释为什么没有形成反转形态）===
        pattern_names = [p["name"] for p in patterns]

        # 1. 吞没形态分析
        if "阳吞阴" not in pattern_names and "阴吞阳" not in pattern_names:
            if curr_bullish and prev_bullish:
                pattern_analysis.append(f"吞没形态：今日{curr_type}，昨日也是{prev_type}，需要阴阳交替才能形成吞没")
            elif not curr_bullish and not prev_bullish:
                pattern_analysis.append(f"吞没形态：今日{curr_type}，昨日也是{prev_type}，需要阴阳交替才能形成吞没")
            elif curr_bullish and not prev_bullish:
                if not (curr["open"] < prev["close"] and curr["close"] > prev["open"]):
                    pattern_analysis.append(f"阳吞阴未形成：今日阳线实体未完全包含昨日阴线（需开盘<{prev['close']:.2f}且收盘>{prev['open']:.2f}）")
            elif not curr_bullish and prev_bullish:
                if not (curr["open"] > prev["close"] and curr["close"] < prev["open"]):
                    pattern_analysis.append(f"阴吞阳未形成：今日阴线实体未完全包含昨日阳线（需开盘>{prev['close']:.2f}且收盘<{prev['open']:.2f}）")

        # 2. 刺透/乌云盖顶分析
        if "刺透" not in " ".join(pattern_names) and "乌云盖顶" not in pattern_names:
            if curr_bullish and not prev_bullish:
                prev_drop = prev["open"] - prev["close"]
                if prev_drop > 0:
                    third_point = prev["close"] + prev_drop / 3
                    if curr["close"] < third_point:
                        pattern_analysis.append(f"刺透形态未形成：今日收盘{curr['close']:.2f}未穿过前阴线1/3位置{third_point:.2f}")
            elif not curr_bullish and prev_bullish:
                if curr["open"] <= prev["close"]:
                    pattern_analysis.append(f"乌云盖顶未形成：今日开盘{curr['open']:.2f}未跳空高开（需>{prev['close']:.2f}）")

        # 3. 锤子线/上吊线分析
        lower_shadow_curr = min(curr["open"], curr["close"]) - curr["low"]
        upper_shadow_curr = curr["high"] - max(curr["open"], curr["close"])
        if "锤子线" not in " ".join(pattern_names) and "上吊线" not in " ".join(pattern_names):
            if curr_body > 0:
                shadow_ratio = lower_shadow_curr / curr_body if curr_body > 0 else 0
                if shadow_ratio < 2:
                    pattern_analysis.append(f"锤子线/上吊线未形成：下影线/实体比={shadow_ratio:.1f}（需>=2），下影线不够长")
                elif upper_shadow_curr >= curr_body * 0.3:
                    pattern_analysis.append(f"锤子线/上吊线未形成：上影线过长，不符合形态要求")

        # 如果没有任何形态
        if not patterns:
            pattern_analysis.insert(0, f"当前{trend_desc}，今日{curr_type}，昨日{prev_type}，暂无明显反转形态")

        return patterns, pattern_analysis

    def _analyze_trend(self, df: pd.DataFrame, days: int) -> str:
        """分析近期趋势"""
        if len(df) < days:
            return "数据不足"

        recent = df.tail(days)
        start_price = recent["close"].iloc[0]
        end_price = recent["close"].iloc[-1]
        change_pct = (end_price - start_price) / start_price * 100

        high = recent["high"].max()
        low = recent["low"].min()

        if change_pct > 5:
            return f"上涨{change_pct:.1f}%，强势"
        elif change_pct > 2:
            return f"上涨{change_pct:.1f}%，偏强"
        elif change_pct > -2:
            return f"震荡{change_pct:+.1f}%"
        elif change_pct > -5:
            return f"下跌{change_pct:.1f}%，偏弱"
        else:
            return f"下跌{change_pct:.1f}%，弱势"

    def _generate_detailed_recommendation(self, volume_status, volume_ratio,
                                           new_high, new_low, near_support, near_resistance,
                                           upper_shadow_warning, upper_shadow_ratio, ma_status, ma_support,
                                           macd_status, macd_cross, patterns,
                                           trend_5d, trend_10d, trend_20d,
                                           support_break_status="", resistance_break_status="") -> tuple:
        """生成详细综合建议"""
        bullish_factors = []
        bearish_factors = []
        position_advices = []  # 收集仓位建议

        # === 量价分析 ===
        if new_high and volume_status == "放量":
            bullish_factors.append(f"【强】放量创新高，量比{volume_ratio}，上攻动能充足")
        elif new_high and volume_status == "缩量":
            bearish_factors.append("【弱】缩量新高，追高风险大")
        elif new_low and volume_status == "放量":
            bearish_factors.append(f"【强】放量创新低，量比{volume_ratio}，恐慌抛售")
        elif new_low and volume_status == "缩量":
            bullish_factors.append("【中】缩量新低，抛压减弱，关注企稳")
        elif volume_status == "放量":
            bullish_factors.append(f"【中】放量震荡，量比{volume_ratio}，资金活跃")

        # === 支撑压力位分析（增强版）===
        if support_break_status:
            bearish_factors.append(f"【强】{support_break_status}")
            if "30-50%" in support_break_status:
                position_advices.append("减仓30-50%")
            elif "10-20%" in support_break_status:
                position_advices.append("减仓10-20%")

        if resistance_break_status:
            if "放量突破" in resistance_break_status:
                bullish_factors.append(f"【强】{resistance_break_status}")
                if "50%" in resistance_break_status:
                    position_advices.append("可加仓50%")
                elif "30%" in resistance_break_status:
                    position_advices.append("可加仓30%")
                elif "10%" in resistance_break_status:
                    position_advices.append("可加仓10%")
            elif "缩量" in resistance_break_status:
                bearish_factors.append(f"【中】{resistance_break_status}")

        if near_support and not support_break_status:
            bullish_factors.append("【中】接近支撑位，有支撑预期")
        if near_resistance and not resistance_break_status:
            bearish_factors.append("【中】接近压力位，可能承压")

        # === 上影线 ===
        if upper_shadow_warning:
            bearish_factors.append(f"【中】上影线/实体比{upper_shadow_ratio:.1f}，短期转弱概率大")

        # === 均线分析 ===
        ma7 = ma_status.get("MA7", {})
        ma18 = ma_status.get("MA18", {})
        ma30 = ma_status.get("MA30", {})
        ma89 = ma_status.get("MA89", {})

        above_count = sum([
            ma7.get("above", False),
            ma18.get("above", False),
            ma30.get("above", False),
            ma89.get("above", False)
        ])

        if above_count == 4:
            bullish_factors.append("【强】站上全部均线(7/18/30/89)，多头排列")
        elif above_count >= 3:
            bullish_factors.append(f"【中】站上{above_count}条均线，偏多")
        elif above_count <= 1:
            bearish_factors.append(f"【强】跌破多条均线，仅站上{above_count}条，空头排列")
        else:
            bearish_factors.append(f"【中】均线缠绕，站上{above_count}条")

        # 检查是否回踩均线
        if ma7.get("above") and abs(ma7.get("diff_pct", 0)) < 1:
            bullish_factors.append("【中】回踩MA7支撑")
        if ma18.get("above") and abs(ma18.get("diff_pct", 0)) < 1.5:
            bullish_factors.append("【中】回踩MA18支撑")

        # === MACD ===
        if macd_cross == "金叉":
            if "零轴上方" in macd_status:
                bullish_factors.append("【强】零轴上方MACD金叉，强势确认")
            else:
                bullish_factors.append("【中】MACD金叉，关注反弹")
        elif macd_cross == "死叉":
            if "零轴下方" in macd_status:
                bearish_factors.append("【强】零轴下方MACD死叉，弱势确认")
            else:
                bearish_factors.append("【中】MACD死叉，注意回调")

        # === 反转形态（增强版：收集仓位建议）===
        for p in patterns:
            strength_label = "【强】" if p["strength"] == "强" else ("【中】" if p["strength"] == "中" else "【弱】")
            if p["type"] == "看涨":
                bullish_factors.append(f"{strength_label}{p['name']}形态，{p['desc']}")
                if p.get("position_advice") and "加仓" in p.get("position_advice", ""):
                    position_advices.append(p["position_advice"])
            elif p["type"] == "看跌":
                bearish_factors.append(f"{strength_label}{p['name']}形态，{p['desc']}")
                if p.get("position_advice") and "减仓" in p.get("position_advice", ""):
                    position_advices.append(p["position_advice"])

        # === 趋势分析 ===
        if "强势" in trend_5d or "上涨" in trend_5d:
            bullish_factors.append(f"【中】近5日{trend_5d}")
        elif "弱势" in trend_5d or "下跌" in trend_5d:
            bearish_factors.append(f"【中】近5日{trend_5d}")

        if "强势" in trend_20d:
            bullish_factors.append(f"【中】近20日趋势向好")
        elif "弱势" in trend_20d:
            bearish_factors.append(f"【中】近20日趋势走弱")

        # === 综合评分 ===
        bullish_score = len([f for f in bullish_factors if "【强】" in f]) * 3 + \
                        len([f for f in bullish_factors if "【中】" in f]) * 1
        bearish_score = len([f for f in bearish_factors if "【强】" in f]) * 3 + \
                        len([f for f in bearish_factors if "【中】" in f]) * 1

        score = bullish_score - bearish_score

        # === 生成建议 ===
        if score >= 5:
            action = ActionType.BUY
            risk = "中"
            reason = "多重看涨信号共振"
        elif score >= 2 and (near_support or any("回踩" in f for f in bullish_factors)):
            action = ActionType.ADD
            risk = "低"
            reason = "支撑位置可加仓"
        elif score <= -5:
            action = ActionType.SELL
            risk = "高"
            reason = "多重看跌信号，建议离场"
        elif score <= -2:
            action = ActionType.REDUCE
            risk = "中"
            reason = "走弱迹象，可减仓"
        else:
            action = ActionType.HOLD
            risk = "低"
            reason = "多空平衡，观望为主"

        # === 生成具体仓位建议 ===
        if position_advices:
            # 去重并合并仓位建议
            position_advice = "；".join(list(dict.fromkeys(position_advices)))
        else:
            # 根据操作类型给出默认建议
            if action == ActionType.BUY:
                position_advice = "可建仓30-50%"
            elif action == ActionType.ADD:
                position_advice = "可加仓10-20%"
            elif action == ActionType.REDUCE:
                position_advice = "建议减仓20-30%"
            elif action == ActionType.SELL:
                position_advice = "建议清仓或减至10%以下"
            else:
                position_advice = "维持现有仓位"

        # 详细分析文本
        detail_parts = []
        detail_parts.append(f"综合评分: 多方{bullish_score}分 vs 空方{bearish_score}分")
        detail_parts.append(f"近期趋势: 5日{trend_5d}，10日{trend_10d}，20日{trend_20d}")
        detail_parts.append(f"均线状态: {ma_support}")
        detail_parts.append(f"MACD: {macd_status}，{macd_cross if macd_cross != '无' else '无信号'}")

        action_detail = "；".join(detail_parts)

        return action, reason, action_detail, bullish_factors, bearish_factors, risk, position_advice

    def has_buy_signal(self, df: pd.DataFrame, code: str, name: str) -> tuple:
        """
        简单判断是否有买入信号
        返回 (has_signal, signal_name, strength)
        """
        analysis = self.analyze(df, code, name)
        if analysis is None:
            return False, "", ""

        if analysis.action in (ActionType.BUY, ActionType.ADD):
            return True, analysis.action_reason, analysis.risk_level

        return False, "", ""
