"""
反转三兄弟 - A股监控系统
Streamlit 主应用入口
"""
import streamlit as st
from datetime import datetime

from data.fetcher import DataFetcher
from signals.analyzer import StrategyAnalyzer, ActionType
from database.models import Database
from config import INDEX_CODES

# 页面配置
st.set_page_config(
    page_title="反转三兄弟 - A股监控",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化
db = Database()
analyzer = StrategyAnalyzer()
fetcher = DataFetcher()


def render_signal_card(code: str, name: str, action: str, reason: str):
    """渲染信号卡片"""
    colors = {
        "买入": ("#e8f5e9", "#4caf50", "🟢"),
        "加仓": ("#e8f5e9", "#66bb6a", "🟢"),
        "卖出": ("#ffebee", "#f44336", "🔴"),
        "减仓": ("#fff3e0", "#ff9800", "🟠"),
        "持有观望": ("#f5f5f5", "#9e9e9e", "⚪"),
    }
    bg, border, emoji = colors.get(action, ("#f5f5f5", "#9e9e9e", "⚪"))

    st.markdown(
        f"""
        <div style="
            background-color: {bg};
            border-left: 4px solid {border};
            padding: 12px 15px;
            margin: 8px 0;
            border-radius: 4px;
        ">
            <strong>{emoji} {action}</strong> |
            <strong>{code}</strong> {name}<br>
            <small style="color: #666;">{reason}</small>
        </div>
        """,
        unsafe_allow_html=True
    )


def main():
    # 标题
    st.title("📈 反转三兄弟 - A股监控系统")

    # 显示更新时间
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.caption(f"最后更新: {now}")

    # 刷新按钮
    if st.button("🔄 刷新数据"):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    # ============ 今日自选股信号 ============
    st.subheader("🔔 今日自选股信号")

    watchlist = db.get_watchlist()

    if not watchlist:
        st.info("暂无自选股，请前往「自选股」页面添加")
    else:
        buy_signals = []
        sell_signals = []
        hold_signals = []

        with st.spinner("正在分析自选股..."):
            for stock in watchlist:
                code = stock["code"]
                name = stock["name"]

                df = fetcher.get_stock_data(code, days=60)
                if df is None:
                    continue

                analysis = analyzer.analyze(df, code, name)
                if analysis is None:
                    continue

                signal_data = {
                    "code": code,
                    "name": name,
                    "action": analysis.action.value,
                    "reason": analysis.action_reason,
                    "price": analysis.current_price
                }

                if analysis.action in (ActionType.BUY, ActionType.ADD):
                    buy_signals.append(signal_data)
                elif analysis.action in (ActionType.SELL, ActionType.REDUCE):
                    sell_signals.append(signal_data)
                else:
                    hold_signals.append(signal_data)

        # 显示信号
        if buy_signals:
            st.markdown("**买入/加仓信号:**")
            for sig in buy_signals:
                render_signal_card(sig["code"], sig["name"], sig["action"], sig["reason"])

        if sell_signals:
            st.markdown("**卖出/减仓信号:**")
            for sig in sell_signals:
                render_signal_card(sig["code"], sig["name"], sig["action"], sig["reason"])

        if not buy_signals and not sell_signals:
            st.success("今日自选股暂无明确买卖信号")

        if hold_signals:
            with st.expander(f"持有观望 ({len(hold_signals)}只)"):
                for sig in hold_signals:
                    st.write(f"- {sig['code']} {sig['name']}: {sig['reason']}")

    st.divider()

    # ============ 大盘信号 ============
    st.subheader("📊 大盘信号")

    cols = st.columns(len(INDEX_CODES))

    for i, (name, code) in enumerate(INDEX_CODES.items()):
        with cols[i]:
            try:
                df = fetcher.get_index_data(code, days=60)

                if df is not None and len(df) >= 2:
                    current = df.iloc[-1]
                    prev = df.iloc[-2]

                    price = current["close"]
                    pct_change = (price - prev["close"]) / prev["close"] * 100

                    # 分析
                    analysis = analyzer.analyze(df, code, name)
                    signal_text = "⚪ 无信号"
                    if analysis:
                        if analysis.action in (ActionType.BUY, ActionType.ADD):
                            signal_text = f"🟢 {analysis.action.value}"
                        elif analysis.action in (ActionType.SELL, ActionType.REDUCE):
                            signal_text = f"🔴 {analysis.action.value}"

                    st.metric(
                        label=name,
                        value=f"{price:.2f}",
                        delta=f"{pct_change:+.2f}%"
                    )
                    st.caption(signal_text)

                    # 显示主要形态
                    if analysis and analysis.patterns:
                        for p in analysis.patterns[:1]:
                            st.caption(f"📍 {p['name']}")
                else:
                    st.metric(label=name, value="--")

            except Exception as e:
                st.metric(label=name, value="--")

    st.divider()

    # ============ 快速链接 ============
    st.subheader("📌 快速操作")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.page_link("pages/1_自选股.py", label="⭐ 管理自选股", icon="⭐")

    with col2:
        st.page_link("pages/2_Top10推荐.py", label="🏆 Top10推荐", icon="🏆")

    with col3:
        st.page_link("pages/3_自选ETF.py", label="📊 自选ETF", icon="📊")

    # ============ 侧边栏 ============
    with st.sidebar:
        st.header("反转三兄弟")
        st.caption("基于K线形态的买卖信号监控")

        st.divider()

        st.subheader("自选股")
        if watchlist:
            for stock in watchlist[:10]:
                st.text(f"{stock['code']} {stock['name']}")
            if len(watchlist) > 10:
                st.caption(f"...共 {len(watchlist)} 只")
        else:
            st.caption("暂无自选股")

        st.divider()

        st.subheader("策略要点")
        st.markdown("""
        - **吞没形态**: 阳吞阴/阴吞阳
        - **乌云盖顶/刺透**: 跳空反转
        - **锤子线**: 底部信号
        - **量价配合**: 放量确认
        - **均线支撑**: 5/10/20/30日
        - **MACD金叉死叉**
        """)


if __name__ == "__main__":
    main()
