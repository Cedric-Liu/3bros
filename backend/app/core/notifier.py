"""
微信推送模块 - Server酱
"""
import requests
from typing import List, Optional
from datetime import datetime


class WeChatNotifier:
    """Server酱微信推送"""

    SERVERCHAN_URL = "https://sctapi.ftqq.com/{key}.send"

    def __init__(self, send_key: Optional[str] = None, db=None):
        """
        Args:
            send_key: Server酱的SendKey，如果不提供则从数据库读取
            db: Database实例，用于读取设置
        """
        self.db = db
        self._send_key = send_key

    @property
    def send_key(self) -> str:
        """获取SendKey"""
        if self._send_key:
            return self._send_key
        if self.db:
            return self.db.get_setting("serverchan_key", "")
        return ""

    @send_key.setter
    def send_key(self, value: str):
        """设置SendKey"""
        self._send_key = value
        if self.db:
            self.db.set_setting("serverchan_key", value)

    def is_configured(self) -> bool:
        """检查是否已配置"""
        return bool(self.send_key)

    def send_message(self, title: str, content: str = "") -> bool:
        """
        发送消息

        Args:
            title: 消息标题
            content: 消息内容 (支持Markdown)

        Returns:
            是否发送成功
        """
        if not self.is_configured():
            print("Server酱未配置")
            return False

        try:
            url = self.SERVERCHAN_URL.format(key=self.send_key)
            data = {
                "title": title,
                "desp": content
            }

            response = requests.post(url, data=data, timeout=10)
            result = response.json()

            if result.get("code") == 0:
                return True
            else:
                print(f"发送失败: {result.get('message', '未知错误')}")
                return False

        except Exception as e:
            print(f"发送消息异常: {e}")
            return False

    def send_test_message(self) -> bool:
        """发送测试消息"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.send_message(
            title="反转三兄弟 - 测试消息",
            content=f"这是一条测试消息\n\n发送时间: {now}\n\n如果您收到此消息，说明推送配置成功！"
        )

    def send_signals(self, signals: List[dict]) -> bool:
        """
        发送信号通知

        Args:
            signals: 信号列表

        Returns:
            是否发送成功
        """
        if not signals:
            return True

        # 分类信号
        buy_signals = [s for s in signals if s["signal_type"] == "买入"]
        sell_signals = [s for s in signals if s["signal_type"] == "卖出"]

        # 构建标题
        title = f"反转三兄弟信号 - {len(buy_signals)}买入/{len(sell_signals)}卖出"

        # 构建内容
        lines = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines.append(f"**检测时间**: {now}\n")

        if buy_signals:
            lines.append("## 🟢 买入信号\n")
            for s in buy_signals:
                confirmations = ", ".join(s.get("confirmations", []))
                lines.append(
                    f"- **{s['code']} {s['name']}** | {s['pattern_name']} | "
                    f"强度 {s['strength']:.0%}"
                )
                if confirmations:
                    lines.append(f"  - 确认: {confirmations}")
                lines.append(f"  - 价格: {s['price']:.2f}")
                lines.append("")

        if sell_signals:
            lines.append("## 🔴 卖出信号\n")
            for s in sell_signals:
                confirmations = ", ".join(s.get("confirmations", []))
                lines.append(
                    f"- **{s['code']} {s['name']}** | {s['pattern_name']} | "
                    f"强度 {s['strength']:.0%}"
                )
                if confirmations:
                    lines.append(f"  - 确认: {confirmations}")
                lines.append(f"  - 价格: {s['price']:.2f}")
                lines.append("")

        content = "\n".join(lines)

        return self.send_message(title, content)

    def send_daily_summary(
        self,
        watchlist_signals: List[dict],
        market_summary: str = ""
    ) -> bool:
        """
        发送每日汇总

        Args:
            watchlist_signals: 自选股信号
            market_summary: 大盘摘要

        Returns:
            是否发送成功
        """
        now = datetime.now().strftime("%Y-%m-%d")
        title = f"反转三兄弟 - {now} 每日汇总"

        lines = []

        if market_summary:
            lines.append("## 📊 大盘概况\n")
            lines.append(market_summary)
            lines.append("")

        if watchlist_signals:
            lines.append("## 🔔 自选股信号\n")
            for s in watchlist_signals:
                emoji = "🟢" if s["signal_type"] == "买入" else "🔴"
                lines.append(
                    f"{emoji} **{s['code']} {s['name']}** - {s['pattern_name']} "
                    f"(强度 {s['strength']:.0%})"
                )
            lines.append("")
        else:
            lines.append("## 🔔 自选股信号\n")
            lines.append("今日无信号\n")

        content = "\n".join(lines)

        return self.send_message(title, content)
