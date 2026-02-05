"""
数据库模块 - SQLite数据模型
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json


class Database:
    """SQLite数据库管理器"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 自选股表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sort_order INTEGER DEFAULT 0,
                notes TEXT,
                buy_price REAL,
                buy_date TEXT,
                buy_quantity INTEGER
            )
        """)

        # 信号历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signal_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                pattern_name TEXT NOT NULL,
                strength REAL,
                price REAL,
                description TEXT,
                confirmations TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ETF自选表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS etf_watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sort_order INTEGER DEFAULT 0,
                notes TEXT
            )
        """)

        conn.commit()
        conn.close()

    # ============ 自选股管理 ============

    def add_to_watchlist(self, code: str, name: str, notes: str = "") -> bool:
        """添加股票到自选"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 获取当前最大排序值
            cursor.execute("SELECT MAX(sort_order) FROM watchlist")
            max_order = cursor.fetchone()[0] or 0

            cursor.execute(
                """
                INSERT OR REPLACE INTO watchlist (code, name, sort_order, notes)
                VALUES (?, ?, ?, ?)
                """,
                (code, name, max_order + 1, notes)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加自选股失败: {e}")
            return False

    def remove_from_watchlist(self, code: str) -> bool:
        """从自选中移除股票"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM watchlist WHERE code = ?", (code,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"移除自选股失败: {e}")
            return False

    def get_watchlist(self) -> List[Dict]:
        """获取自选股列表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT code, name, added_at, sort_order, notes
            FROM watchlist
            ORDER BY sort_order DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def is_in_watchlist(self, code: str) -> bool:
        """检查股票是否在自选中"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM watchlist WHERE code = ?", (code,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def update_watchlist_order(self, code: str, new_order: int) -> bool:
        """更新自选股排序"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE watchlist SET sort_order = ? WHERE code = ?",
                (new_order, code)
            )
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def update_buy_info(self, code: str, buy_price: float = None,
                        buy_date: str = None, buy_quantity: int = None) -> bool:
        """更新股票买入信息"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 先检查是否有这些列，如果没有则添加
            cursor.execute("PRAGMA table_info(watchlist)")
            columns = [row[1] for row in cursor.fetchall()]

            if "buy_price" not in columns:
                cursor.execute("ALTER TABLE watchlist ADD COLUMN buy_price REAL")
            if "buy_date" not in columns:
                cursor.execute("ALTER TABLE watchlist ADD COLUMN buy_date TEXT")
            if "buy_quantity" not in columns:
                cursor.execute("ALTER TABLE watchlist ADD COLUMN buy_quantity INTEGER")

            # 更新买入信息
            updates = []
            values = []

            if buy_price is not None:
                updates.append("buy_price = ?")
                values.append(buy_price)
            if buy_date is not None:
                updates.append("buy_date = ?")
                values.append(buy_date)
            if buy_quantity is not None:
                updates.append("buy_quantity = ?")
                values.append(buy_quantity)

            if updates:
                values.append(code)
                cursor.execute(
                    f"UPDATE watchlist SET {', '.join(updates)} WHERE code = ?",
                    values
                )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"更新买入信息失败: {e}")
            return False

    def get_buy_info(self, code: str) -> dict:
        """获取股票买入信息"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 检查列是否存在
            cursor.execute("PRAGMA table_info(watchlist)")
            columns = [row[1] for row in cursor.fetchall()]

            if "buy_price" not in columns:
                conn.close()
                return {"buy_price": None, "buy_date": None, "buy_quantity": None}

            cursor.execute(
                "SELECT buy_price, buy_date, buy_quantity FROM watchlist WHERE code = ?",
                (code,)
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    "buy_price": row[0],
                    "buy_date": row[1],
                    "buy_quantity": row[2]
                }
            return {"buy_price": None, "buy_date": None, "buy_quantity": None}
        except Exception as e:
            print(f"获取买入信息失败: {e}")
            return {"buy_price": None, "buy_date": None, "buy_quantity": None}

    # ============ 信号历史 ============

    def save_signal(self, signal_dict: Dict) -> bool:
        """保存信号到历史记录"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            confirmations = json.dumps(signal_dict.get("confirmations", []))

            cursor.execute(
                """
                INSERT INTO signal_history
                (code, name, signal_type, pattern_name, strength, price, description, confirmations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal_dict["code"],
                    signal_dict["name"],
                    signal_dict["signal_type"],
                    signal_dict["pattern_name"],
                    signal_dict["strength"],
                    signal_dict["price"],
                    signal_dict["description"],
                    confirmations
                )
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存信号失败: {e}")
            return False

    def get_signal_history(
        self,
        code: Optional[str] = None,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict]:
        """获取信号历史"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if code:
            cursor.execute(
                """
                SELECT * FROM signal_history
                WHERE code = ? AND detected_at >= datetime('now', ?)
                ORDER BY detected_at DESC
                LIMIT ?
                """,
                (code, f"-{days} days", limit)
            )
        else:
            cursor.execute(
                """
                SELECT * FROM signal_history
                WHERE detected_at >= datetime('now', ?)
                ORDER BY detected_at DESC
                LIMIT ?
                """,
                (f"-{days} days", limit)
            )

        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            d = dict(row)
            d["confirmations"] = json.loads(d.get("confirmations", "[]"))
            result.append(d)

        return result

    def get_today_signals(self, code: Optional[str] = None) -> List[Dict]:
        """获取今日信号"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if code:
            cursor.execute(
                """
                SELECT * FROM signal_history
                WHERE code = ? AND date(detected_at) = date('now')
                ORDER BY detected_at DESC
                """,
                (code,)
            )
        else:
            cursor.execute(
                """
                SELECT * FROM signal_history
                WHERE date(detected_at) = date('now')
                ORDER BY strength DESC
                """
            )

        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            d = dict(row)
            d["confirmations"] = json.loads(d.get("confirmations", "[]"))
            result.append(d)

        return result

    # ============ 配置管理 ============

    def get_setting(self, key: str, default: str = "") -> str:
        """获取配置项"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()

        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> bool:
        """设置配置项"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (key, value)
            )
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def get_all_settings(self) -> Dict[str, str]:
        """获取所有配置"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.fetchall()
        conn.close()

        return {row["key"]: row["value"] for row in rows}

    # ============ ETF自选管理 ============

    def add_to_etf_watchlist(self, code: str, name: str, notes: str = "") -> bool:
        """添加ETF到自选"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 获取当前最大排序值
            cursor.execute("SELECT MAX(sort_order) FROM etf_watchlist")
            max_order = cursor.fetchone()[0] or 0

            cursor.execute(
                """
                INSERT OR REPLACE INTO etf_watchlist (code, name, sort_order, notes)
                VALUES (?, ?, ?, ?)
                """,
                (code, name, max_order + 1, notes)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加ETF失败: {e}")
            return False

    def remove_from_etf_watchlist(self, code: str) -> bool:
        """从ETF自选中移除"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM etf_watchlist WHERE code = ?", (code,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"移除ETF失败: {e}")
            return False

    def get_etf_watchlist(self) -> List[Dict]:
        """获取ETF自选列表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT code, name, added_at, sort_order, notes
            FROM etf_watchlist
            ORDER BY sort_order DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def is_in_etf_watchlist(self, code: str) -> bool:
        """检查ETF是否在自选中"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM etf_watchlist WHERE code = ?", (code,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
