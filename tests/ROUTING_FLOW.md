# Agent Routing Flow Diagram

## Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Sends Query                           │
│                  POST /api/v1/chat                              │
│           {"question": "Phân tích BTC"}                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Agent Endpoints Handler                        │
│              (agent_endpoints.py:80)                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               AgentRouter.route(query)                          │
│              (agent_router.py:65)                               │
│                                                                 │
│   Regex Pattern: \b(phân\s*tích|phan\s*tich)\b                 │
│   Flags: IGNORECASE | UNICODE                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                ┌────────┴────────┐
                │                 │
                ▼                 ▼
    ┌───────────────────┐  ┌──────────────────┐
    │ Contains          │  │ Does NOT         │
    │ "Phân tích"?      │  │ contain          │
    │                   │  │ "Phân tích"?     │
    │ ✓ YES             │  │ ✗ NO             │
    └───────┬───────────┘  └────────┬─────────┘
            │                       │
            ▼                       ▼
    ┌───────────────────┐  ┌──────────────────┐
    │ Return "trading"  │  │ Return           │
    │                   │  │ "conversational" │
    └───────┬───────────┘  └────────┬─────────┘
            │                       │
            └───────────┬───────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              Select Agent Instance                              │
│      (agent_endpoints.py:114)                                   │
│                                                                 │
│  selected_agent = trading_agent if agent_type == "trading"     │
│                   else conversational_agent                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                ┌────────┴────────┐
                │                 │
                ▼                 ▼
    ┌───────────────────┐  ┌──────────────────┐
    │  Trading Agent    │  │ Conversational   │
    │                   │  │ Agent            │
    │  Model: gpt-5     │  │ Model: gpt-4.1   │
    │  with reasoning   │  │ -mini            │
    │                   │  │                  │
    │  Technical        │  │ General Q&A      │
    │  Analysis         │  │ Web Search       │
    │  Code Interpreter │  │ Code Interpreter │
    └───────┬───────────┘  └────────┬─────────┘
            │                       │
            └───────────┬───────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│            Run Selected Agent                                   │
│       (agent_endpoints.py:117)                                  │
│                                                                 │
│   ai_response = await runner.run(selected_agent, agent_input)  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Store Response in Memory                           │
│         (agent_endpoints.py:127)                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Return JSON Response                            │
│                                                                 │
│  {                                                              │
│    "status": "success",                                         │
│    "response": "...",                                           │
│    "agent_used": "TradingAgent",  ← Which agent was selected   │
│    "session_id": "...",                                         │
│    "user_id": "...",                                            │
│    "timestamp": "..."                                           │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Example Routing Decisions

### Example 1: Technical Analysis Request
```
Input:  "Phân tích BTC"
        ↓
Regex:  MATCH ✓ ("Phân tích" found)
        ↓
Route:  "trading"
        ↓
Agent:  TradingAgent
        ↓
Output: Technical analysis with charts, indicators, support/resistance levels
```

### Example 2: General Question
```
Input:  "Giá Bitcoin hiện tại là bao nhiêu?"
        ↓
Regex:  NO MATCH ✗ (no "Phân tích")
        ↓
Route:  "conversational"
        ↓
Agent:  ConversationalAgent
        ↓
Output: Current price with market context
```

## Pattern Matching Examples

```
┌─────────────────────────────┬─────────┬──────────────────┐
│ Query                       │ Match?  │ Agent Selected   │
├─────────────────────────────┼─────────┼──────────────────┤
│ "Phân tích BTC"             │ ✓ YES   │ TradingAgent     │
│ "phân tích btc"             │ ✓ YES   │ TradingAgent     │
│ "PHÂN TÍCH BTC"             │ ✓ YES   │ TradingAgent     │
│ "Phân tích báo cáo"         │ ✓ YES   │ TradingAgent     │
│ "phan tich BTC"             │ ✓ YES   │ TradingAgent     │
│ "Tôi muốn phân tích"        │ ✓ YES   │ TradingAgent     │
│ "Giá Bitcoin?"              │ ✗ NO    │ Conversational   │
│ "Xu hướng thị trường?"      │ ✗ NO    │ Conversational   │
│ "Cho tôi thông tin"         │ ✗ NO    │ Conversational   │
└─────────────────────────────┴─────────┴──────────────────┘
```

## Code Location Reference

```
trading-agent-tp/
│
├── trading_agent_tp/
│   ├── core/
│   │   ├── agent_router.py          ← Routing logic (line 13-78)
│   │   ├── trading-agent.py         ← Trading Agent definition
│   │   └── conversational_agent.py  ← Conversational Agent
│   │
│   └── api/
│       └── agent_endpoints.py       ← API integration (line 113-121)
│
├── test_agent_router.py             ← Test suite
└── AGENT_ROUTING_README.md          ← Full documentation
```

## Regex Pattern Breakdown

```
Pattern: \b(phân\s*tích|phan\s*tich)\b

┌─────────────────────────────────────────────────────────────┐
│  \b          │ Word boundary (start)                        │
│              │ Ensures we match whole words only            │
├──────────────┼──────────────────────────────────────────────┤
│  (           │ Start capture group                          │
├──────────────┼──────────────────────────────────────────────┤
│  phân        │ Literal text "phân" (with diacritics)        │
├──────────────┼──────────────────────────────────────────────┤
│  \s*         │ Zero or more whitespace characters           │
│              │ Allows "phân tích" or "phân  tích"           │
├──────────────┼──────────────────────────────────────────────┤
│  tích        │ Literal text "tích" (with diacritics)        │
├──────────────┼──────────────────────────────────────────────┤
│  |           │ OR operator                                  │
├──────────────┼──────────────────────────────────────────────┤
│  phan        │ Literal text "phan" (without diacritics)     │
├──────────────┼──────────────────────────────────────────────┤
│  \s*         │ Zero or more whitespace characters           │
├──────────────┼──────────────────────────────────────────────┤
│  tich        │ Literal text "tich" (without diacritics)     │
├──────────────┼──────────────────────────────────────────────┤
│  )           │ End capture group                            │
├──────────────┼──────────────────────────────────────────────┤
│  \b          │ Word boundary (end)                          │
└──────────────┴──────────────────────────────────────────────┘

Flags:
  - re.IGNORECASE  → Case insensitive (Phân/phân/PHÂN)
  - re.UNICODE     → Unicode-aware (Vietnamese characters)
```