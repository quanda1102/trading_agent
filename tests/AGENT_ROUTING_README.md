# Agent Routing System

This document explains the agent routing implementation that automatically selects between the Trading Agent and Conversational Agent based on user queries.

## Overview

The system uses regex pattern matching to detect the keyword "Phân tích" (analyze/analysis in Vietnamese) in user queries. When detected, the system routes to the Trading Agent for technical analysis; otherwise, it uses the Conversational Agent.

## Components

### 1. AgentRouter (`trading_agent_tp/core/agent_router.py`)

The main routing logic component with the following features:

#### Regex Pattern

```python
ANALYSIS_PATTERN = re.compile(
    r'\b(phân\s*tích|phan\s*tich)\b',
    re.IGNORECASE | re.UNICODE
)
```

**Pattern Explanation:**
- `\b` - Word boundary (ensures whole word matching)
- `phân\s*tích` - Matches "phân tích" with optional whitespace between words
- `phan\s*tich` - Matches "phan tich" (non-diacritical version)
- `\b` - Word boundary (end)
- `re.IGNORECASE` - Case-insensitive matching (matches "Phân tích", "phân tích", "PHÂN TÍCH")
- `re.UNICODE` - Unicode-aware matching (handles Vietnamese characters properly)

#### Key Methods

**`should_use_trading_agent(query: str) -> bool`**
- Determines if the trading agent should be used
- Returns `True` if the query contains "Phân tích", `False` otherwise

**`route(query: str) -> AgentType`**
- Routes the query to appropriate agent
- Returns either `"trading"` or `"conversational"`

**`get_agent_name(query: str) -> str`**
- Returns the agent name: `"TradingAgent"` or `"ConversationalAgent"`

### 2. AnalysisPatterns Class

Additional patterns for detecting specific types of analysis:

- `BASIC` - General "phân tích" pattern
- `TECHNICAL_ANALYSIS` - Technical analysis specific
- `ANALYSIS_REPORT` - Analysis report specific
- `MARKET_ANALYSIS` - Market analysis specific

**`detect_analysis_type(query: str) -> str`**
- Returns: `"technical"`, `"report"`, `"market"`, `"general"`, or `"none"`

### 3. API Integration (`trading_agent_tp/api/agent_endpoints.py`)

The routing is integrated into the `/api/v1/chat` endpoint:

```python
# Route to appropriate agent based on query content
agent_type = AgentRouter.route(request.question)
selected_agent = trading_agent if agent_type == "trading" else conversational_agent

# Run the selected agent
ai_response = await runner.run(selected_agent, agent_input)
```

The API response includes which agent was used:

```json
{
    "status": "success",
    "response": "...",
    "agent_used": "TradingAgent",
    "session_id": "...",
    "user_id": "...",
    "timestamp": "..."
}
```

## Usage Examples

### Queries that Route to Trading Agent

All these queries contain "Phân tích" and will use the Trading Agent:

1. `"Phân tích BTC"`
2. `"phân tích báo cáo kỹ thuật"`
3. `"PHÂN TÍCH thị trường"`
4. `"Tôi muốn phân tích giá Bitcoin"`
5. `"Hãy phân tích cho tôi biểu đồ này"`
6. `"phan tich BTC"` (without diacritics)

### Queries that Route to Conversational Agent

These queries don't contain "Phân tích" and will use the Conversational Agent:

1. `"Giá Bitcoin hiện tại là bao nhiêu?"`
2. `"Xu hướng thị trường như thế nào?"`
3. `"Tôi muốn biết về BTC"`
4. `"Cho tôi thông tin về crypto"`
5. `"Hôm nay thị trường ra sao?"`

## Testing

Run the test script to verify the routing behavior:

```bash
python test_agent_router.py
```

The test script includes:
- Agent routing tests
- Analysis pattern detection tests
- Direct regex pattern tests

## API Request Example

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "session_id": "session456",
    "question": "Phân tích BTC"
  }'
```

**Response:**
```json
{
  "status": "success",
  "response": "...(technical analysis)...",
  "agent_used": "TradingAgent",
  "session_id": "session456",
  "user_id": "user123",
  "timestamp": "2025-10-21T17:30:00.000000+00:00"
}
```

## Pattern Matching Details

### What Matches

The pattern is designed to be flexible and catch various forms:

| Input | Matches? | Reason |
|-------|----------|--------|
| `"Phân tích BTC"` | ✓ | Exact match |
| `"phân tích"` | ✓ | Case insensitive |
| `"PHÂN TÍCH"` | ✓ | Case insensitive |
| `"Phân  tích"` | ✓ | Allows spaces |
| `"phan tich"` | ✓ | Non-diacritical |
| `"Tôi muốn phân tích"` | ✓ | Word boundary matching |
| `"phântích"` | ✗ | No space between words |
| `"Giá Bitcoin"` | ✗ | Doesn't contain keyword |

### Word Boundary Matching

The `\b` word boundary ensures:
- Won't match partial words containing these characters
- Matches the keyword at the beginning, middle, or end of sentences
- Works correctly with Vietnamese text

## Extending the Router

### Adding New Keywords

To add more keywords that should route to the Trading Agent:

```python
ANALYSIS_PATTERN = re.compile(
    r'\b(phân\s*tích|phan\s*tich|new_keyword)\b',
    re.IGNORECASE | re.UNICODE
)
```

### Adding More Agent Types

To support more than two agents:

1. Update the `AgentType` literal in `agent_router.py`
2. Add new routing conditions in the `route()` method
3. Import and register the new agent in `agent_endpoints.py`
4. Update the selection logic in the chat endpoint

## Files Modified/Created

1. **Created:** `trading_agent_tp/core/agent_router.py` - Main routing logic
2. **Modified:** `trading_agent_tp/api/agent_endpoints.py` - API integration
3. **Created:** `test_agent_router.py` - Test suite
4. **Created:** `AGENT_ROUTING_README.md` - This documentation

## Technical Notes

### Import Handling

The trading agent file uses a hyphenated name (`trading-agent.py`), which requires special import handling:

```python
from importlib import import_module

trading_agent_module = import_module('trading_agent_tp.core.trading-agent')
trading_agent = trading_agent_module.agent
```

### Performance

- Regex compilation happens once at module load time
- Pattern matching is O(n) where n is the query length
- Very fast for typical query sizes (< 1ms)

### Unicode Support

The `re.UNICODE` flag ensures proper handling of:
- Vietnamese diacritical marks (ă, â, ê, ô, ơ, ư, etc.)
- Tone marks (à, á, ả, ã, ạ, etc.)
- Mixed language queries

## Future Enhancements

Potential improvements:

1. **Multi-language support** - Add English "analysis", "analyze" patterns
2. **Intent classification** - Use ML model for more sophisticated routing
3. **Context-aware routing** - Consider conversation history
4. **Confidence scoring** - Return confidence level with routing decision
5. **A/B testing** - Compare routing strategies
6. **Logging** - Add detailed routing decision logs for analysis

## Troubleshooting

### Issue: Agent not routing correctly

**Check:**
1. Verify the query contains "phân tích" or "phan tich"
2. Check for typos or unusual spacing
3. Run `test_agent_router.py` to verify pattern matching

### Issue: Import error for trading_agent

**Solution:**
Ensure the file `trading_agent_tp/core/trading-agent.py` exists and the import uses `importlib`

### Issue: Pattern not matching Vietnamese text

**Solution:**
Verify the regex uses `re.UNICODE` flag for proper Vietnamese character handling