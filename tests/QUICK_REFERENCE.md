# Agent Routing - Quick Reference

## The Regex Pattern

```python
r'\b(phân\s*tích|phan\s*tich)\b'
```
**Flags:** `re.IGNORECASE | re.UNICODE`

## Usage in Code

```python
from trading_agent_tp.core.agent_router import AgentRouter

# Check if should use trading agent
if AgentRouter.should_use_trading_agent(query):
    # Use trading agent
    pass

# Get agent type
agent_type = AgentRouter.route(query)  # Returns "trading" or "conversational"

# Get agent name
agent_name = AgentRouter.get_agent_name(query)  # Returns agent name string
```

## Matching Examples

| Query | Matches? | Agent |
|-------|----------|-------|
| `"Phân tích BTC"` | ✓ | TradingAgent |
| `"phân tích"` | ✓ | TradingAgent |
| `"phan tich"` | ✓ | TradingAgent |
| `"Giá Bitcoin?"` | ✗ | ConversationalAgent |

## API Response

```json
{
  "status": "success",
  "response": "...",
  "agent_used": "TradingAgent",  // ← Shows which agent was used
  "session_id": "...",
  "user_id": "...",
  "timestamp": "..."
}
```

## Testing

```bash
# Run all tests
uv run python test_agent_router.py

# Expected: All tests pass ✓
```

## Files

- **Router Logic:** `trading_agent_tp/core/agent_router.py`
- **API Integration:** `trading_agent_tp/api/agent_endpoints.py` (line 113-118)
- **Tests:** `test_agent_router.py`
- **Docs:** `AGENT_ROUTING_README.md`

## Pattern Details

- **Case Insensitive:** Matches uppercase/lowercase
- **Unicode Aware:** Handles Vietnamese diacritics
- **Flexible Spacing:** `\s*` allows optional whitespace
- **Word Boundaries:** `\b` ensures whole word matching
- **Alternative Form:** Also matches non-diacritical "phan tich"

## Common Queries

### Routes to Trading Agent ✓
- "Phân tích BTC"
- "Phân tích báo cáo kỹ thuật"
- "Tôi muốn phân tích thị trường"
- "Hãy phân tích cho tôi"

### Routes to Conversational Agent
- "Giá Bitcoin hiện tại?"
- "Xu hướng thị trường?"
- "Cho tôi thông tin về BTC"
- "Hôm nay thị trường ra sao?"