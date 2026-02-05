"""
ETF相关的Pydantic模型
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ETFBase(BaseModel):
    """ETF基础信息"""
    code: str = Field(..., description="ETF代码")
    name: str = Field(..., description="ETF名称")


class ETFInWatchlist(ETFBase):
    """自选ETF信息"""
    added_at: Optional[str] = Field(None, description="添加时间")
    sort_order: Optional[int] = Field(0, description="排序")
    notes: Optional[str] = Field(None, description="备注")


class ETFWithQuote(ETFBase):
    """带行情的ETF信息"""
    price: Optional[float] = Field(None, description="当前价格")
    prev_close: Optional[float] = Field(None, description="昨收")
    change: Optional[float] = Field(None, description="涨跌额")
    pct_change: Optional[float] = Field(None, description="涨跌幅")
    volume: Optional[float] = Field(None, description="成交量")


class PopularETF(ETFBase):
    """热门ETF"""
    category: str = Field(..., description="分类: 宽基/行业")


class AddToETFWatchlistRequest(BaseModel):
    """添加ETF到自选请求"""
    code: str = Field(..., description="ETF代码")
    name: str = Field(..., description="ETF名称")
    notes: Optional[str] = Field("", description="备注")


class ETFWatchlistResponse(BaseModel):
    """ETF自选列表响应"""
    items: List[ETFInWatchlist]
    total: int


class ETFSearchResult(BaseModel):
    """ETF搜索结果"""
    code: str
    name: str


class ETFSearchResponse(BaseModel):
    """ETF搜索响应"""
    results: List[ETFSearchResult]


class PopularETFResponse(BaseModel):
    """热门ETF响应"""
    items: List[PopularETF]
