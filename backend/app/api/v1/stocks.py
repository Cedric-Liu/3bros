"""
股票API路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from ...deps import get_db
from ...core.fetcher import DataFetcher
from ...core.analyzer import StrategyAnalyzer
from ...schemas.stock import (
    AddToWatchlistRequest,
    UpdateBuyInfoRequest,
    WatchlistResponse,
    StockInWatchlist,
    SearchResponse,
    SearchResult,
    BuyInfoResponse,
    StrategyAnalysisResponse,
    PatternInfo,
    SupportResistanceLine,
    StockSignalSummary,
    WatchlistWithSignals,
    KlineDataPoint,
    KlineResponse
)

router = APIRouter()
fetcher = DataFetcher()
analyzer = StrategyAnalyzer()


@router.get("/watchlist", response_model=WatchlistResponse)
async def get_watchlist():
    """获取自选股列表"""
    db = get_db()
    items = db.get_watchlist()
    return WatchlistResponse(
        items=[StockInWatchlist(**item) for item in items],
        total=len(items)
    )


@router.post("/watchlist")
async def add_to_watchlist(request: AddToWatchlistRequest):
    """添加自选股"""
    db = get_db()
    success = db.add_to_watchlist(request.code, request.name, request.notes or "")
    if not success:
        raise HTTPException(status_code=400, detail="添加失败")
    return {"success": True, "message": f"已添加 {request.code} {request.name}"}


@router.delete("/watchlist/{code}")
async def remove_from_watchlist(code: str):
    """删除自选股"""
    db = get_db()
    success = db.remove_from_watchlist(code)
    if not success:
        raise HTTPException(status_code=400, detail="删除失败")
    return {"success": True, "message": f"已删除 {code}"}


@router.get("/watchlist/signals", response_model=WatchlistWithSignals)
async def get_watchlist_with_signals():
    """获取带信号的自选股列表"""
    db = get_db()
    watchlist = db.get_watchlist()

    results = []
    for stock in watchlist:
        code = stock["code"]
        name = stock["name"]

        # 获取股票数据
        df = fetcher.get_stock_data(code, days=60)
        if df is None or len(df) < 30:
            results.append(StockSignalSummary(
                code=code,
                name=name,
                current_price=0,
                action="持有观望",
                action_reason="数据不足",
                risk_level="低",
                volume_status="平量",
                volume_ratio=1.0,
                macd_cross="无",
                patterns=[]
            ))
            continue

        # 分析
        analysis = analyzer.analyze(df, code, name)
        if analysis is None:
            results.append(StockSignalSummary(
                code=code,
                name=name,
                current_price=df["close"].iloc[-1] if len(df) > 0 else 0,
                action="持有观望",
                action_reason="分析失败",
                risk_level="低",
                volume_status="平量",
                volume_ratio=1.0,
                macd_cross="无",
                patterns=[]
            ))
            continue

        results.append(StockSignalSummary(
            code=code,
            name=name,
            current_price=analysis.current_price,
            action=analysis.action.value,
            action_reason=analysis.action_reason,
            risk_level=analysis.risk_level,
            volume_status=analysis.volume_status,
            volume_ratio=analysis.volume_ratio,
            macd_cross=analysis.macd_cross,
            patterns=[p["name"] for p in analysis.patterns]
        ))

    return WatchlistWithSignals(items=results, total=len(results))


@router.get("/search", response_model=SearchResponse)
async def search_stocks(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    include_etf: bool = Query(False, description="是否包含ETF")
):
    """搜索股票"""
    results = fetcher.search_stock(keyword, include_etf)
    return SearchResponse(
        results=[SearchResult(**r) for r in results]
    )


@router.get("/{code}/klines", response_model=KlineResponse)
async def get_stock_klines(
    code: str,
    days: int = Query(60, ge=1, le=365, description="获取天数")
):
    """获取股票K线数据及支撑压力线"""
    name = fetcher.get_stock_name(code)

    df = fetcher.get_stock_data(code, days=days)
    if df is None or len(df) < 5:
        raise HTTPException(status_code=404, detail="获取K线数据失败或数据不足")

    # 构建K线数据
    klines = []
    for _, row in df.iterrows():
        klines.append(KlineDataPoint(
            date=str(row["date"]) if "date" in row else str(row.name),
            open=float(row["open"]),
            close=float(row["close"]),
            high=float(row["high"]),
            low=float(row["low"]),
            volume=float(row["volume"])
        ))

    # 获取支撑压力线（需要足够数据）
    support_lines_data = []
    resistance_lines_data = []
    if len(df) >= 30:
        analysis = analyzer.analyze(df, code, name)
        if analysis:
            support_lines_data = [SupportResistanceLine(**s) for s in analysis.support_lines]
            resistance_lines_data = [SupportResistanceLine(**r) for r in analysis.resistance_lines]

    return KlineResponse(
        code=code,
        name=name,
        klines=klines,
        support_lines=support_lines_data,
        resistance_lines=resistance_lines_data
    )


@router.get("/{code}/analysis", response_model=StrategyAnalysisResponse)
async def get_stock_analysis(code: str):
    """获取股票详细分析"""
    # 获取股票名称
    name = fetcher.get_stock_name(code)

    # 获取K线数据
    df = fetcher.get_stock_data(code, days=60)
    if df is None or len(df) < 30:
        raise HTTPException(status_code=404, detail="获取股票数据失败或数据不足")

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


@router.put("/{code}/buy-info")
async def update_buy_info(code: str, request: UpdateBuyInfoRequest):
    """更新买入信息"""
    db = get_db()

    # 检查是否在自选中
    if not db.is_in_watchlist(code):
        raise HTTPException(status_code=404, detail="股票不在自选中")

    success = db.update_buy_info(
        code,
        buy_price=request.buy_price,
        buy_date=request.buy_date,
        buy_quantity=request.buy_quantity
    )

    if not success:
        raise HTTPException(status_code=400, detail="更新失败")

    return {"success": True, "message": "已更新买入信息"}


@router.get("/{code}/buy-info", response_model=BuyInfoResponse)
async def get_buy_info(code: str):
    """获取买入信息"""
    db = get_db()
    info = db.get_buy_info(code)
    return BuyInfoResponse(**info)


