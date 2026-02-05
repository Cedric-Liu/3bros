"""
ETF API路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List

from ...deps import get_db
from ...core.fetcher import DataFetcher
from ...core.analyzer import StrategyAnalyzer
from ...schemas.etf import (
    AddToETFWatchlistRequest,
    ETFWatchlistResponse,
    ETFInWatchlist,
    ETFSearchResponse,
    ETFSearchResult,
    PopularETFResponse,
    PopularETF
)
from ...schemas.stock import StrategyAnalysisResponse, PatternInfo, SupportResistanceLine

router = APIRouter()
fetcher = DataFetcher()
analyzer = StrategyAnalyzer()


@router.get("/watchlist", response_model=ETFWatchlistResponse)
async def get_etf_watchlist():
    """获取ETF自选列表"""
    db = get_db()
    items = db.get_etf_watchlist()
    return ETFWatchlistResponse(
        items=[ETFInWatchlist(**item) for item in items],
        total=len(items)
    )


@router.post("/watchlist")
async def add_to_etf_watchlist(request: AddToETFWatchlistRequest):
    """添加ETF到自选"""
    db = get_db()
    success = db.add_to_etf_watchlist(request.code, request.name, request.notes or "")
    if not success:
        raise HTTPException(status_code=400, detail="添加失败")
    return {"success": True, "message": f"已添加 {request.code} {request.name}"}


@router.delete("/watchlist/{code}")
async def remove_from_etf_watchlist(code: str):
    """从ETF自选中移除"""
    db = get_db()
    success = db.remove_from_etf_watchlist(code)
    if not success:
        raise HTTPException(status_code=400, detail="删除失败")
    return {"success": True, "message": f"已删除 {code}"}


@router.get("/popular", response_model=PopularETFResponse)
async def get_popular_etfs():
    """获取热门ETF列表"""
    etfs = fetcher.get_popular_etfs()
    return PopularETFResponse(
        items=[PopularETF(**etf) for etf in etfs]
    )


@router.get("/search", response_model=ETFSearchResponse)
async def search_etfs(
    keyword: str = Query(..., min_length=1, description="搜索关键词")
):
    """搜索ETF"""
    results = fetcher.search_etf(keyword)
    return ETFSearchResponse(
        results=[ETFSearchResult(**r) for r in results]
    )


@router.get("/{code}/analysis", response_model=StrategyAnalysisResponse)
async def get_etf_analysis(code: str):
    """获取ETF详细分析"""
    # 获取ETF名称
    name = fetcher.get_stock_name(code)

    # 获取K线数据
    df = fetcher.get_etf_data(code, days=60)
    if df is None or len(df) < 30:
        raise HTTPException(status_code=404, detail="获取ETF数据失败或数据不足")

    # 分析
    analysis = analyzer.analyze(df, code, name)
    if analysis is None:
        raise HTTPException(status_code=500, detail="分析失败")

    # 转换为响应格式
    return StrategyAnalysisResponse(
        code=analysis.code,
        name=analysis.name,
        current_price=analysis.current_price,
        volume_status=analysis.volume_status,
        volume_ratio=analysis.volume_ratio,
        price_new_high=analysis.price_new_high,
        price_new_low=analysis.price_new_low,
        volume_price_conclusion=analysis.volume_price_conclusion,
        support_lines=[SupportResistanceLine(**s) for s in analysis.support_lines],
        resistance_lines=[SupportResistanceLine(**r) for r in analysis.resistance_lines],
        near_support=analysis.near_support,
        near_resistance=analysis.near_resistance,
        support_break_status=analysis.support_break_status,
        resistance_break_status=analysis.resistance_break_status,
        upper_shadow_ratio=analysis.upper_shadow_ratio,
        upper_shadow_warning=analysis.upper_shadow_warning,
        upper_shadow_detail=analysis.upper_shadow_detail,
        ma_status=analysis.ma_status,
        ma_support=analysis.ma_support,
        macd_status=analysis.macd_status,
        macd_cross=analysis.macd_cross,
        patterns=[PatternInfo(**p) for p in analysis.patterns],
        pattern_analysis=analysis.pattern_analysis,
        trend_5d=analysis.trend_5d,
        trend_10d=analysis.trend_10d,
        trend_20d=analysis.trend_20d,
        action=analysis.action.value,
        action_reason=analysis.action_reason,
        action_detail=analysis.action_detail,
        bullish_factors=analysis.bullish_factors,
        bearish_factors=analysis.bearish_factors,
        risk_level=analysis.risk_level,
        position_advice=analysis.position_advice
    )
