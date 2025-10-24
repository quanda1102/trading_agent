"""
Enhanced Database Tool with Time-Horizon Awareness

This tool provides intelligent data retrieval based on trading time horizons:
- Short-term: < 3 weeks (uses crypto_kline_hours - 1h/4h data)
- Medium-term: 3 weeks - 3 months (uses crypto_kline_days - daily data)
- Long-term: 3-6 months (uses crypto_kline_weeks - weekly data)
- Very long-term: > 6 months (uses crypto_kline_months - monthly data)

Automatically selects the appropriate table and time interval based on the analysis horizon.
"""

import mysql.connector
from mysql.connector import Error
from typing import Dict, Any, List, Optional, Literal
import os
import json
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


TimeHorizon = Literal["short", "medium", "long", "very_long"]


class TimeHorizonConfig:
    """Configuration for different time horizons."""

    SHORT_TERM = {
        "horizon": "short",
        "description": "< 3 weeks",
        "table": "crypto_kline_hours",
        "interval": "1h",
        "max_days": 21,
        "default_limit": 168,  # 1 week of hourly data
        "indicators": ["RSI(14)", "MACD(12,26,9)", "EMA(20,50)", "Bollinger(20,2)"],
        "news_relevance_days": 3,  # Only news from last 3 days is relevant
    }

    MEDIUM_TERM = {
        "horizon": "medium",
        "description": "3 weeks - 3 months",
        "table": "crypto_kline_days",
        "interval": "1d",
        "max_days": 90,
        "default_limit": 30,  # 30 days
        "indicators": ["RSI(14)", "MACD(12,26,9)", "SMA(20,50,200)", "Bollinger(20,2)", "Volume Profile"],
        "news_relevance_days": 14,  # News from last 2 weeks
    }

    LONG_TERM = {
        "horizon": "long",
        "description": "3-6 months",
        "table": "crypto_kline_weeks",
        "interval": "1w",
        "max_days": 180,
        "default_limit": 26,  # 26 weeks (~6 months)
        "indicators": ["SMA(50,200)", "MACD(12,26,9)", "200-week MA", "Fibonacci Retracements"],
        "news_relevance_days": 30,  # News from last month
    }

    VERY_LONG_TERM = {
        "horizon": "very_long",
        "description": "> 6 months",
        "table": "crypto_kline_months",
        "interval": "1M",
        "max_days": 730,  # 2 years
        "default_limit": 24,  # 24 months
        "indicators": ["SMA(12,24)", "Market Cycles", "Long-term Trends"],
        "news_relevance_days": 90,  # News from last 3 months
    }

    @classmethod
    def get_config(cls, horizon: TimeHorizon) -> Dict[str, Any]:
        """Get configuration for a specific time horizon."""
        configs = {
            "short": cls.SHORT_TERM,
            "medium": cls.MEDIUM_TERM,
            "long": cls.LONG_TERM,
            "very_long": cls.VERY_LONG_TERM,
        }
        return configs.get(horizon, cls.MEDIUM_TERM)

    @classmethod
    def auto_detect_horizon(cls, query: str) -> TimeHorizon:
        """Auto-detect time horizon from query text."""
        query_lower = query.lower()

        # Short-term keywords
        short_keywords = ["short", "ngắn hạn", "scalp", "day trade", "intraday", "hourly", "4h", "1h"]
        if any(kw in query_lower for kw in short_keywords):
            return "short"

        # Long-term keywords
        long_keywords = ["long", "dài hạn", "weekly", "tuần", "tháng", "month", "invest", "hold"]
        if any(kw in query_lower for kw in long_keywords):
            return "long"

        # Very long-term keywords
        very_long_keywords = ["very long", "rất dài", "yearly", "năm", "cycle", "chu kỳ"]
        if any(kw in query_lower for kw in very_long_keywords):
            return "very_long"

        # Default to medium-term
        return "medium"


class EnhancedDatabaseTool:
    """Enhanced database tool with time-horizon awareness."""

    def __init__(self):
        self.connection = None
        self._connect()

    def _connect(self):
        """Connect to MySQL database."""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST"),
                user=os.getenv("MYSQL_USER"),
                password=os.getenv("MYSQL_PASSWORD"),
                database=os.getenv("MYSQL_DATABASE", "finance_services")
            )
            if self.connection.is_connected():
                print("✅ Connected to MySQL database (Enhanced)")
        except Error as e:
            print(f"❌ MySQL Error: {e}")
            self.connection = None

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        if not self.connection or not self.connection.is_connected():
            self._connect()

        if not self.connection:
            return []

        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()

            # Convert datetime objects to strings for JSON serialization
            for row in results:
                for key, value in row.items():
                    if isinstance(value, datetime):
                        row[key] = value.isoformat()

            return results
        except Error as e:
            print(f"❌ Query Error: {e}")
            return []

    def get_data_by_horizon(
        self,
        symbol: str,
        horizon: TimeHorizon = "medium",
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get cryptocurrency data for a specific time horizon.

        Args:
            symbol: Cryptocurrency symbol (btc, eth, etc.)
            horizon: Time horizon (short, medium, long, very_long)
            limit: Number of records to retrieve (uses default if None)

        Returns:
            Dict with data, metadata, and configuration info
        """
        config = TimeHorizonConfig.get_config(horizon)
        interval = config["interval"]
        query: str
        table: str

        if horizon == "short":
            table = "crypto_kline_hours"
            query = f"""
            SELECT
                id, symbol, `interval`,
                open_price, high_price, low_price, close_price,
                volume, quote_volume, trade_count,
                taker_buy_base_volume, taker_buy_quote_volume,
                open_time, close_time, updated_at
            FROM finance_services.crypto_kline_hours
            WHERE symbol = '{symbol.lower()}'
              AND `interval` IN ('1h', '4h')
              AND DATE(open_time) >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            ORDER BY close_time DESC
            """
        elif horizon == "medium":
            table = "crypto_kline_days"
            query = f"""
            SELECT
                id, symbol, `interval`,
                open_price, high_price, low_price, close_price,
                volume, quote_volume, trade_count,
                taker_buy_base_volume, taker_buy_quote_volume,
                open_time, close_time, updated_at
            FROM finance_services.crypto_kline_days
            WHERE symbol = '{symbol.lower()}'
              AND `interval` = '1d'
              AND DATE(open_time) >= DATE_SUB(NOW(), INTERVAL 1 YEAR)
            ORDER BY close_time DESC
            """
        elif horizon == "long":
            table = "crypto_kline_months + crypto_kline_weeks"
            query = f"""
            SELECT *
            FROM (
                SELECT
                    id, symbol, `interval`,
                    open_price, high_price, low_price, close_price,
                    volume, quote_volume, trade_count,
                    taker_buy_base_volume, taker_buy_quote_volume,
                    open_time, close_time, updated_at
                FROM finance_services.crypto_kline_months
                WHERE symbol = '{symbol.lower()}'
                  AND `interval` = '1M'

                UNION ALL

                SELECT
                    id, symbol, `interval`,
                    open_price, high_price, low_price, close_price,
                    volume, quote_volume, trade_count,
                    taker_buy_base_volume, taker_buy_quote_volume,
                    open_time, close_time, updated_at
                FROM finance_services.crypto_kline_weeks
                WHERE symbol = '{symbol.lower()}'
                  AND `interval` = '1w'
                  AND DATE(open_time) >= DATE_SUB(NOW(), INTERVAL 10 YEAR)
            ) AS merged_horizon
            ORDER BY close_time DESC
            """
        else:
            # Fallback to previous behaviour for very_long or unspecified horizons
            table = config["table"]
            query = f"""
            SELECT
                id, symbol, `interval`,
                open_price, high_price, low_price, close_price,
                volume, quote_volume, trade_count,
                taker_buy_base_volume, taker_buy_quote_volume,
                open_time, close_time, updated_at
            FROM finance_services.{table}
            WHERE symbol = '{symbol.lower()}'
              AND `interval` = '{interval}'
            ORDER BY close_time DESC
            """

        results = self.execute_query(query)

        if horizon == "short":
            timeframe_label = "1h & 4h (last 30 days)"
        elif horizon == "medium":
            timeframe_label = "1d (last 1 year)"
        elif horizon == "long":
            timeframe_label = "1M & 1w (long horizon)"
        else:
            timeframe_label = interval

        return {
            "status": "success" if results else "no_data",
            "horizon": horizon,
            "config": config,
            "symbol": symbol.upper(),
            "interval": timeframe_label,
            "table_used": table,
            "record_count": len(results),
            "data": results,
            "metadata": {
                "horizon_description": config["description"],
                "recommended_indicators": config["indicators"],
                "news_relevance_days": config["news_relevance_days"],
                "timeframe": timeframe_label,
            }
        }

    def get_multi_horizon_data(
        self,
        symbol: str,
        horizons: List[TimeHorizon] = ["short", "medium", "long"]
    ) -> Dict[str, Any]:
        """
        Get data for multiple time horizons at once.

        This is useful for comprehensive multi-timeframe analysis.

        Args:
            symbol: Cryptocurrency symbol
            horizons: List of time horizons to retrieve

        Returns:
            Dict with data for each horizon
        """
        results = {}

        for horizon in horizons:
            results[horizon] = self.get_data_by_horizon(symbol, horizon)

        return {
            "status": "success",
            "symbol": symbol.upper(),
            "horizons_analyzed": horizons,
            "data": results,
            "metadata": {
                "total_records": sum(r["record_count"] for r in results.values()),
                "analysis_type": "multi_timeframe",
            }
        }

    def get_latest_prices_all_horizons(self, symbol: str) -> Dict[str, Any]:
        """Get latest price for all time horizons."""
        horizons: List[TimeHorizon] = ["short", "medium", "long", "very_long"]
        latest_prices = {}

        for horizon in horizons:
            data = self.get_data_by_horizon(symbol, horizon, limit=1)
            if data["data"]:
                latest = data["data"][0]
                latest_prices[horizon] = {
                    "close_price": latest["close_price"],
                    "close_time": latest["close_time"],
                    "interval": data["interval"],
                    "volume": latest["volume"],
                }

        return {
            "status": "success",
            "symbol": symbol.upper(),
            "latest_prices": latest_prices,
        }

    def get_statistics_by_horizon(
        self,
        symbol: str,
        horizon: TimeHorizon = "medium"
    ) -> Dict[str, Any]:
        """Get statistical summary for a specific time horizon."""
        config = TimeHorizonConfig.get_config(horizon)
        table = config["table"]
        interval = config["interval"]

        query = f"""
        SELECT
            COUNT(*) as record_count,
            MIN(low_price) as min_price,
            MAX(high_price) as max_price,
            AVG(close_price) as avg_price,
            AVG(volume) as avg_volume,
            SUM(volume) as total_volume,
            MIN(open_time) as start_time,
            MAX(close_time) as end_time
        FROM finance_services.{table}
        WHERE symbol = '{symbol.lower()}'
        AND `interval` = '{interval}'
        """

        results = self.execute_query(query)

        if results:
            stats = results[0]
            # Calculate volatility
            if stats.get('min_price') and stats.get('max_price') and stats['min_price'] != 0:
                stats['volatility_pct'] = ((float(stats['max_price']) - float(stats['min_price'])) / float(stats['min_price'])) * 100

        return {
            "status": "success" if results else "no_data",
            "horizon": horizon,
            "symbol": symbol.upper(),
            "interval": interval,
            "statistics": results[0] if results else None,
            "config": config,
        }

    def close(self):
        """Close database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔒 MySQL connection closed")


# Global enhanced database tool instance
enhanced_db_tool = EnhancedDatabaseTool()


def get_enhanced_database_tool() -> EnhancedDatabaseTool:
    """Get the global enhanced database tool instance."""
    return enhanced_db_tool


def smart_query_with_horizon(query: str) -> str:
    """
    Execute a smart query that automatically detects time horizon.

    Args:
        query: Natural language query (e.g., "Get BTC data for short-term analysis")

    Returns:
        JSON string with results
    """
    try:
        # Extract symbol
        symbols = ['btc', 'eth', 'sol', 'bnb', 'xrp', 'ada', 'doge', 'avax', 'link', 'dot']
        symbol = None
        query_lower = query.lower()

        for sym in symbols:
            if sym in query_lower:
                symbol = sym
                break

        if not symbol:
            return json.dumps({
                "error": "symbol_not_found",
                "message": "Could not identify cryptocurrency symbol in query",
                "query": query,
                "supported_symbols": symbols,
            }, indent=2)

        # Auto-detect horizon
        horizon = TimeHorizonConfig.auto_detect_horizon(query)

        # Check if multi-horizon requested
        if "all" in query_lower or "multi" in query_lower or "tất cả" in query_lower:
            result = enhanced_db_tool.get_multi_horizon_data(symbol)
        else:
            result = enhanced_db_tool.get_data_by_horizon(symbol, horizon)

        return json.dumps(result, indent=2, default=str)

    except Exception as e:
        return json.dumps({
            "error": "execution_failed",
            "message": str(e),
            "query": query,
        }, indent=2)


def get_data_for_strategy(
    symbol: str,
    strategy_type: Literal["scalping", "day_trade", "swing_trade", "position_trade", "long_term_hold"]
) -> str:
    """
    Get data optimized for specific trading strategies.

    Strategy Mappings:
    - scalping: 1h data (very short-term, quick trades)
    - day_trade: 4h data (short-term, daily trades)
    - swing_trade: 1d data (medium-term, days to weeks)
    - position_trade: 1w data (long-term, weeks to months)
    - long_term_hold: 1M data (very long-term, months to years)

    Args:
        symbol: Cryptocurrency symbol
        strategy_type: Trading strategy type

    Returns:
        JSON string with appropriate data for the strategy
    """
    strategy_to_horizon: Dict[str, TimeHorizon] = {
        "scalping": "short",
        "day_trade": "short",
        "swing_trade": "medium",
        "position_trade": "long",
        "long_term_hold": "very_long",
    }

    horizon = strategy_to_horizon.get(strategy_type, "medium")

    try:
        result = enhanced_db_tool.get_data_by_horizon(symbol, horizon)
        result["strategy_type"] = strategy_type
        result["strategy_info"] = {
            "name": strategy_type,
            "typical_hold_time": {
                "scalping": "minutes to hours",
                "day_trade": "hours to 1 day",
                "swing_trade": "days to weeks",
                "position_trade": "weeks to months",
                "long_term_hold": "months to years",
            }[strategy_type],
            "recommended_indicators": result["config"]["indicators"],
        }

        return json.dumps(result, indent=2, default=str)

    except Exception as e:
        return json.dumps({
            "error": "execution_failed",
            "message": str(e),
            "symbol": symbol,
            "strategy_type": strategy_type,
        }, indent=2)


# Backward compatibility function for existing database tool interface
def execute_database_query(query: str, use_smart_sql: bool = True) -> str:
    """
    Execute a database query with smart horizon detection.

    This maintains backward compatibility while adding horizon awareness.

    Args:
        query: Natural language query
        use_smart_sql: If True, uses smart horizon detection

    Returns:
        JSON string with query results
    """
    if use_smart_sql:
        return smart_query_with_horizon(query)
    else:
        # Fallback to direct query
        try:
            results = enhanced_db_tool.execute_query(query)
            return json.dumps({
                "status": "success",
                "record_count": len(results),
                "data": results,
            }, indent=2, default=str)
        except Exception as e:
            return json.dumps({
                "error": "execution_failed",
                "message": str(e),
                "query": query,
            }, indent=2)
