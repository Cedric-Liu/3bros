"""
市场相关的Pydantic模型
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class IndexInfo(BaseModel):
    """指数信息"""
    code: str = Field(..., description="指数代码")
    name: str = Field(..., description="指数名称")
    price: float = Field(..., description="当前点位")
    change: float = Field(..., description="涨跌额")
    pct_change: float = Field(..., description="涨跌幅")
    volume: Optional[float] = Field(None, description="成交量")
    amount: Optional[float] = Field(None, description="成交额")


class IndexWithSignal(IndexInfo):
    """带信号的指数信息"""
    action: Optional[str] = Field(None, description="操作建议")
    action_reason: Optional[str] = Field(None, description="建议原因")
    macd_cross: Optional[str] = Field(None, description="MACD状态")


class MarketIndicesResponse(BaseModel):
    """大盘指数响应"""
    indices: List[IndexWithSignal]
    update_time: str = Field(..., description="更新时间")


# ============ 今日信号 ============

class TodaySignal(BaseModel):
    """今日信号"""
    code: str
    name: str
    signal_type: str = Field(..., description="信号类型: 买入/卖出")
    pattern_name: str = Field(..., description="形态名称")
    strength: float = Field(..., description="信号强度 0-1")
    price: float = Field(..., description="价格")
    description: Optional[str] = Field(None, description="描述")
    confirmations: List[str] = Field(default_factory=list, description="确认因素")
    detected_at: Optional[str] = Field(None, description="检测时间")


class TodaySignalsResponse(BaseModel):
    """今日信号响应"""
    buy_signals: List[TodaySignal] = Field(default_factory=list, description="买入信号")
    sell_signals: List[TodaySignal] = Field(default_factory=list, description="卖出信号")
    total: int = Field(0, description="信号总数")


# ============ 市场扫描 ============

class ScanRequest(BaseModel):
    """扫描请求"""
    limit: Optional[int] = Field(200, description="扫描股票数量")


class ScanTaskInfo(BaseModel):
    """扫描任务信息"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="状态: pending/running/completed/failed")
    progress: int = Field(0, description="进度 0-100")
    total: int = Field(0, description="总数")
    processed: int = Field(0, description="已处理数")
    started_at: Optional[str] = Field(None, description="开始时间")
    completed_at: Optional[str] = Field(None, description="完成时间")


class ScanResult(BaseModel):
    """扫描结果项"""
    code: str
    name: str
    price: float
    pct_change: float = Field(..., description="涨跌幅")
    action: str = Field(..., description="操作建议")
    action_reason: str = Field(..., description="建议原因")
    patterns: List[str] = Field(default_factory=list, description="检测到的形态")
    bullish_count: int = Field(0, description="看涨因素数")
    bearish_count: int = Field(0, description="看跌因素数")
    score: int = Field(0, description="综合评分")


class ScanResultResponse(BaseModel):
    """扫描结果响应"""
    task_id: str
    status: str
    progress: int
    total: int
    processed: int
    results: List[ScanResult] = Field(default_factory=list, description="扫描结果（按评分排序）")
    buy_signals: List[ScanResult] = Field(default_factory=list, description="买入信号")
    sell_signals: List[ScanResult] = Field(default_factory=list, description="卖出信号")
    error: Optional[str] = Field(None, description="错误信息")
