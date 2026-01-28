"""
设置页面
"""
import streamlit as st

from database.models import Database
from notify.wechat import WeChatNotifier

st.set_page_config(
    page_title="设置 - 反转三兄弟",
    page_icon="⚙️",
    layout="wide"
)

# 初始化
db = Database()
notifier = WeChatNotifier()


def main():
    st.title("⚙️ 设置")

    # ============ 微信推送设置 ============
    st.subheader("📱 微信推送设置")

    st.markdown("""
    使用 [Server酱](https://sct.ftqq.com/) 进行微信推送：
    1. 访问 [sct.ftqq.com](https://sct.ftqq.com/) 并登录
    2. 获取您的 **SendKey**
    3. 将 SendKey 填入下方
    """)

    current_key = db.get_setting("serverchan_key", "")

    # 显示当前状态
    if current_key:
        st.success("✅ 已配置 Server酱")
        st.text(f"当前Key: {current_key[:8]}...{current_key[-4:]}" if len(current_key) > 12 else "已设置")
    else:
        st.warning("⚠️ 尚未配置 Server酱")

    # 配置表单
    with st.form("serverchan_form"):
        new_key = st.text_input(
            "Server酱 SendKey",
            value="",
            placeholder="SCT...",
            type="password",
            help="从 sct.ftqq.com 获取的 SendKey"
        )

        col1, col2 = st.columns(2)

        with col1:
            submit = st.form_submit_button("💾 保存", use_container_width=True)

        with col2:
            test = st.form_submit_button("📤 发送测试", use_container_width=True)

        if submit and new_key:
            db.set_setting("serverchan_key", new_key)
            st.success("保存成功！")
            st.rerun()

        if test:
            if new_key:
                notifier._send_key = new_key
            if notifier.is_configured():
                with st.spinner("发送测试消息..."):
                    if notifier.send_test_message():
                        st.success("✅ 测试消息发送成功，请检查微信！")
                    else:
                        st.error("❌ 发送失败，请检查 SendKey 是否正确")
            else:
                st.error("请先填写 SendKey")

    st.divider()

    # ============ 推送时间设置 ============
    st.subheader("⏰ 推送时间设置")

    st.info("自动推送功能需要配合定时任务使用（如 cron）。这里设置的时间仅作为提醒。")

    current_push_time = db.get_setting("push_time", "15:30")

    push_time = st.time_input(
        "每日推送时间",
        value=None,
        help="建议设置在收盘后，如 15:30"
    )

    if st.button("保存推送时间"):
        if push_time:
            db.set_setting("push_time", push_time.strftime("%H:%M"))
            st.success(f"已保存，每日 {push_time.strftime('%H:%M')} 推送")

    st.divider()

    # ============ 信号检测参数 ============
    st.subheader("🎯 信号检测参数")

    st.caption("调整信号检测的敏感度（高级设置）")

    col1, col2 = st.columns(2)

    with col1:
        volume_threshold = st.slider(
            "放量阈值",
            min_value=1.0,
            max_value=3.0,
            value=float(db.get_setting("volume_threshold", "1.5")),
            step=0.1,
            help="成交量超过均量的倍数才算放量"
        )

        hammer_ratio = st.slider(
            "锤子线影线比例",
            min_value=1.5,
            max_value=3.0,
            value=float(db.get_setting("hammer_ratio", "2.0")),
            step=0.1,
            help="下影线长度/实体长度的最小比例"
        )

    with col2:
        engulfing_volume = st.slider(
            "吞没形态放量要求",
            min_value=1.0,
            max_value=2.0,
            value=float(db.get_setting("engulfing_volume", "1.2")),
            step=0.1,
            help="吞没形态时成交量的放大倍数要求"
        )

        doji_ratio = st.slider(
            "十字星实体比例",
            min_value=0.05,
            max_value=0.2,
            value=float(db.get_setting("doji_ratio", "0.1")),
            step=0.01,
            help="实体占振幅比例小于此值算十字星"
        )

    if st.button("保存参数设置"):
        db.set_setting("volume_threshold", str(volume_threshold))
        db.set_setting("hammer_ratio", str(hammer_ratio))
        db.set_setting("engulfing_volume", str(engulfing_volume))
        db.set_setting("doji_ratio", str(doji_ratio))
        st.success("参数已保存！")

    st.divider()

    # ============ 数据管理 ============
    st.subheader("🗄️ 数据管理")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🗑️ 清除缓存", use_container_width=True):
            st.cache_data.clear()
            st.success("缓存已清除")

    with col2:
        st.download_button(
            label="📥 导出自选股",
            data=export_watchlist(),
            file_name="watchlist.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col3:
        if st.button("📜 查看信号历史", use_container_width=True):
            history = db.get_signal_history(days=30)
            if history:
                st.dataframe(history, use_container_width=True)
            else:
                st.info("暂无历史记录")

    st.divider()

    # ============ 关于 ============
    st.subheader("ℹ️ 关于")

    st.markdown("""
    **反转三兄弟 A股监控系统**

    基于经典K线形态的A股买卖信号监控工具，帮助识别：
    - 阳吞阴 / 阴吞阳
    - 乌云盖顶 / 刺透形态
    - 锤子线 / 上吊线
    - 启明星 / 黄昏星
    - 十字星

    **技术栈**:
    - Streamlit
    - AKShare
    - Plotly
    - SQLite

    **免责声明**: 本工具仅供学习参考，不构成投资建议。股市有风险，投资需谨慎。
    """)


def export_watchlist() -> str:
    """导出自选股为CSV"""
    watchlist = db.get_watchlist()

    if not watchlist:
        return "code,name,added_at\n"

    lines = ["code,name,added_at"]
    for stock in watchlist:
        lines.append(f"{stock['code']},{stock['name']},{stock['added_at']}")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
