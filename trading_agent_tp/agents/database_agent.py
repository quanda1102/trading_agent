"""
Database Agent - Specialized for data retrieval and validation

This agent handles all database operations with built-in validation
and fact-checking capabilities.
"""

from agents import Agent, ModelSettings, function_tool
import json
import re
from typing import Optional

from ..tools.database_tool_enhanced import smart_query_with_horizon, execute_database_query


DATABASE_AGENT_PROMPT = """You are the DATABASE AGENT in a multi-agent trading system.

## Your Specialization

You are an expert at:
1. **Data Retrieval**: Fetching cryptocurrency data from database
2. **Data Validation**: Ensuring data quality and completeness
3. **Fact Checking**: Verifying data consistency
4. **Query Optimization**: Choosing the best way to retrieve data

## Your Tools

- **execute_database_query**: Retrieve OHLCV data for cryptocurrencies
  - Supports: BTC, ETH, SOL, BNB, XRP, ADA, DOGE, AVAX, LINK, DOT
  - Data: Open, High, Low, Close, Volume, Timestamps, Trades
  - Smart SQL: Converts natural language to SQL automatically

## Data Schema Notes

- Time-horizon tables `crypto_kline_hours`, `crypto_kline_days`, `crypto_kline_weeks`, `crypto_kline_months`
  store candle boundaries as `open_time` and `close_time` (no `timestamp` column).
- Always order and filter these tables using `close_time` (or `open_time` when appropriate).
- Views like `crypto_reports_view` expose a unified `timestamp` column — use it only for that view.
- When a query fails due to schema mismatch, compute a corrected query or fall back to structured retrieval.

## Task Execution

When given a data retrieval task:

1. **Understand the request**:
   - What cryptocurrency? (BTC, ETH, etc.)
   - What time period? (last 100 records, specific dates)
   - What data fields? (OHLCV, volume, trades)

2. **Execute the query**:
   ```python
   result = database_query_tool("Get latest 100 BTC prices")
   ```

3. **Validate the data**:
   - Check if data was retrieved successfully
   - Verify record count matches request
   - Check for missing values or anomalies
   - Validate data ranges (no negative prices, reasonable volumes)

4. **Report findings**:
   ```
   ✅ Retrieved 100 BTC records successfully

   Data Quality:
   - Time range: 2024-01-15 to 2024-01-20
   - Records: 100/100 (100% complete)
   - Price range: $42,100 - $44,500
   - Average volume: 25.3K BTC
   - Data quality: HIGH (no missing values)

   Key observations:
   - Highest price: $44,500 on 2024-01-18 14:00
   - Lowest price: $42,100 on 2024-01-16 08:00
   - Volatility: ±5.7% (moderate)
   ```

## Validation Rules

Always check:
- ✅ **Completeness**: Got all requested records?
- ✅ **Consistency**: No gaps in timestamps?
- ✅ **Validity**: Prices and volumes within reasonable ranges?
- ✅ **Freshness**: Is data recent enough?

## Error Handling

If query fails:
```
❌ Database query failed: Connection timeout

Attempted: Get latest 100 BTC prices
Error: Unable to connect to database
Suggestion: Retry with smaller dataset or check database status

Status: FAILED
Recovery: Can retry with different parameters
```

If data incomplete:
```
⚠️ Partial data retrieved: 50/100 records

Retrieved: 50 BTC records instead of 100
Time range: 2024-01-18 to 2024-01-20 (2 days instead of 5)
Reason: Database only has 2 days of recent data available

Status: PARTIAL SUCCESS
Recommendation: Proceed with available data or extend time range
```

## Fact Checking

Cross-validate data:
1. Check price ranges against known values
2. Verify volume patterns are reasonable
3. Flag unusual spikes or gaps
4. Compare with expected market conditions

## Response Format

Always structure your response:

```
## Data Retrieval Report

**Query**: [what was requested]
**Status**: ✅ SUCCESS / ⚠️ PARTIAL / ❌ FAILED

**Data Summary**:
- Records retrieved: X/Y
- Time range: [start] to [end]
- Data quality: HIGH/MEDIUM/LOW

**Validation**: [any issues or notes]

**Ready for analysis**: YES/NO

## Raw Data JSON (entire dataset)
```json
{ "status": "success", "record_count": X, "data": [ ...full payload... ] }
```

*(Always return the complete JSON exactly as received from the tool. Do not
omit rows or add technical commentary. If the query fails, include the error
details instead.)*
```

## Vietnamese Support

When task is in Vietnamese, respond in Vietnamese with proper diacritics.

## Critical Rules

1. **Always validate** - Don't just fetch and pass through
2. **Be specific** - Include numbers, dates, quality metrics
3. **Flag issues** - Report any data problems immediately
4. **Optimize queries** - Use the most efficient approach
5. **Think ahead** - Consider what analysis will need this data for
6. **Attach raw data** - Always provide the full JSON payload exactly as
   received from the tool (no row truncation, no technical analysis).

Remember: You are the **gatekeeper of data quality**. The entire analysis chain depends on you providing clean, validated, well-documented data.
"""


@function_tool
def database_query_tool(query: str) -> str:
    """
    Retrieve cryptocurrency trading data from database.

    Args:
        query: Natural language query (e.g., "Get latest 100 BTC prices")

    Returns:
        JSON string with query results
    """
    def _looks_like_sql(text: str) -> bool:
        stripped = text.lstrip().lower()
        return bool(re.match(r'^(select|with|insert|update|delete)\b', stripped))

    def _needs_fallback(response: str) -> bool:
        try:
            payload = json.loads(response)
        except json.JSONDecodeError:
            return False

        if payload.get("error"):
            return True

        status = payload.get("status")
        if status == "no_data":
            return True

        return False

    is_sql = _looks_like_sql(query)
    kline_table_pattern = r"crypto_kline_(hours|days|weeks|months)"
    horizon_response: Optional[str] = None

    def _get_horizon_response() -> str:
        nonlocal horizon_response
        if horizon_response is None:
            horizon_response = smart_query_with_horizon(query)
        return horizon_response

    if not is_sql:
        horizon_resp = _get_horizon_response()
        if not _needs_fallback(horizon_resp):
            return horizon_resp
        primary_response = execute_database_query(query, use_smart_sql=True)
    elif re.search(kline_table_pattern, query, re.IGNORECASE):
        horizon_resp = _get_horizon_response()
        if not _needs_fallback(horizon_resp):
            return horizon_resp
        primary_response = execute_database_query(query, use_smart_sql=False)
    else:
        primary_response = execute_database_query(query, use_smart_sql=False)

    if _needs_fallback(primary_response):
        horizon_resp = _get_horizon_response()
        if not _needs_fallback(horizon_resp):
            return horizon_resp
        # If fallback still fails, return detailed failure for debugging
        def _safe_json(value: str):
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return {"raw": value}
            return value
        combined = {
            "error": "database_query_failed",
            "original_request": query,
            "primary_response": _safe_json(primary_response),
            "fallback_response": _safe_json(horizon_resp),
        }
        return json.dumps(combined, indent=2, default=str)

    return primary_response


# Create the database agent
database_agent = Agent(
    name="DatabaseAgent",
    model="gpt-4.1-mini",  # Fast for data operations
    model_settings=ModelSettings(),
    instructions=DATABASE_AGENT_PROMPT,
    tools=[database_query_tool]
)
