"""
反转三兄弟 Top 10 推荐
扫描市场找到最符合策略的股票
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import time

from data.fetcher import DataFetcher
from signals.analyzer import StrategyAnalyzer, ActionType
from database.models import Database

st.set_page_config(
    page_title="Top10推荐 - 反转三兄弟",
    page_icon="🏆",
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


def render_stock_detail(analysis, show_add_button=True):
    """渲染股票详细分析"""
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(render_action_badge(analysis.action.value), unsafe_allow_html=True)
        st.markdown(f"**当前价格**: {analysis.current_price:.2f}")
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

    # 反转形态
    if analysis.patterns:
        st.markdown("**反转形态**")
        for p in analysis.patterns[:2]:
            emoji = "🟢" if p["type"] == "看涨" else ("🔴" if p["type"] == "看跌" else "⚪")
            st.markdown(f"- {emoji} {p['name']}: {p['desc']}")


def scan_market_for_top10():
    """扫描市场，找到评分最高的10只股票"""
    st.info("正在扫描市场活跃股票...")

    # 获取活跃股票列表
    stocks = fetcher.get_stocks_for_scan(limit=150)

    if not stocks:
        st.error("获取股票列表失败")
        return []

    st.write(f"共获取 {len(stocks)} 只活跃股票，正在分析...")

    results = []
    progress = st.progress(0)

    for i, stock in enumerate(stocks):
        code = stock["code"]
        name = stock["name"]

        try:
            df = fetcher.get_stock_data(code, days=60)
            if df is not None and len(df) >= 30:
                analysis = analyzer.analyze(df, code, name)
                if analysis:
                    # 计算综合评分
                    bullish_score = len([f for f in analysis.bullish_factors if "【强】" in f]) * 3 + \
                                    len([f for f in analysis.bullish_factors if "【中】" in f]) * 1
                    bearish_score = len([f for f in analysis.bearish_factors if "【强】" in f]) * 3 + \
                                    len([f for f in analysis.bearish_factors if "【中】" in f]) * 1
                    score = bullish_score - bearish_score

                    # 只保留正分的股票（偏多）
                    if score > 0:
                        results.append({
                            "code": code,
                            "name": name,
                            "score": score,
                            "bullish_score": bullish_score,
                            "bearish_score": bearish_score,
                            "analysis": analysis,
                            "change_pct": stock.get("change_pct", 0)
                        })
        except:
            pass

        progress.progress((i + 1) / len(stocks))
        time.sleep(0.05)

    progress.empty()

    # 按评分排序，取前10
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:10]


def main():
    st.title("🏆 反转三兄弟 Top 10 推荐")
    st.caption("扫描市场活跃股票，推荐最符合反转三兄弟策略的股票")

    col1, col2 = st.columns(2)
    with col1:
        scan_btn = st.button("🔍 开始扫描市场", type="primary")
    with col2:
        st.caption("扫描约150只活跃股票，耗时约2-3分钟")

    st.divider()

    if scan_btn:
        top10 = scan_market_for_top10()

        if not top10:
            st.warning("未找到符合条件的股票")
            return

        st.success(f"扫描完成！找到 {len(top10)} 只推荐股票")

        # 一键添加按钮
        if st.button("📥 一键添加全部到自选股"):
            added = 0
            for item in top10:
                if not db.is_in_watchlist(item["code"]):
                    db.add_to_watchlist(item["code"], item["name"])
                    added += 1
            st.success(f"已添加 {added} 只新股票到自选股")

        st.divider()

        # 显示Top 10
        for rank, item in enumerate(top10, 1):
            analysis = item["analysis"]

            # 标题栏
            medal = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
            change_color = "red" if item["change_pct"] > 0 else ("green" if item["change_pct"] < 0 else "gray")

            with st.expander(
                f"{medal} **{item['code']}** {item['name']} | "
                f"评分: 多方{item['bullish_score']} vs 空方{item['bearish_score']} | "
                f"涨跌: {item['change_pct']:+.2f}%",
                expanded=(rank <= 3)
            ):
                # 添加到自选按钮
                col1, col2 = st.columns([4, 1])
                with col2:
                    if not db.is_in_watchlist(item["code"]):
                        if st.button("➕ 加自选", key=f"add_{item['code']}"):
                            db.add_to_watchlist(item["code"], item["name"])
                            st.success(f"已添加 {item['name']}")
                            st.rerun()
                    else:
                        st.write("✅ 已自选")

                # 详细分析
                render_stock_detail(analysis, show_add_button=False)

    else:
        # 显示说明
        st.markdown("""
        ### 扫描逻辑

        1. **获取活跃股票**: 按成交额排序，获取前150只活跃股票
        2. **逐只分析**: 对每只股票进行反转三兄弟策略分析
        3. **综合评分**: 计算多空因素得分（强信号3分，中信号1分）
        4. **排序推荐**: 按综合得分排序，推荐前10只

        ### 评分规则

        | 信号类型 | 分数 |
        |---------|------|
        | 【强】信号 | 3分 |
        | 【中】信号 | 1分 |

        **综合得分 = 多方得分 - 空方得分**

        ### 提示

        - 推荐的股票仅供参考，请结合自身判断
        - 建议关注评分差距大（多方远高于空方）的股票
        - 点击股票可展开查看详细分析
        """)


if __name__ == "__main__":
    main()
