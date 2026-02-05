"""
市场API路由
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Optional
from datetime import datetime
import uuid

from ...deps import get_db
from ...core.fetcher import DataFetcher
from ...core.analyzer import StrategyAnalyzer
from ...config import INDEX_CODES
from ...schemas.market import (
    MarketIndicesResponse,
    IndexWithSignal,
    TodaySignalsResponse,
    TodaySignal,
    ScanRequest,
    ScanTaskInfo,
    ScanResult,
    ScanResultResponse
)

router = APIRouter()
fetcher = DataFetcher()
analyzer = StrategyAnalyzer()

# 存储扫描任务状态
scan_tasks: Dict[str, dict] = {}


@router.get("/indices", response_model=MarketIndicesResponse)
async def get_market_indices():
    """获取大盘指数"""
    indices = []

    for name, code in INDEX_CODES.items():
        # 获取指数数据
        df = fetcher.get_index_data(code, days=60)

        if df is None or len(df) < 30:
            indices.append(IndexWithSignal(
                code=code,
                name=name,
                price=0,
                change=0,
                pct_change=0,
                action=None,
                action_reason=None,
                macd_cross=None
            ))
            continue

        current = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else current

        price = current["close"]
        change = price - prev["close"]
        pct_change = (change / prev["close"]) * 100 if prev["close"] > 0 else 0

        # 分析指数
        analysis = analyzer.analyze(df, code, name)

        indices.append(IndexWithSignal(
            code=code,
            name=name,
            price=round(price, 2),
            change=round(change, 2),
            pct_change=round(pct_change, 2),
            volume=current.get("volume", 0),
            action=analysis.action.value if analysis else None,
            action_reason=analysis.action_reason if analysis else None,
            macd_cross=analysis.macd_cross if analysis else None
        ))

    return MarketIndicesResponse(
        indices=indices,
        update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


@router.get("/signals/today", response_model=TodaySignalsResponse)
async def get_today_signals():
    """获取今日信号汇总"""
    db = get_db()
    signals = db.get_today_signals()

    buy_signals = []
    sell_signals = []

    for s in signals:
        signal = TodaySignal(
            code=s["code"],
            name=s["name"],
            signal_type=s["signal_type"],
            pattern_name=s["pattern_name"],
            strength=s["strength"],
            price=s["price"],
            description=s.get("description"),
            confirmations=s.get("confirmations", []),
            detected_at=s.get("detected_at")
        )

        if s["signal_type"] == "买入":
            buy_signals.append(signal)
        else:
            sell_signals.append(signal)

    return TodaySignalsResponse(
        buy_signals=buy_signals,
        sell_signals=sell_signals,
        total=len(signals)
    )


@router.post("/scan", response_model=ScanTaskInfo)
async def start_market_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks
):
    """开始市场扫描（异步）"""
    task_id = str(uuid.uuid4())

    # 初始化任务状态
    scan_tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "total": request.limit or 200,
        "processed": 0,
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "results": [],
        "error": None
    }

    # 在后台运行扫描
    background_tasks.add_task(run_scan_task, task_id, request.limit or 200)

    return ScanTaskInfo(
        task_id=task_id,
        status="pending",
        progress=0,
        total=request.limit or 200,
        processed=0,
        started_at=scan_tasks[task_id]["started_at"]
    )


def run_scan_task(task_id: str, limit: int):
    """执行扫描任务（同步函数，由BackgroundTasks在线程池中运行）"""
    try:
        scan_tasks[task_id]["status"] = "running"

        # 获取活跃股票列表
        stocks = fetcher.get_stocks_for_scan(limit)
        scan_tasks[task_id]["total"] = len(stocks)

        results = []
        buy_signals = []
        sell_signals = []

        for i, stock in enumerate(stocks):
            code = stock["code"]
            name = stock["name"]

            # 更新进度
            scan_tasks[task_id]["processed"] = i + 1
            scan_tasks[task_id]["progress"] = int((i + 1) / len(stocks) * 100)

            try:
                # 获取数据并分析
                df = fetcher.get_stock_data(code, days=60)
                if df is None or len(df) < 30:
                    continue

                analysis = analyzer.analyze(df, code, name)
                if analysis is None:
                    continue

                # 计算评分
                bullish_count = len(analysis.bullish_factors)
                bearish_count = len(analysis.bearish_factors)
                score = len([f for f in analysis.bullish_factors if "【强】" in f]) * 3 + \
                        len([f for f in analysis.bullish_factors if "【中】" in f]) * 1 - \
                        len([f for f in analysis.bearish_factors if "【强】" in f]) * 3 - \
                        len([f for f in analysis.bearish_factors if "【中】" in f]) * 1

                pct_change = stock.get("change_pct", 0)
                try:
                    pct_change = float(pct_change)
                except (ValueError, TypeError):
                    pct_change = 0.0

                result = ScanResult(
                    code=code,
                    name=name,
                    price=float(analysis.current_price),
                    pct_change=pct_change,
                    action=analysis.action.value,
                    action_reason=analysis.action_reason,
                    patterns=[p["name"] for p in analysis.patterns],
                    bullish_count=bullish_count,
                    bearish_count=bearish_count,
                    score=score
                )

                results.append(result)

                # 分类信号
                if analysis.action.value in ["买入", "加仓"]:
                    buy_signals.append(result)
                elif analysis.action.value in ["卖出", "减仓"]:
                    sell_signals.append(result)
            except Exception as e:
                print(f"扫描股票 {code} {name} 失败: {e}")
                continue

        # 按评分排序
        results.sort(key=lambda x: x.score, reverse=True)
        buy_signals.sort(key=lambda x: x.score, reverse=True)
        sell_signals.sort(key=lambda x: x.score, reverse=False)

        scan_tasks[task_id]["results"] = results
        scan_tasks[task_id]["buy_signals"] = buy_signals
        scan_tasks[task_id]["sell_signals"] = sell_signals
        scan_tasks[task_id]["status"] = "completed"
        scan_tasks[task_id]["completed_at"] = datetime.now().isoformat()

    except Exception as e:
        scan_tasks[task_id]["status"] = "failed"
        scan_tasks[task_id]["error"] = str(e)


@router.get("/scan/{task_id}", response_model=ScanResultResponse)
async def get_scan_result(task_id: str):
    """获取扫描进度/结果"""
    if task_id not in scan_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = scan_tasks[task_id]

    return ScanResultResponse(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        total=task["total"],
        processed=task["processed"],
        results=task.get("results", [])[:20],  # 只返回前20个
        buy_signals=task.get("buy_signals", [])[:10],
        sell_signals=task.get("sell_signals", [])[:10],
        error=task.get("error")
    )
