"""
数据获取模块 - 使用腾讯财经API
"""
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import streamlit as st
import json
import time


class DataFetcher:
    """A股数据获取器 - 使用腾讯财经API"""

    # 腾讯财经API
    TENCENT_KLINE_API = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    TENCENT_QUOTE_API = "https://qt.gtimg.cn/q="

    # 东方财富搜索API (仍然可用)
    EASTMONEY_SEARCH_API = "https://searchapi.eastmoney.com/api/suggest/get"
    EASTMONEY_LIST_API = "https://push2.eastmoney.com/api/qt/clist/get"

    @staticmethod
    def _get_tencent_symbol(symbol: str) -> str:
        """转换为腾讯格式的股票代码（支持股票和ETF）"""
        if symbol.startswith("6"):
            return f"sh{symbol}"  # 上海主板 + 科创板(688)
        elif symbol.startswith("5"):
            return f"sh{symbol}"  # 上海ETF (51xxxx, 56xxxx等)
        elif symbol.startswith("0") or symbol.startswith("3"):
            return f"sz{symbol}"  # 深圳主板 + 创业板
        elif symbol.startswith("1"):
            return f"sz{symbol}"  # 深圳ETF (159xxx)
        elif symbol.startswith("8") or symbol.startswith("4"):
            return f"bj{symbol}"  # 北交所
        else:
            return f"sh{symbol}"

    @staticmethod
    def _get_index_tencent_symbol(symbol: str) -> str:
        """转换指数代码为腾讯格式"""
        if symbol == "000001":
            return "sh000001"  # 上证指数
        elif symbol == "399001":
            return "sz399001"  # 深证成指
        elif symbol == "399006":
            return "sz399006"  # 创业板指
        elif symbol == "000688":
            return "sh000688"  # 科创50
        else:
            if symbol.startswith("000"):
                return f"sh{symbol}"
            else:
                return f"sz{symbol}"

    @staticmethod
    @st.cache_data(ttl=300)  # 缓存5分钟
    def get_stock_data(
        symbol: str,
        days: int = 60,
        adjust: str = "qfq"
    ) -> Optional[pd.DataFrame]:
        """
        获取个股日K线数据 - 使用腾讯财经API

        Args:
            symbol: 股票代码，如 "600519"
            days: 获取天数
            adjust: 复权类型，qfq前复权，hfq后复权

        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        try:
            tencent_symbol = DataFetcher._get_tencent_symbol(symbol)
            fq_type = "qfq" if adjust == "qfq" else ("hfq" if adjust == "hfq" else "day")

            params = {
                "param": f"{tencent_symbol},day,,,{days},{fq_type}"
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://gu.qq.com/"
            }

            response = requests.get(
                DataFetcher.TENCENT_KLINE_API,
                params=params,
                headers=headers,
                timeout=10
            )

            data = response.json()

            if not data.get("data"):
                return None

            stock_data = data["data"].get(tencent_symbol)
            if not stock_data:
                return None

            # 获取复权数据
            klines = stock_data.get(f"{fq_type}day") or stock_data.get("day")
            if not klines:
                return None

            # 解析数据: [日期, 开盘, 收盘, 最高, 最低, 成交量]
            records = []
            for kline in klines:
                records.append({
                    "date": kline[0],
                    "open": float(kline[1]),
                    "close": float(kline[2]),
                    "high": float(kline[3]),
                    "low": float(kline[4]),
                    "volume": float(kline[5]) if len(kline) > 5 else 0,
                    "amount": 0  # 腾讯API不提供成交额
                })

            df = pd.DataFrame(records)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)

            return df

        except Exception as e:
            st.error(f"获取股票 {symbol} 数据失败: {e}")
            return None

    @staticmethod
    @st.cache_data(ttl=300)
    def get_index_data(
        symbol: str,
        days: int = 60
    ) -> Optional[pd.DataFrame]:
        """
        获取指数日K线数据

        Args:
            symbol: 指数代码，如 "000001"(上证指数)
            days: 获取天数

        Returns:
            DataFrame
        """
        try:
            tencent_symbol = DataFetcher._get_index_tencent_symbol(symbol)

            params = {
                "param": f"{tencent_symbol},day,,,{days},"
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://gu.qq.com/"
            }

            response = requests.get(
                DataFetcher.TENCENT_KLINE_API,
                params=params,
                headers=headers,
                timeout=10
            )

            data = response.json()

            if not data.get("data"):
                return None

            stock_data = data["data"].get(tencent_symbol)
            if not stock_data:
                return None

            klines = stock_data.get("day")
            if not klines:
                return None

            records = []
            for kline in klines:
                records.append({
                    "date": kline[0],
                    "open": float(kline[1]),
                    "close": float(kline[2]),
                    "high": float(kline[3]),
                    "low": float(kline[4]),
                    "volume": float(kline[5]) if len(kline) > 5 else 0
                })

            df = pd.DataFrame(records)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)

            return df

        except Exception as e:
            st.error(f"获取指数 {symbol} 数据失败: {e}")
            return None

    @staticmethod
    @st.cache_data(ttl=3600)  # 缓存1小时
    def get_all_stocks() -> pd.DataFrame:
        """
        获取A股股票列表 - 使用东方财富板块成分股API

        Returns:
            DataFrame with columns: code, name
        """
        try:
            all_stocks = []
            seen_codes = set()

            # 获取多个板块的成分股
            boards = ["b:BK0500", "b:BK0701", "b:BK0804", "b:BK0600"]

            url = DataFetcher.EASTMONEY_LIST_API

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com/"
            }

            for board in boards:
                try:
                    params = {
                        "cb": "jQuery",
                        "fid": "f3",
                        "po": 1,
                        "pz": 500,
                        "pn": 1,
                        "np": 1,
                        "fltt": 2,
                        "invt": 2,
                        "ut": "b2884a393a59ad64002292a3e90d46a5",
                        "fs": board,
                        "fields": "f12,f14",
                        "_": int(datetime.now().timestamp() * 1000)
                    }

                    response = requests.get(url, params=params, headers=headers, timeout=15)
                    text = response.text

                    if "jQuery" in text:
                        text = text[text.index("(") + 1 : text.rindex(")")]
                        data = json.loads(text)

                        if data.get("rc") == 0 and data.get("data") and data["data"].get("diff"):
                            for item in data["data"]["diff"]:
                                code = item.get("f12", "")
                                name = item.get("f14", "")
                                if code and name and code not in seen_codes:
                                    all_stocks.append({
                                        "code": code,
                                        "name": name
                                    })
                                    seen_codes.add(code)

                    time.sleep(0.1)  # 避免请求太快
                except:
                    continue

            df = pd.DataFrame(all_stocks)
            return df

        except Exception as e:
            st.error(f"获取股票列表失败: {e}")
            return pd.DataFrame(columns=["code", "name"])

    @staticmethod
    @st.cache_data(ttl=60)  # 缓存1分钟
    def get_realtime_quote(symbol: str) -> Optional[Dict]:
        """
        获取个股实时行情 - 使用腾讯API

        Args:
            symbol: 股票代码

        Returns:
            dict with current price, change, etc.
        """
        try:
            tencent_symbol = DataFetcher._get_tencent_symbol(symbol)

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://gu.qq.com/"
            }

            response = requests.get(
                f"{DataFetcher.TENCENT_QUOTE_API}{tencent_symbol}",
                headers=headers,
                timeout=10
            )

            text = response.text

            # 解析腾讯行情数据
            # 格式: v_sh600519="1~贵州茅台~600519~1342.00~1337.00~1340.51~80166~..."
            if "=" not in text or '""' in text:
                return None

            data_str = text.split("=")[1].strip().strip('"')
            parts = data_str.split("~")

            if len(parts) < 35:
                return None

            return {
                "code": parts[2],
                "name": parts[1],
                "price": float(parts[3]) if parts[3] else 0,
                "prev_close": float(parts[4]) if parts[4] else 0,
                "open": float(parts[5]) if parts[5] else 0,
                "volume": float(parts[6]) * 100 if parts[6] else 0,  # 手转股
                "amount": float(parts[37]) * 10000 if len(parts) > 37 and parts[37] else 0,
                "high": float(parts[33]) if len(parts) > 33 and parts[33] else 0,
                "low": float(parts[34]) if len(parts) > 34 and parts[34] else 0,
                "change": float(parts[31]) if len(parts) > 31 and parts[31] else 0,
                "pct_change": float(parts[32]) if len(parts) > 32 and parts[32] else 0
            }

        except Exception as e:
            return None

    @staticmethod
    def search_stock(keyword: str, include_etf: bool = False) -> List[Dict]:
        """
        搜索股票 - 使用东方财富搜索建议API

        Args:
            keyword: 股票代码或名称关键字
            include_etf: 是否包含ETF

        Returns:
            list of dicts with code, name, type
        """
        try:
            params = {
                "input": keyword,
                "type": 14,
                "token": "D43BF722C8E33BDC906FB84D85E326E8",
                "count": 20
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com/"
            }

            response = requests.get(
                DataFetcher.EASTMONEY_SEARCH_API,
                params=params,
                headers=headers,
                timeout=10
            )
            data = response.json()

            results = []
            if data.get("QuotationCodeTable") and data["QuotationCodeTable"].get("Data"):
                for item in data["QuotationCodeTable"]["Data"]:
                    code = item.get("Code", "")
                    name = item.get("Name", "")
                    classify = item.get("Classify", "")
                    sec_type = item.get("SecurityType", "")

                    # A股: 1上海主板, 2深圳主板, 25科创板, 23创业板
                    if classify == "AStock" or sec_type in ("1", "2", "25", "23"):
                        results.append({
                            "code": code,
                            "name": name,
                            "type": "stock"
                        })
                    # ETF: 代码以5或159开头
                    elif include_etf and (code.startswith("5") or code.startswith("159")):
                        results.append({
                            "code": code,
                            "name": name,
                            "type": "etf"
                        })

            return results

        except Exception as e:
            return []

    @staticmethod
    def search_etf(keyword: str) -> List[Dict]:
        """
        搜索ETF

        Args:
            keyword: ETF代码或名称关键字

        Returns:
            list of dicts with code and name
        """
        try:
            params = {
                "input": keyword,
                "type": 14,
                "token": "D43BF722C8E33BDC906FB84D85E326E8",
                "count": 30
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com/"
            }

            response = requests.get(
                DataFetcher.EASTMONEY_SEARCH_API,
                params=params,
                headers=headers,
                timeout=10
            )
            data = response.json()

            results = []
            if data.get("QuotationCodeTable") and data["QuotationCodeTable"].get("Data"):
                for item in data["QuotationCodeTable"]["Data"]:
                    code = item.get("Code", "")
                    name = item.get("Name", "")
                    # ETF: 代码以5或159开头
                    if code.startswith("5") or code.startswith("159"):
                        results.append({
                            "code": code,
                            "name": name
                        })

            return results

        except Exception as e:
            return []

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_popular_etfs() -> List[Dict]:
        """获取热门ETF列表"""
        # 常见的宽基和行业ETF
        popular_etfs = [
            {"code": "510300", "name": "沪深300ETF", "category": "宽基"},
            {"code": "510500", "name": "中证500ETF", "category": "宽基"},
            {"code": "159915", "name": "创业板ETF", "category": "宽基"},
            {"code": "588000", "name": "科创50ETF", "category": "宽基"},
            {"code": "512010", "name": "医药ETF", "category": "行业"},
            {"code": "512880", "name": "证券ETF", "category": "行业"},
            {"code": "515790", "name": "光伏ETF", "category": "行业"},
            {"code": "512480", "name": "半导体ETF", "category": "行业"},
            {"code": "512690", "name": "酒ETF", "category": "行业"},
            {"code": "512800", "name": "银行ETF", "category": "行业"},
            {"code": "159869", "name": "游戏ETF", "category": "行业"},
            {"code": "516160", "name": "新能源车ETF", "category": "行业"},
            {"code": "512660", "name": "军工ETF", "category": "行业"},
            {"code": "159611", "name": "电力ETF", "category": "行业"},
            {"code": "512200", "name": "房地产ETF", "category": "行业"},
        ]
        return popular_etfs

    @staticmethod
    @st.cache_data(ttl=300)
    def get_etf_data(symbol: str, days: int = 60) -> Optional[pd.DataFrame]:
        """
        获取ETF日K线数据（与股票数据获取相同）
        """
        return DataFetcher.get_stock_data(symbol, days)

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_stock_name(symbol: str) -> str:
        """获取股票名称"""
        try:
            quote = DataFetcher.get_realtime_quote(symbol)
            if quote and quote.get("name"):
                return quote["name"]
            return symbol
        except:
            return symbol

    @staticmethod
    @st.cache_data(ttl=1800)
    def get_stocks_for_scan(limit: int = 200) -> List[Dict]:
        """
        获取用于扫描的股票列表（按成交额排序的活跃股票）

        Args:
            limit: 返回数量

        Returns:
            list of dicts with code, name, change_pct
        """
        try:
            url = DataFetcher.EASTMONEY_LIST_API

            params = {
                "cb": "jQuery",
                "fid": "f6",  # 按成交额排序
                "po": 1,  # 降序
                "pz": limit,
                "pn": 1,
                "np": 1,
                "fltt": 2,
                "invt": 2,
                "ut": "b2884a393a59ad64002292a3e90d46a5",
                "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",  # A股主板+创业板+科创板
                "fields": "f12,f14,f3,f6",  # 代码,名称,涨跌幅,成交额
                "_": int(datetime.now().timestamp() * 1000)
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com/"
            }

            response = requests.get(url, params=params, headers=headers, timeout=15)
            text = response.text

            if "jQuery" in text:
                text = text[text.index("(") + 1: text.rindex(")")]
                data = json.loads(text)

                if data.get("rc") == 0 and data.get("data") and data["data"].get("diff"):
                    stocks = []
                    for item in data["data"]["diff"]:
                        code = item.get("f12", "")
                        name = item.get("f14", "")
                        change_pct = item.get("f3", 0)

                        # 过滤ST股票和新股
                        if "ST" in name or "N" == name[0:1] or "C" == name[0:1]:
                            continue

                        stocks.append({
                            "code": code,
                            "name": name,
                            "change_pct": change_pct
                        })

                    return stocks

        except Exception as e:
            pass

        return []
