"""
定时任务调度器 - 每日推送
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import Optional

from .notifier import WeChatNotifier
from .fetcher import DataFetcher
from .analyzer import StrategyAnalyzer
from ..deps import get_db


scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """获取调度器实例"""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
    return scheduler


async def daily_push_job():
    """
    每日推送任务
    推送内容：
    1. 大盘指数概况
    2. 自选股信号汇总
    3. Top10扫描结果（热门股信号）
    """
    print(f"[{datetime.now()}] 开始执行每日推送任务...")

    db = get_db()
    notifier = WeChatNotifier(db=db)

    if not notifier.is_configured():
        print("Server酱未配置，跳过推送")
        return

    fetcher = DataFetcher()
    analyzer = StrategyAnalyzer()

    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ========== 1. 大盘指数概况 ==========
    lines.append("## 📊 大盘概况\n")
    try:
        from ..config import INDEX_CODES
        for name, code in INDEX_CODES.items():
            df = fetcher.get_index_data(code, days=5)
            if df is not None and len(df) >= 2:
                current = df.iloc[-1]
                prev = df.iloc[-2]
                price = current["close"]
                pct = (price - prev["close"]) / prev["close"] * 100
                emoji = "🔴" if pct >= 0 else "🟢"
                lines.append(f"{emoji} **{name}** {price:.2f} ({pct:+.2f}%)")
        lines.append("")
    except Exception as e:
        lines.append(f"获取指数失败: {e}\n")

    # ========== 2. 自选股信号汇总 ==========
    lines.append("## 🔔 自选股信号\n")
    try:
        watchlist = db.get_watchlist()
        buy_stocks = []
        sell_stocks = []

        for stock in watchlist:
            code = stock["code"]
            name = stock["name"]

            df = fetcher.get_stock_data(code, days=60)
            if df is None or len(df) < 30:
                continue

            analysis = analyzer.analyze(df, code, name)
            if analysis is None:
                continue

            if analysis.action.value in ["买入", "加仓"]:
                buy_stocks.append({
                    "code": code,
                    "name": name,
                    "action": analysis.action.value,
                    "reason": analysis.action_reason,
                    "price": analysis.current_price,
                    "patterns": [p["name"] for p in analysis.patterns if p["type"] == "看涨"]
                })
            elif analysis.action.value in ["卖出", "减仓"]:
                sell_stocks.append({
                    "code": code,
                    "name": name,
                    "action": analysis.action.value,
                    "reason": analysis.action_reason,
                    "price": analysis.current_price,
                    "patterns": [p["name"] for p in analysis.patterns if p["type"] == "看跌"]
                })

        if buy_stocks:
            lines.append("**买入/加仓信号:**")
            for s in buy_stocks:
                patterns = f" | {', '.join(s['patterns'])}" if s['patterns'] else ""
                lines.append(f"- 🟢 {s['code']} {s['name']} ¥{s['price']:.2f} - {s['action']}{patterns}")
            lines.append("")

        if sell_stocks:
            lines.append("**卖出/减仓信号:**")
            for s in sell_stocks:
                patterns = f" | {', '.join(s['patterns'])}" if s['patterns'] else ""
                lines.append(f"- 🔴 {s['code']} {s['name']} ¥{s['price']:.2f} - {s['action']}{patterns}")
            lines.append("")

        if not buy_stocks and not sell_stocks:
            lines.append("今日自选股无明显信号\n")

    except Exception as e:
        lines.append(f"分析自选股失败: {e}\n")

    # ========== 3. Top10 热门股扫描 ==========
    lines.append("## 🔥 热门股信号 (Top10)\n")
    try:
        # 获取活跃股票
        active_stocks = fetcher.get_stocks_for_scan(limit=50)
        top_buy = []
        top_sell = []

        for stock in active_stocks:  # 扫描前50只
            code = stock["code"]
            name = stock["name"]

            df = fetcher.get_stock_data(code, days=60)
            if df is None or len(df) < 30:
                continue

            analysis = analyzer.analyze(df, code, name)
            if analysis is None:
                continue

            # 计算评分
            bullish_score = len([f for f in analysis.bullish_factors if "【强】" in f]) * 3 + \
                           len([f for f in analysis.bullish_factors if "【中】" in f])
            bearish_score = len([f for f in analysis.bearish_factors if "【强】" in f]) * 3 + \
                           len([f for f in analysis.bearish_factors if "【中】" in f])

            if analysis.action.value in ["买入", "加仓"] and bullish_score >= 3:
                top_buy.append({
                    "code": code,
                    "name": name,
                    "price": analysis.current_price,
                    "action": analysis.action.value,
                    "reason": analysis.action_reason,
                    "score": bullish_score - bearish_score
                })
            elif analysis.action.value in ["卖出", "减仓"] and bearish_score >= 3:
                top_sell.append({
                    "code": code,
                    "name": name,
                    "price": analysis.current_price,
                    "action": analysis.action.value,
                    "reason": analysis.action_reason,
                    "score": bearish_score - bullish_score
                })

        # 按评分排序，取前5
        top_buy.sort(key=lambda x: -x["score"])
        top_sell.sort(key=lambda x: -x["score"])

        if top_buy[:5]:
            lines.append("**买入信号 Top5:**")
            for i, s in enumerate(top_buy[:5], 1):
                lines.append(f"{i}. 🟢 {s['code']} {s['name']} ¥{s['price']:.2f} (+{s['score']}分)")
            lines.append("")

        if top_sell[:5]:
            lines.append("**卖出信号 Top5:**")
            for i, s in enumerate(top_sell[:5], 1):
                lines.append(f"{i}. 🔴 {s['code']} {s['name']} ¥{s['price']:.2f} (+{s['score']}分)")
            lines.append("")

        if not top_buy and not top_sell:
            lines.append("今日热门股无明显信号\n")

    except Exception as e:
        lines.append(f"扫描热门股失败: {e}\n")

    # ========== 发送推送 ==========
    lines.append(f"\n---\n*推送时间: {now}*")

    title = f"反转三兄弟 - {datetime.now().strftime('%m/%d')} 每日信号"
    content = "\n".join(lines)

    success = notifier.send_message(title, content)

    if success:
        print(f"[{datetime.now()}] 每日推送发送成功")
    else:
        print(f"[{datetime.now()}] 每日推送发送失败")


def daily_push_job_sync():
    """同步版本的每日推送任务（供BackgroundTasks使用）"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # 直接运行同步代码
    print(f"[{datetime.now()}] 开始执行每日推送任务...")

    db = get_db()
    notifier = WeChatNotifier(db=db)

    if not notifier.is_configured():
        print("Server酱未配置，跳过推送")
        return

    fetcher = DataFetcher()
    analyzer = StrategyAnalyzer()

    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ========== 1. 大盘指数概况 ==========
    lines.append("## 📊 大盘概况\n")
    try:
        from ..config import INDEX_CODES
        for name, code in INDEX_CODES.items():
            df = fetcher.get_index_data(code, days=5)
            if df is not None and len(df) >= 2:
                current = df.iloc[-1]
                prev = df.iloc[-2]
                price = current["close"]
                pct = (price - prev["close"]) / prev["close"] * 100
                emoji = "🔴" if pct >= 0 else "🟢"
                lines.append(f"{emoji} **{name}** {price:.2f} ({pct:+.2f}%)")
        lines.append("")
    except Exception as e:
        lines.append(f"获取指数失败: {e}\n")

    # ========== 2. 自选股信号汇总 ==========
    lines.append("## 🔔 自选股信号\n")
    try:
        watchlist = db.get_watchlist()
        buy_stocks = []
        sell_stocks = []

        for stock in watchlist:
            code = stock["code"]
            name = stock["name"]

            df = fetcher.get_stock_data(code, days=60)
            if df is None or len(df) < 30:
                continue

            analysis = analyzer.analyze(df, code, name)
            if analysis is None:
                continue

            if analysis.action.value in ["买入", "加仓"]:
                buy_stocks.append({
                    "code": code,
                    "name": name,
                    "action": analysis.action.value,
                    "reason": analysis.action_reason,
                    "price": analysis.current_price,
                    "patterns": [p["name"] for p in analysis.patterns if p["type"] == "看涨"]
                })
            elif analysis.action.value in ["卖出", "减仓"]:
                sell_stocks.append({
                    "code": code,
                    "name": name,
                    "action": analysis.action.value,
                    "reason": analysis.action_reason,
                    "price": analysis.current_price,
                    "patterns": [p["name"] for p in analysis.patterns if p["type"] == "看跌"]
                })

        if buy_stocks:
            lines.append("**买入/加仓信号:**")
            for s in buy_stocks:
                patterns = f" | {', '.join(s['patterns'])}" if s['patterns'] else ""
                lines.append(f"- 🟢 {s['code']} {s['name']} ¥{s['price']:.2f} - {s['action']}{patterns}")
            lines.append("")

        if sell_stocks:
            lines.append("**卖出/减仓信号:**")
            for s in sell_stocks:
                patterns = f" | {', '.join(s['patterns'])}" if s['patterns'] else ""
                lines.append(f"- 🔴 {s['code']} {s['name']} ¥{s['price']:.2f} - {s['action']}{patterns}")
            lines.append("")

        if not buy_stocks and not sell_stocks:
            lines.append("今日自选股无明显信号\n")

    except Exception as e:
        lines.append(f"分析自选股失败: {e}\n")

    # ========== 3. Top10 热门股扫描 ==========
    lines.append("## 🔥 热门股信号 (Top10)\n")
    try:
        active_stocks = fetcher.get_stocks_for_scan(limit=50)
        top_buy = []
        top_sell = []

        for stock in active_stocks:
            code = stock["code"]
            name = stock["name"]

            df = fetcher.get_stock_data(code, days=60)
            if df is None or len(df) < 30:
                continue

            analysis = analyzer.analyze(df, code, name)
            if analysis is None:
                continue

            bullish_score = len([f for f in analysis.bullish_factors if "【强】" in f]) * 3 + \
                           len([f for f in analysis.bullish_factors if "【中】" in f])
            bearish_score = len([f for f in analysis.bearish_factors if "【强】" in f]) * 3 + \
                           len([f for f in analysis.bearish_factors if "【中】" in f])

            if analysis.action.value in ["买入", "加仓"] and bullish_score >= 3:
                top_buy.append({
                    "code": code,
                    "name": name,
                    "price": analysis.current_price,
                    "action": analysis.action.value,
                    "reason": analysis.action_reason,
                    "score": bullish_score - bearish_score
                })
            elif analysis.action.value in ["卖出", "减仓"] and bearish_score >= 3:
                top_sell.append({
                    "code": code,
                    "name": name,
                    "price": analysis.current_price,
                    "action": analysis.action.value,
                    "reason": analysis.action_reason,
                    "score": bearish_score - bullish_score
                })

        top_buy.sort(key=lambda x: -x["score"])
        top_sell.sort(key=lambda x: -x["score"])

        if top_buy[:5]:
            lines.append("**买入信号 Top5:**")
            for i, s in enumerate(top_buy[:5], 1):
                lines.append(f"{i}. 🟢 {s['code']} {s['name']} ¥{s['price']:.2f} (+{s['score']}分)")
            lines.append("")

        if top_sell[:5]:
            lines.append("**卖出信号 Top5:**")
            for i, s in enumerate(top_sell[:5], 1):
                lines.append(f"{i}. 🔴 {s['code']} {s['name']} ¥{s['price']:.2f} (+{s['score']}分)")
            lines.append("")

        if not top_buy and not top_sell:
            lines.append("今日热门股无明显信号\n")

    except Exception as e:
        lines.append(f"扫描热门股失败: {e}\n")

    # ========== 发送推送 ==========
    lines.append(f"\n---\n*推送时间: {now}*")

    title = f"反转三兄弟 - {datetime.now().strftime('%m/%d')} 每日信号"
    content = "\n".join(lines)

    success = notifier.send_message(title, content)

    if success:
        print(f"[{datetime.now()}] 每日推送发送成功")
    else:
        print(f"[{datetime.now()}] 每日推送发送失败")


def start_scheduler():
    """启动调度器"""
    global scheduler
    scheduler = get_scheduler()

    # 从数据库读取推送时间
    db = get_db()
    push_time = db.get_setting("push_time", "15:30")

    try:
        hour, minute = push_time.split(":")
        hour = int(hour)
        minute = int(minute)
    except:
        hour, minute = 15, 30

    # 添加每日推送任务
    scheduler.add_job(
        daily_push_job,
        CronTrigger(hour=hour, minute=minute, day_of_week="mon-fri"),
        id="daily_push",
        replace_existing=True
    )

    scheduler.start()
    print(f"[Scheduler] 定时推送已启动，每个交易日 {hour:02d}:{minute:02d} 推送")


def stop_scheduler():
    """停止调度器"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] 定时推送已停止")


def update_push_time(push_time: str):
    """更新推送时间"""
    global scheduler
    if scheduler is None:
        return

    try:
        hour, minute = push_time.split(":")
        hour = int(hour)
        minute = int(minute)
    except:
        return

    # 重新调度任务
    scheduler.reschedule_job(
        "daily_push",
        trigger=CronTrigger(hour=hour, minute=minute, day_of_week="mon-fri")
    )
    print(f"[Scheduler] 推送时间已更新为 {hour:02d}:{minute:02d}")
