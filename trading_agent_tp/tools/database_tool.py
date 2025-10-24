"""
Database Tool

Provides database query capabilities for trading data retrieval.
"""

import mysql.connector
from mysql.connector import Error
from typing import Dict, Any, List, Optional, Union
import os
import json
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class DatabaseTool:
    """Database tool for querying trading data."""

    def __init__(self):
        self.connection = None
        self.last_error: Optional[str] = None
        self._connect()

    def _connect(self):
        """Connect to MySQL database."""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST"),
                user=os.getenv("MYSQL_USER"),
                password=os.getenv("MYSQL_PASSWORD"),
                database=os.getenv("MYSQL_DATABASE")
            )
            if self.connection.is_connected():
                print("✅ Connected to MySQL database")
            self.last_error = None
        except Error as e:
            print(f"❌ MySQL Error: {e}")
            self.connection = None
            self.last_error = str(e)

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        if not self.connection or not self.connection.is_connected():
            self._connect()

        if not self.connection:
            return []

        try:
            self.last_error = None
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
            self.last_error = str(e)
            return []

    def get_crypto_data(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get cryptocurrency data for a symbol."""
        query = f"""
        SELECT * FROM finance_services.crypto_reports_view
        WHERE symbol = '{symbol.upper()}'
        ORDER BY timestamp DESC
        LIMIT {limit}
        """
        return self.execute_query(query)

    def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest price data for a symbol."""
        query = f"""
        SELECT * FROM finance_services.crypto_reports_view
        WHERE symbol = '{symbol.upper()}'
        ORDER BY timestamp DESC
        LIMIT 1
        """
        results = self.execute_query(query)
        return results[0] if results else None

    def get_price_range(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get price data for a date range."""
        query = f"""
        SELECT * FROM finance_services.crypto_reports_view
        WHERE symbol = '{symbol.upper()}'
        AND timestamp >= DATE_SUB(NOW(), INTERVAL {days} DAY)
        ORDER BY timestamp ASC
        """
        return self.execute_query(query)

    def get_ohlcv_data(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get OHLCV (Open, High, Low, Close, Volume) data for a symbol."""
        query = f"""
        SELECT timestamp, open, high, low, close, volume, trades
        FROM finance_services.crypto_reports_view
        WHERE symbol = '{symbol.upper()}'
        ORDER BY timestamp DESC
        LIMIT {limit}
        """
        return self.execute_query(query)

    def get_price_statistics(self, symbol: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get statistical summary of price data for a symbol."""
        query = f"""
        SELECT
            COUNT(*) as record_count,
            MIN(low) as min_price,
            MAX(high) as max_price,
            AVG(close) as avg_price,
            AVG(volume) as avg_volume,
            SUM(volume) as total_volume,
            MIN(timestamp) as start_time,
            MAX(timestamp) as end_time
        FROM finance_services.crypto_reports_view
        WHERE symbol = '{symbol.upper()}'
        AND timestamp >= DATE_SUB(NOW(), INTERVAL {days} DAY)
        """
        results = self.execute_query(query)
        return results[0] if results else None

    def get_available_symbols(self) -> List[str]:
        """Get list of all available cryptocurrency symbols in the database."""
        query = """
        SELECT DISTINCT symbol
        FROM finance_services.crypto_reports_view
        ORDER BY symbol
        """
        results = self.execute_query(query)
        return [row['symbol'] for row in results]

    def get_data_range(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get the time range of available data for a symbol."""
        query = f"""
        SELECT
            MIN(timestamp) as earliest_data,
            MAX(timestamp) as latest_data,
            COUNT(*) as total_records
        FROM finance_services.crypto_reports_view
        WHERE symbol = '{symbol.upper()}'
        """
        results = self.execute_query(query)
        return results[0] if results else None

    def close(self):
        """Close database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔒 MySQL connection closed")


# Global database tool instance
database_tool = DatabaseTool()


def get_database_tool() -> DatabaseTool:
    """Get the global database tool instance."""
    return database_tool


def natural_language_to_sql(query: str) -> Optional[str]:
    """
    Convert natural language query to SQL.

    Supported patterns:
    - "Get latest N [SYMBOL] prices"
    - "Get [SYMBOL] data for last N days"
    - "Get OHLCV data for [SYMBOL]"
    - "Get price statistics for [SYMBOL]"
    """
    query_lower = query.lower()

    # Extract symbol
    symbols = ['btc', 'eth', 'sol', 'bnb', 'xrp', 'ada', 'doge', 'avax', 'link', 'dot']
    symbol = None
    for sym in symbols:
        if sym in query_lower:
            symbol = sym.upper()
            break

    if not symbol:
        return None

    # Pattern: "latest N records"
    latest_match = re.search(r'latest\s+(\d+)', query_lower)
    if latest_match:
        limit = int(latest_match.group(1))
        return f"""
        SELECT * FROM finance_services.crypto_reports_view
        WHERE symbol = '{symbol}'
        ORDER BY timestamp DESC
        LIMIT {limit}
        """

    # Pattern: "last N days"
    days_match = re.search(r'last\s+(\d+)\s+days?', query_lower)
    if days_match:
        days = int(days_match.group(1))
        return f"""
        SELECT * FROM finance_services.crypto_reports_view
        WHERE symbol = '{symbol}'
        AND timestamp >= DATE_SUB(NOW(), INTERVAL {days} DAY)
        ORDER BY timestamp ASC
        """

    # Pattern: "OHLCV"
    if 'ohlcv' in query_lower:
        limit_match = re.search(r'(\d+)', query_lower)
        limit = int(limit_match.group(1)) if limit_match else 100
        return f"""
        SELECT timestamp, open, high, low, close, volume, trades
        FROM finance_services.crypto_reports_view
        WHERE symbol = '{symbol}'
        ORDER BY timestamp DESC
        LIMIT {limit}
        """

    # Pattern: "statistics"
    if 'statistic' in query_lower or 'summary' in query_lower:
        days_match = re.search(r'(\d+)\s+days?', query_lower)
        days = int(days_match.group(1)) if days_match else 30
        return f"""
        SELECT
            COUNT(*) as record_count,
            MIN(low) as min_price,
            MAX(high) as max_price,
            AVG(close) as avg_price,
            AVG(volume) as avg_volume,
            SUM(volume) as total_volume,
            MIN(timestamp) as start_time,
            MAX(timestamp) as end_time
        FROM finance_services.crypto_reports_view
        WHERE symbol = '{symbol}'
        AND timestamp >= DATE_SUB(NOW(), INTERVAL {days} DAY)
        """

    # Default: latest 100 records
    return f"""
    SELECT * FROM finance_services.crypto_reports_view
    WHERE symbol = '{symbol}'
    ORDER BY timestamp DESC
    LIMIT 100
    """


def execute_database_query(query: str, use_smart_sql: bool = False) -> str:
    """
    Execute a database query and return results as JSON string.

    Args:
        query: SQL query or natural language query (if use_smart_sql=True)
        use_smart_sql: If True, converts natural language to SQL first

    Returns:
        JSON string with query results or error message
    """
    try:
        if use_smart_sql:
            sql_query = natural_language_to_sql(query)
            if not sql_query:
                return json.dumps({
                    "error": "Could not parse query",
                    "message": f"Unable to convert '{query}' to SQL",
                    "suggestion": "Try: 'Get latest 100 BTC prices' or 'Get BTC data for last 30 days'"
                }, indent=2)
        else:
            sql_query = query

        results = database_tool.execute_query(sql_query)

        if database_tool.last_error:
            return json.dumps({
                "error": "execution_failed",
                "message": database_tool.last_error,
                "query": sql_query
            }, indent=2)

        if not results:
            return json.dumps({
                "status": "no_data",
                "message": "Query executed successfully but returned no data",
                "record_count": 0
            }, indent=2)

        return json.dumps({
            "status": "success",
            "record_count": len(results),
            "data": results
        }, indent=2, default=str)

    except Exception as e:
        return json.dumps({
            "error": "execution_failed",
            "message": str(e),
            "query": query
        }, indent=2)


def get_crypto_price_data(symbol: str, limit: int = 100) -> str:
    """
    Get cryptocurrency price data for a symbol.

    Args:
        symbol: Cryptocurrency symbol (BTC, ETH, etc.)
        limit: Number of records to retrieve (default: 100)

    Returns:
        JSON string with price data
    """
    try:
        results = database_tool.get_crypto_data(symbol, limit)

        if not results:
            return json.dumps({
                "error": "no_data",
                "message": f"No data found for {symbol}",
                "symbol": symbol
            }, indent=2)

        return json.dumps({
            "status": "success",
            "symbol": symbol,
            "record_count": len(results),
            "data": results
        }, indent=2, default=str)

    except Exception as e:
        return json.dumps({
            "error": "execution_failed",
            "message": str(e),
            "symbol": symbol
        }, indent=2)


def get_latest_crypto_price(symbol: str) -> str:
    """
    Get the latest price for a cryptocurrency.

    Args:
        symbol: Cryptocurrency symbol (BTC, ETH, etc.)

    Returns:
        JSON string with latest price data
    """
    try:
        result = database_tool.get_latest_price(symbol)

        if not result:
            return json.dumps({
                "error": "no_data",
                "message": f"No data found for {symbol}",
                "symbol": symbol
            }, indent=2)

        return json.dumps({
            "status": "success",
            "symbol": symbol,
            "data": result
        }, indent=2, default=str)

    except Exception as e:
        return json.dumps({
            "error": "execution_failed",
            "message": str(e),
            "symbol": symbol
        }, indent=2)


def get_price_statistics(symbol: str, days: int = 30) -> str:
    """
    Get statistical summary of price data for a cryptocurrency.

    Args:
        symbol: Cryptocurrency symbol (BTC, ETH, etc.)
        days: Number of days to analyze (default: 30)

    Returns:
        JSON string with statistical summary
    """
    try:
        result = database_tool.get_price_statistics(symbol, days)

        if not result:
            return json.dumps({
                "error": "no_data",
                "message": f"No data found for {symbol}",
                "symbol": symbol
            }, indent=2)

        # Calculate additional statistics
        if result.get('min_price') and result.get('max_price'):
            result['volatility_pct'] = ((result['max_price'] - result['min_price']) / result['min_price']) * 100

        return json.dumps({
            "status": "success",
            "symbol": symbol,
            "period_days": days,
            "statistics": result
        }, indent=2, default=str)

    except Exception as e:
        return json.dumps({
            "error": "execution_failed",
            "message": str(e),
            "symbol": symbol
        }, indent=2)


def get_ohlcv_data(symbol: str, limit: int = 100) -> str:
    """
    Get OHLCV (Open, High, Low, Close, Volume) data for a cryptocurrency.

    Args:
        symbol: Cryptocurrency symbol (BTC, ETH, etc.)
        limit: Number of records to retrieve (default: 100)

    Returns:
        JSON string with OHLCV data
    """
    try:
        results = database_tool.get_ohlcv_data(symbol, limit)

        if not results:
            return json.dumps({
                "error": "no_data",
                "message": f"No OHLCV data found for {symbol}",
                "symbol": symbol
            }, indent=2)

        return json.dumps({
            "status": "success",
            "symbol": symbol,
            "record_count": len(results),
            "data": results
        }, indent=2, default=str)

    except Exception as e:
        return json.dumps({
            "error": "execution_failed",
            "message": str(e),
            "symbol": symbol
        }, indent=2)


def list_available_symbols() -> str:
    """
    Get list of all available cryptocurrency symbols in the database.

    Returns:
        JSON string with list of symbols
    """
    try:
        symbols = database_tool.get_available_symbols()

        return json.dumps({
            "status": "success",
            "count": len(symbols),
            "symbols": symbols
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "error": "execution_failed",
            "message": str(e)
        }, indent=2)


def get_data_availability(symbol: str) -> str:
    """
    Get the time range and count of available data for a symbol.

    Args:
        symbol: Cryptocurrency symbol (BTC, ETH, etc.)

    Returns:
        JSON string with data availability information
    """
    try:
        result = database_tool.get_data_range(symbol)

        if not result:
            return json.dumps({
                "error": "no_data",
                "message": f"No data found for {symbol}",
                "symbol": symbol
            }, indent=2)

        return json.dumps({
            "status": "success",
            "symbol": symbol,
            "availability": result
        }, indent=2, default=str)

    except Exception as e:
        return json.dumps({
            "error": "execution_failed",
            "message": str(e),
            "symbol": symbol
        }, indent=2)
