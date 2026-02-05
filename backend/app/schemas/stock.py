"""
股票相关的Pydantic模型
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ============ 基础模型 ============

class StockBase(BaseModel):
    """股票基础信息"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")


class StockInWatchlist(StockBase):
    """自选股信息"""
    added_at: Optional[str] = Field(None, description="添加时间")
    sort_order: Optional[int] = Field(0, description="排序")
    notes: Optional[str] = Field(None, description="备注")


class StockWithQuote(StockBase):
    """带行情的股票信息"""
    price: Optional[float] = Field(None, description="当前价格")
    prev_close: Optional[float] = Field(None, description="昨收")
    change: Optional[float] = Field(None, description="涨跌额")
    pct_change: Optional[float] = Field(None, description="涨跌幅")
    volume: Optional[float] = Field(None, description="成交量")
    amount: Optional[float] = Field(None, description="成交额")


# ============ 请求模型 ============

class AddToWatchlistRequest(BaseModel):
    """添加自选股请求"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    notes: Optional[str] = Field("", description="备注")


class UpdateBuyInfoRequest(BaseModel):
    """更新买入信息请求"""
    buy_price: Optional[float] = Field(None, description="买入价格")
    buy_date: Optional[str] = Field(None, description="买入日期")
    buy_quantity: Optional[int] = Field(None, description="买入数量")


class SearchStockRequest(BaseModel):
    """搜索股票请求"""
    keyword: str = Field(..., description="搜索关键词")
    include_etf: Optional[bool] = Field(False, description="是否包含ETF")


# ============ 响应模型 ============

class WatchlistResponse(BaseModel):
    """自选股列表响应"""
    items: List[StockInWatchlist]
    total: int


class SearchResult(BaseModel):
    """搜索结果"""
    code: str
    name: str
    type: str = Field("stock", description="类型: stock/etf")


class SearchResponse(BaseModel):
    """搜索响应"""
    results: List[SearchResult]


class BuyInfoResponse(BaseModel):
    """买入信息响应"""
    buy_price: Optional[float] = None
    buy_date: Optional[str] = None
    buy_quantity: Optional[int] = None


# ============ 支撑/压力位模型 ============

class SupportResistanceLine(BaseModel):
    """支撑/压力线"""
    price: float = Field(..., description="价位")
    name: str = Field(..., description="名称")
    type: str = Field(..., description="类型: strong/medium/weak")
    ref_date: str = Field(..., description="参考日期")
    days_ago: int = Field(..., description="距今天数")
    ref_open: float = Field(..., description="参考开盘价")
    ref_close: float = Field(..., description="参考收盘价")
    calculation: str = Field(..., description="计算方式")
    vs_current: str = Field(..., description="与现价对比")


# ============ 均线状态模型 ============

class MAStatus(BaseModel):
    """单条均线状态"""
    value: float = Field(..., description="均线值")
    above: bool = Field(..., description="是否在均线上方")
    diff_pct: float = Field(..., description="与均线差值百分比")


class AllMAStatus(BaseModel):
    """所有均线状态"""
    MA7: Optional[MAStatus] = None
    MA18: Optional[MAStatus] = None
    MA30: Optional[MAStatus] = None
    MA89: Optional[MAStatus] = None


# ============ 形态模型 ============

class PatternInfo(BaseModel):
    """形态信息"""
    name: str = Field(..., description="形态名称")
    type: str = Field(..., description="类型: 看涨/看跌/待定")
    strength: str = Field(..., description="强度: 强/中/弱")
    desc: str = Field(..., description="描述")
    position_advice: Optional[str] = Field(None, description="仓位建议")


# ============ 完整分析结果模型 ============

class StrategyAnalysisResponse(BaseModel):
    """策略分析结果"""
    # 基本信息
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    current_price: float = Field(..., description="当前价格")

    # 量价分析
    volume_status: str = Field(..., description="量能状态: 放量/缩量/平量")
    volume_ratio: float = Field(..., description="量比")
    price_new_high: bool = Field(False, description="是否创新高")
    price_new_low: bool = Field(False, description="是否创新低")
    volume_price_conclusion: str = Field(..., description="量价结论")

    # 压力支撑线
    support_lines: List[SupportResistanceLine] = Field(default_factory=list, description="支撑线列表")
    resistance_lines: List[SupportResistanceLine] = Field(default_factory=list, description="压力线列表")
    near_support: bool = Field(False, description="是否接近支撑")
    near_resistance: bool = Field(False, description="是否接近压力")
    support_break_status: str = Field("", description="支撑线击穿状态")
    resistance_break_status: str = Field("", description="压力线突破状态")

    # 上影线分析
    upper_shadow_ratio: float = Field(0, description="上影线/实体比例")
    upper_shadow_warning: bool = Field(False, description="上影线预警")
    upper_shadow_detail: str = Field("", description="上影线计算详情")

    # 均线分析
    ma_status: Dict = Field(default_factory=dict, description="各均线状态")
    ma_support: str = Field("", description="均线支撑情况")

    # MACD分析
    macd_status: str = Field("", description="MACD状态")
    macd_cross: str = Field("无", description="金叉/死叉/无")

    # 反转形态
    patterns: List[PatternInfo] = Field(default_factory=list, description="检测到的形态")
    pattern_analysis: List[str] = Field(default_factory=list, description="形态分析说明")

    # 趋势分析
    trend_5d: str = Field("", description="5日趋势")
    trend_10d: str = Field("", description="10日趋势")
    trend_20d: str = Field("", description="20日趋势")

    # 综合建议
    action: str = Field(..., description="操作建议: 买入/卖出/加仓/减仓/持有观望")
    action_reason: str = Field("", description="简短原因")
    action_detail: str = Field("", description="详细分析")
    bullish_factors: List[str] = Field(default_factory=list, description="看多因素")
    bearish_factors: List[str] = Field(default_factory=list, description="看空因素")
    risk_level: str = Field("低", description="风险等级: 高/中/低")
    position_advice: str = Field("", description="仓位建议")

    class Config:
        from_attributes = True


# ============ K线数据模型 ============

class KlineDataPoint(BaseModel):
    """K线数据点"""
    date: str = Field(..., description="日期")
    open: float = Field(..., description="开盘价")
    close: float = Field(..., description="收盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    volume: float = Field(..., description="成交量")


class KlineResponse(BaseModel):
    """K线数据响应"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    klines: List[KlineDataPoint] = Field(default_factory=list, description="K线数据")
    support_lines: List[SupportResistanceLine] = Field(default_factory=list, description="支撑线")
    resistance_lines: List[SupportResistanceLine] = Field(default_factory=list, description="压力线")


# ============ 简化分析结果（用于列表展示）============

class StockSignalSummary(BaseModel):
    """股票信号摘要（用于列表展示）"""
    code: str
    name: str
    current_price: float
    action: str
    action_reason: str
    risk_level: str
    volume_status: str
    volume_ratio: float
    macd_cross: str
    patterns: List[str] = Field(default_factory=list, description="形态名称列表")


class WatchlistWithSignals(BaseModel):
    """带信号的自选股列表"""
    items: List[StockSignalSummary]
    total: int
