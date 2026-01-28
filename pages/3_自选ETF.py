"""
自选ETF - ETF监控与推荐
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import time

from data.fetcher import DataFetcher
from signals.analyzer import StrategyAnalyzer, ActionType
from database.models import Database

st.set_page_config(
    page_title="自选ETF - 反转三兄弟",
    page_icon="📊",
    layout="wide"
)

# 初始化
db = Database()
analyzer = StrategyAnalyzer()
fetcher = DataFetcher()


def render_action_badge(action: str):
    """渲染操作建议标签"""
    colors = {
        "买入": ("🟢", "#e8f5e9", "#2e7d32"),
        "加仓": ("🟢", "#e8f5e9", "#4caf50"),
        "卖出": ("🔴", "#ffebee", "#c62828"),
        "减仓": ("🟠", "#fff3e0", "#ef6c00"),
        "持有观望": ("⚪", "#f5f5f5", "#616161"),
    }
    emoji, bg, color = colors.get(action, ("⚪", "#f5f5f5", "#616161"))
    return f"""<span style="
        display: inline-block;
        background: {bg};
        color: {color};
        padding: 4px 10px;
        border-radius: 15px;
        font-weight: bold;
        font-size: 14px;
    ">{emoji} {action}</span>"""


def render_etf_analysis(analysis):
    """渲染ETF详细分析"""
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(render_action_badge(analysis.action.value), unsafe_allow_html=True)
        st.markdown(f"**当前价格**: {analysis.current_price:.3f}")
        st.markdown(f"**风险等级**: {analysis.risk_level}")
        st.markdown(f"**仓位建议**: {analysis.position_advice}")

    with col2:
        st.markdown(f"**判断依据**: {analysis.action_reason}")
        st.markdown(f"**详细分析**: {analysis.action_detail}")

    # 多空因素
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**看多因素**")
        if analysis.bullish_factors:
            for f in analysis.bullish_factors[:3]:
                st.markdown(f"- {f}")
        else:
            st.markdown("*暂无*")

    with col2:
        st.markdown("**看空因素**")
        if analysis.bearish_factors:
            for f in analysis.bearish_factors[:3]:
                st.markdown(f"- {f}")
        else:
            st.markdown("*暂无*")

    # 趋势和均线
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**5日趋势**: {analysis.trend_5d}")
    with col2:
        st.markdown(f"**10日趋势**: {analysis.trend_10d}")
    with col3:
        st.markdown(f"**MACD**: {analysis.macd_cross if analysis.macd_cross != '无' else '无信号'}")


def main():
    st.title("📊 自选ETF")
    st.caption("ETF监控与策略分析")

    # ============ Tab布局 ============
    tab1, tab2, tab3 = st.tabs(["📋 我的ETF", "🔍 搜索ETF", "🏆 热门ETF推荐"])

    # ============ 我的ETF ============
    with tab1:
        # 获取自选ETF列表
        etf_watchlist = db.get_etf_watchlist()

        if not etf_watchlist:
            st.info("暂无自选ETF，请在「搜索ETF」或「热门ETF推荐」中添加")
        else:
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("🔄 刷新分析"):
                    st.cache_data.clear()
                    st.rerun()

            st.write(f"共 {len(etf_watchlist)} 只ETF")

            # 分析所有ETF
            analysis_results = {
                "买入": [],
                "加仓": [],
                "减仓": [],
                "卖出": [],
                "持有观望": []
            }

            with st.spinner("正在分析自选ETF..."):
                for etf in etf_watchlist:
                    code = etf["code"]
                    name = etf["name"]

                    df = fetcher.get_etf_data(code, days=120)
                    if df is None:
                        continue

                    analysis = analyzer.analyze(df, code, name)
                    if analysis is None:
                        continue

                    analysis_results[analysis.action.value].append({
                        "code": code,
                        "name": name,
                        "analysis": analysis,
                        "price": analysis.current_price
                    })

            # 分类显示
            for action_type in ["买入", "加仓", "减仓", "卖出", "持有观望"]:
                if analysis_results[action_type]:
                    emoji = "🟢" if action_type in ["买入", "加仓"] else ("🔴" if action_type == "卖出" else ("🟠" if action_type == "减仓" else "⚪"))
                    st.markdown(f"### {emoji} {action_type}信号")

                    for item in analysis_results[action_type]:
                        expanded = action_type in ["买入", "加仓"]
                        with st.expander(f"**{item['code']}** {item['name']} - {item['analysis'].action_reason}", expanded=expanded):
                            col1, col2 = st.columns([4, 1])
                            with col2:
                                if st.button("🗑️ 删除", key=f"del_etf_{item['code']}"):
                                    db.remove_from_etf_watchlist(item['code'])
                                    st.rerun()

                            render_etf_analysis(item['analysis'])

    # ============ 搜索ETF ============
    with tab2:
        search_keyword = st.text_input(
            "搜索ETF",
            placeholder="输入ETF代码或名称，如 510300、沪深300",
            key="etf_search"
        )

        if search_keyword and len(search_keyword) >= 2:
            results = fetcher.search_etf(search_keyword)

            if results:
                st.write(f"找到 {len(results)} 个结果")
                for etf in results[:10]:
                    code = etf["code"]
                    name = etf["name"]
                    in_watchlist = db.is_in_etf_watchlist(code)

                    cols = st.columns([2, 3, 2])
                    cols[0].write(code)
                    cols[1].write(name)

                    if in_watchlist:
                        cols[2].write("✅ 已添加")
                    else:
                        if cols[2].button("➕ 添加", key=f"add_etf_{code}"):
                            if db.add_to_etf_watchlist(code, name):
                                st.success(f"已添加 {code} {name}")
                                st.rerun()
            else:
                st.warning("未找到ETF")

    # ============ 热门ETF推荐 ============
    with tab3:
        st.subheader("热门ETF列表")

        popular_etfs = fetcher.get_popular_etfs()

        # 按类别分组显示
        categories = {}
        for etf in popular_etfs:
            cat = etf.get("category", "其他")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(etf)

        for cat, etfs in categories.items():
            st.markdown(f"**{cat}ETF**")

            for etf in etfs:
                code = etf["code"]
                name = etf["name"]
                in_watchlist = db.is_in_etf_watchlist(code)

                cols = st.columns([2, 3, 2, 2])
                cols[0].write(code)
                cols[1].write(name)

                # 获取实时行情
                try:
                    quote = fetcher.get_realtime_quote(code)
                    if quote:
                        pct = quote.get("pct_change", 0)
                        color = "red" if pct > 0 else ("green" if pct < 0 else "gray")
                        cols[2].markdown(f"<span style='color:{color}'>{pct:+.2f}%</span>", unsafe_allow_html=True)
                except:
                    cols[2].write("--")

                if in_watchlist:
                    cols[3].write("✅ 已添加")
                else:
                    if cols[3].button("➕ 添加", key=f"pop_etf_{code}"):
                        if db.add_to_etf_watchlist(code, name):
                            st.success(f"已添加 {name}")
                            st.rerun()

            st.markdown("---")

        # 一键添加全部
        if st.button("📥 一键添加全部热门ETF"):
            added = 0
            for etf in popular_etfs:
                if not db.is_in_etf_watchlist(etf["code"]):
                    db.add_to_etf_watchlist(etf["code"], etf["name"])
                    added += 1
            st.success(f"已添加 {added} 只ETF")
            st.rerun()

        st.divider()

        # ETF扫描
        st.subheader("ETF买入信号扫描")

        if st.button("🔍 扫描热门ETF买入信号"):
            with st.spinner("正在扫描..."):
                buy_signals = []

                progress = st.progress(0)
                for i, etf in enumerate(popular_etfs):
                    code = etf["code"]
                    name = etf["name"]

                    try:
                        df = fetcher.get_etf_data(code, days=60)
                        if df is not None:
                            analysis = analyzer.analyze(df, code, name)
                            if analysis and analysis.action in (ActionType.BUY, ActionType.ADD):
                                buy_signals.append({
                                    "code": code,
                                    "name": name,
                                    "category": etf.get("category", ""),
                                    "analysis": analysis
                                })
                    except:
                        pass

                    progress.progress((i + 1) / len(popular_etfs))
                    time.sleep(0.1)

                progress.empty()

            if buy_signals:
                st.success(f"发现 {len(buy_signals)} 只ETF有买入信号")

                for sig in buy_signals:
                    with st.expander(f"🟢 **{sig['code']}** {sig['name']} ({sig['category']}) - {sig['analysis'].action_reason}", expanded=True):
                        render_etf_analysis(sig['analysis'])

                        if not db.is_in_etf_watchlist(sig['code']):
                            if st.button("➕ 加自选", key=f"scan_add_{sig['code']}"):
                                db.add_to_etf_watchlist(sig['code'], sig['name'])
                                st.success(f"已添加 {sig['name']}")
            else:
                st.info("热门ETF暂无明显买入信号")


if __name__ == "__main__":
    main()
