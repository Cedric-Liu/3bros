"""
自选股管理页面 - 反转三兄弟策略分析
"""
import streamlit as st

from data.fetcher import DataFetcher
from signals.analyzer import StrategyAnalyzer, ActionType
from database.models import Database

st.set_page_config(
    page_title="自选股 - 反转三兄弟",
    page_icon="⭐",
    layout="wide"
)

# 初始化
db = Database()
analyzer = StrategyAnalyzer()
fetcher = DataFetcher()


def render_action_badge(action: str, size: str = "normal"):
    """渲染操作建议标签"""
    colors = {
        "买入": ("🟢", "#e8f5e9", "#2e7d32"),
        "加仓": ("🟢", "#e8f5e9", "#4caf50"),
        "卖出": ("🔴", "#ffebee", "#c62828"),
        "减仓": ("🟠", "#fff3e0", "#ef6c00"),
        "持有观望": ("⚪", "#f5f5f5", "#616161"),
    }
    emoji, bg, color = colors.get(action, ("⚪", "#f5f5f5", "#616161"))

    font_size = "18px" if size == "normal" else "14px"
    padding = "8px 16px" if size == "normal" else "4px 10px"

    return f"""<span style="
        display: inline-block;
        background: {bg};
        color: {color};
        padding: {padding};
        border-radius: 20px;
        font-weight: bold;
        font-size: {font_size};
    ">{emoji} {action}</span>"""


def render_detailed_analysis(analysis, buy_info=None, code=None):
    """渲染详细策略分析"""
    if analysis is None:
        st.warning("数据不足，无法分析")
        return

    # === 妈妈的持仓信息 ===
    if buy_info and buy_info.get("buy_price"):
        buy_price = buy_info["buy_price"]
        buy_date = buy_info.get("buy_date", "")
        buy_qty = buy_info.get("buy_quantity", 0)
        current_price = analysis.current_price

        profit_pct = ((current_price - buy_price) / buy_price) * 100
        profit_amount = (current_price - buy_price) * (buy_qty or 0)

        if profit_pct >= 0:
            profit_color = "green"
            profit_emoji = "📈"
        else:
            profit_color = "red"
            profit_emoji = "📉"

        st.markdown("### 💰 妈妈的持仓情况")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("买入价格", f"¥{buy_price:.2f}", f"买入日期: {buy_date}")
        with col2:
            st.metric("当前价格", f"¥{current_price:.2f}",
                     f"{profit_pct:+.2f}%", delta_color="normal" if profit_pct >= 0 else "inverse")
        with col3:
            if buy_qty:
                st.metric("持仓数量", f"{buy_qty}股", f"盈亏: ¥{profit_amount:+.0f}")

        # 个性化建议
        st.markdown("**💡 给妈妈的建议：**")
        if profit_pct >= 20:
            st.success(f"🎉 恭喜妈妈！已经赚了{profit_pct:.1f}%，可以考虑卖掉一部分锁定利润。")
        elif profit_pct >= 10:
            st.info(f"👍 不错哦！赚了{profit_pct:.1f}%，可以继续持有，但要注意设置止盈点。")
        elif profit_pct >= 0:
            st.info(f"📊 小赚{profit_pct:.1f}%，继续观察，不要急着卖。")
        elif profit_pct >= -5:
            st.warning(f"😐 小亏{abs(profit_pct):.1f}%，正常波动，先别慌。")
        elif profit_pct >= -10:
            st.warning(f"😟 亏了{abs(profit_pct):.1f}%，要注意了。如果趋势转弱，考虑减仓。")
        else:
            st.error(f"😰 亏了{abs(profit_pct):.1f}%，建议认真看下面的分析，考虑是否止损。")

        st.divider()

    # === 操作建议（最醒目）===
    st.markdown("### 综合建议")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(render_action_badge(analysis.action.value), unsafe_allow_html=True)
        st.markdown(f"**风险等级**: {analysis.risk_level}")
        st.markdown(f"**仓位建议**: {analysis.position_advice}")

    with col2:
        st.markdown(f"**判断依据**: {analysis.action_reason}")
        st.markdown(f"**详细分析**: {analysis.action_detail}")

    st.divider()

    # === 多空因素对比 ===
    st.markdown("### 多空因素分析")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🟢 看多因素**")
        if analysis.bullish_factors:
            for f in analysis.bullish_factors:
                st.markdown(f"- {f}")
        else:
            st.markdown("*暂无明显看多信号*")

    with col2:
        st.markdown("**🔴 看空因素**")
        if analysis.bearish_factors:
            for f in analysis.bearish_factors:
                st.markdown(f"- {f}")
        else:
            st.markdown("*暂无明显看空信号*")

    st.divider()

    # === 反转形态 ===
    st.markdown("### 反转三兄弟形态")
    if analysis.patterns:
        for p in analysis.patterns:
            emoji = "🟢" if p["type"] == "看涨" else ("🔴" if p["type"] == "看跌" else "⚪")
            bg = '#e8f5e9' if p['type'] == '看涨' else '#ffebee' if p['type'] == '看跌' else '#f5f5f5'
            position = p.get('position_advice', '')
            position_text = f"<br><b>仓位建议: {position}</b>" if position else ""
            st.markdown(
                f"""<div style="background: {bg}; padding: 10px; border-radius: 8px; margin: 5px 0;">
                {emoji} <b>{p['name']}</b> ({p['type']}, 强度: {p['strength']})<br>
                <small>{p['desc']}</small>{position_text}</div>""",
                unsafe_allow_html=True
            )
    else:
        st.info("今日无明显反转形态")

    # 显示形态分析说明（为什么没形成）
    if analysis.pattern_analysis:
        st.markdown("**📋 形态分析详情:**")
        for reason in analysis.pattern_analysis:
                st.markdown(f"- {reason}")

    st.divider()

    # === 关键指标 ===
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 量价分析")
        vol_emoji = "📈" if analysis.volume_status == "放量" else ("📉" if analysis.volume_status == "缩量" else "➖")
        st.markdown(f"**量能**: {vol_emoji} {analysis.volume_status}")
        st.markdown(f"**量比**: {analysis.volume_ratio}")
        st.markdown(f"**结论**: {analysis.volume_price_conclusion}")

        if analysis.price_new_high:
            st.success("🔺 创近期新高")
        if analysis.price_new_low:
            st.error("🔻 创近期新低")

    with col2:
        st.markdown("### 趋势分析")
        st.markdown(f"**5日趋势**: {analysis.trend_5d}")
        st.markdown(f"**10日趋势**: {analysis.trend_10d}")
        st.markdown(f"**20日趋势**: {analysis.trend_20d}")

        st.markdown("---")
        st.markdown("### 上影线分析")
        if analysis.upper_shadow_warning:
            st.warning(f"⚠️ 上影线/实体比: {analysis.upper_shadow_ratio}")
        else:
            st.success(f"✅ 上影线/实体比: {analysis.upper_shadow_ratio}")
        st.caption(analysis.upper_shadow_detail)

    with col3:
        st.markdown("### MACD")
        st.markdown(f"**状态**: {analysis.macd_status}")
        if analysis.macd_cross == "金叉":
            st.success("🟢 金叉信号")
        elif analysis.macd_cross == "死叉":
            st.error("🔴 死叉信号")
        else:
            st.markdown("无交叉信号")

    # === 压力/支撑详细分析（独立section）===
    st.divider()
    st.markdown("### 📊 压力线/支撑线详细分析")
    st.markdown(f"**当前价格: {analysis.current_price:.2f}**")

    col_s, col_r = st.columns(2)

    with col_s:
        st.markdown("**🟢 支撑线（来自大阳线）**")
        st.caption("支撑线是股价下跌时可能止跌的位置")
        if analysis.support_lines:
            ref_date = analysis.support_lines[0].get("ref_date", "")
            days_ago = analysis.support_lines[0].get("days_ago", 0)
            ref_open = analysis.support_lines[0].get("ref_open", 0)
            ref_close = analysis.support_lines[0].get("ref_close", 0)
            st.markdown(f"📅 参考: {ref_date}的大阳线（{days_ago}天前）")
            st.markdown(f"当日开盘{ref_open} → 收盘{ref_close}")
            st.markdown("---")
            for s in analysis.support_lines:
                vs_current = s.get("vs_current", "")
                color = "green" if "高于" in vs_current else "red"
                st.markdown(f"**{s['name']}**: ¥{s['price']}")
                st.markdown(f"<span style='color:{color}'>{vs_current}</span>", unsafe_allow_html=True)
                st.caption(f"计算: {s.get('calculation', '')}")
            if analysis.support_break_status:
                st.error(f"⚠️ {analysis.support_break_status}")
            elif analysis.near_support:
                st.success("📍 当前价格接近支撑位，可能有支撑")
        else:
            st.info("最近60天无大阳线，暂无支撑线参考")

    with col_r:
        st.markdown("**🔴 压力线（来自大阴线）**")
        st.caption("压力线是股价上涨时可能受阻的位置")
        if analysis.resistance_lines:
            ref_date = analysis.resistance_lines[0].get("ref_date", "")
            days_ago = analysis.resistance_lines[0].get("days_ago", 0)
            ref_open = analysis.resistance_lines[0].get("ref_open", 0)
            ref_close = analysis.resistance_lines[0].get("ref_close", 0)
            st.markdown(f"📅 参考: {ref_date}的大阴线（{days_ago}天前）")
            st.markdown(f"当日开盘{ref_open} → 收盘{ref_close}")
            st.markdown("---")
            for r in analysis.resistance_lines:
                vs_current = r.get("vs_current", "")
                color = "red" if "高于" in vs_current else "green"
                st.markdown(f"**{r['name']}**: ¥{r['price']}")
                st.markdown(f"<span style='color:{color}'>{vs_current}</span>", unsafe_allow_html=True)
                st.caption(f"计算: {r.get('calculation', '')}")
            if analysis.resistance_break_status:
                if "放量突破" in analysis.resistance_break_status:
                    st.success(f"🚀 {analysis.resistance_break_status}")
                else:
                    st.warning(f"📍 {analysis.resistance_break_status}")
            elif analysis.near_resistance:
                st.warning("📍 当前价格接近压力位，上涨可能受阻")
        else:
            st.info("最近60天无大阴线，暂无压力线参考")

    # 操作提示（通俗易懂版）
    st.markdown("---")
    st.markdown("""
    **💡 妈妈看这里 - 简单操作指南：**
    - 如果股价**跌破支撑1/2** → 说明跌得比较深了，建议卖掉30-50%
    - 如果股价**跌破支撑1/3** → 小跌，可以先卖10-20%观望
    - 如果股价**放量突破压力** → 好兆头！可以适当买入
    - 如果股价**缩量突破压力** → 力度不够，先别追，等回调
    """)

    st.divider()

    # === 均线分析 ===
    st.markdown("### 均线状态 (7/18/30/89日)")
    st.markdown(f"**综合判断**: {analysis.ma_support}")

    if analysis.ma_status:
        cols = st.columns(len(analysis.ma_status))
        for i, (ma_name, ma_info) in enumerate(analysis.ma_status.items()):
            with cols[i]:
                status = "🟢" if ma_info["above"] else "🔴"
                st.metric(
                    label=f"{status} {ma_name}",
                    value=f"{ma_info['value']:.2f}",
                    delta=f"{ma_info['diff_pct']:+.1f}%"
                )


def main():
    st.title("⭐ 自选股 - 策略分析")

    # ============ 添加股票 ============
    with st.expander("➕ 添加股票", expanded=False):
        col1, col2 = st.columns([3, 1])

        with col1:
            search_keyword = st.text_input(
                "搜索股票",
                placeholder="输入股票代码，如 600519、688001",
                key="stock_search"
            )

        with col2:
            st.write("")
            st.write("")
            search_btn = st.button("🔍 搜索", use_container_width=True)

        if search_keyword and (search_btn or len(search_keyword) >= 4):
            results = fetcher.search_stock(search_keyword)

            if results:
                for stock in results[:8]:
                    code = stock["code"]
                    name = stock["name"]
                    in_watchlist = db.is_in_watchlist(code)

                    cols = st.columns([2, 3, 2])
                    cols[0].write(code)
                    cols[1].write(name)

                    if in_watchlist:
                        cols[2].write("✅ 已添加")
                    else:
                        if cols[2].button("➕ 添加", key=f"add_{code}"):
                            if db.add_to_watchlist(code, name):
                                st.success(f"已添加 {code} {name}")
                                st.rerun()
            else:
                st.warning("未找到股票")

    st.divider()

    # ============ 自选股分析 ============
    watchlist = db.get_watchlist()

    if not watchlist:
        st.info("暂无自选股，请在上方搜索添加")
        return

    # 刷新按钮
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 刷新分析"):
            st.cache_data.clear()
            st.rerun()

    st.write(f"共 {len(watchlist)} 只股票")

    # 分析所有股票
    analysis_results = {
        "买入": [],
        "加仓": [],
        "减仓": [],
        "卖出": [],
        "持有观望": []
    }

    with st.spinner("正在分析自选股..."):
        for stock in watchlist:
            code = stock["code"]
            name = stock["name"]

            df = fetcher.get_stock_data(code, days=120)
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

    # ============ 分类显示 ============

    def render_stock_item(item, expanded=True):
        """渲染单只股票的详细信息"""
        code = item['code']
        buy_info = db.get_buy_info(code)

        with st.expander(f"**{code}** {item['name']} - {item['analysis'].action_reason}", expanded=expanded):
            # 操作按钮行
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown(f"**当前价格**: ¥{item['price']:.2f}")
            with col3:
                if st.button("🗑️ 删除", key=f"del_{code}"):
                    db.remove_from_watchlist(code)
                    st.rerun()

            # 买入信息录入
            with st.container():
                st.markdown("**📝 记录妈妈的买入信息：**")
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                with col1:
                    buy_price = st.number_input(
                        "买入价格",
                        value=float(buy_info.get("buy_price") or 0),
                        min_value=0.0,
                        step=0.01,
                        key=f"price_{code}"
                    )
                with col2:
                    buy_date = st.text_input(
                        "买入日期",
                        value=buy_info.get("buy_date") or "",
                        placeholder="如: 2024-01-15",
                        key=f"date_{code}"
                    )
                with col3:
                    buy_qty = st.number_input(
                        "买入数量(股)",
                        value=int(buy_info.get("buy_quantity") or 0),
                        min_value=0,
                        step=100,
                        key=f"qty_{code}"
                    )
                with col4:
                    st.write("")
                    st.write("")
                    if st.button("💾 保存", key=f"save_{code}"):
                        db.update_buy_info(
                            code,
                            buy_price=buy_price if buy_price > 0 else None,
                            buy_date=buy_date if buy_date else None,
                            buy_quantity=buy_qty if buy_qty > 0 else None
                        )
                        st.success("已保存!")
                        st.rerun()

            st.divider()

            # 获取最新buy_info
            buy_info_updated = db.get_buy_info(code)
            render_detailed_analysis(item['analysis'], buy_info_updated, code)

    # 买入信号
    if analysis_results["买入"]:
        st.markdown("## 🟢 买入信号")
        st.caption("这些股票有买入机会，可以考虑建仓")
        for item in analysis_results["买入"]:
            render_stock_item(item, expanded=True)

    # 加仓信号
    if analysis_results["加仓"]:
        st.markdown("## 🟢 加仓信号")
        st.caption("这些股票可以考虑追加投资")
        for item in analysis_results["加仓"]:
            render_stock_item(item, expanded=True)

    # 减仓信号
    if analysis_results["减仓"]:
        st.markdown("## 🟠 减仓信号")
        st.caption("这些股票出现转弱迹象，可以卖掉一部分")
        for item in analysis_results["减仓"]:
            render_stock_item(item, expanded=False)

    # 卖出信号
    if analysis_results["卖出"]:
        st.markdown("## 🔴 卖出信号")
        st.caption("这些股票建议尽快卖出")
        for item in analysis_results["卖出"]:
            render_stock_item(item, expanded=False)

    # 持有观望
    if analysis_results["持有观望"]:
        st.markdown("## ⚪ 持有观望")
        st.caption("这些股票暂时没有明确信号，先拿着别动")
        for item in analysis_results["持有观望"]:
            render_stock_item(item, expanded=False)


if __name__ == "__main__":
    main()
