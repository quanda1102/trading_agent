# Quick Integration Guide

## 🔄 Integrating Enhanced Components

This guide shows you how to integrate the enhanced time-horizon aware components into your existing system.

---

## Option 1: Full Replacement (Recommended)

### Step 1: Update Database Agent

**File**: `trading_agent_tp/agents/__init__.py`

```python
# OLD
from .database_agent import database_agent
# NEW
from .database_agent_enhanced import database_agent_enhanced as database_agent
```

Or create a new module:

**File**: `trading_agent_tp/agents/database_agent_enhanced.py`

```python
"""Enhanced Database Agent with time-horizon awareness."""

from agents import Agent, ModelSettings, function_tool
from ..tools.database_tool_enhanced import smart_query_with_horizon

DATABASE_AGENT_ENHANCED_PROMPT = """You are the ENHANCED DATABASE AGENT with TIME-HORIZON AWARENESS.

Your job:
1. Identify the time horizon from the task description (SHORT/MEDIUM/LONG-TERM)
2. Use the smart_query_with_horizon tool which automatically selects the correct table
3. Report the data source used and validate data quality

Examples:
- "Retrieve BTC data for short-term analysis" → Uses crypto_kline_hours (1h interval)
- "Get BTC long-term trend data" → Uses crypto_kline_weeks (1w interval)
- "Fetch BTC multi-timeframe data" → Returns data from multiple tables

Always report:
- Which table was used (hours/days/weeks/months)
- What interval (1h/4h/1d/1w/1M)
- Data quality (completeness, time range)
- Recommended indicators for this timeframe
"""

@function_tool
def database_query_enhanced(query: str) -> str:
    """
    Retrieve cryptocurrency data with automatic time-horizon detection.

    Args:
        query: Natural language query (e.g., "Get BTC short-term data")

    Returns:
        JSON string with data and metadata about source
    """
    return smart_query_with_horizon(query)

# Create enhanced database agent
database_agent_enhanced = Agent(
    name="EnhancedDatabaseAgent",
    model="gpt-4o-mini",
    model_settings=ModelSettings(),
    instructions=DATABASE_AGENT_ENHANCED_PROMPT,
    tools=[database_query_enhanced]
)
```

### Step 2: Update Multi-Agent Orchestrator

**File**: `trading_agent_tp/core/multi_agent_orchestrator.py`

```python
# Add imports at the top
from .planner_agent_enhanced import planner_agent_enhanced
from ..agents.database_agent_enhanced import database_agent_enhanced
from ..agents.analysis_agent_enhanced import analysis_agent_enhanced
from ..agents.research_agent_enhanced import research_agent_enhanced
from ..agents.report_agent_enhanced import report_agent_enhanced

class MultiAgentOrchestrator:
    def __init__(self, use_enhanced=True):
        """
        Initialize orchestrator.

        Args:
            use_enhanced: If True, use enhanced time-horizon aware agents
        """
        self.runner = Runner()
        self.shared_history: List[Dict[str, Any]] = []
        self.trace_events: List[Dict[str, Any]] = []
        self.max_cycles = self.DEFAULT_MAX_CYCLES

        if use_enhanced:
            # Use enhanced agents
            self.planner = planner_agent_enhanced
            self.agents = {
                "database": database_agent_enhanced,
                "analysis": analysis_agent_enhanced,
                "research": research_agent_enhanced,
                "report": report_agent_enhanced
            }
        else:
            # Use original agents (backward compatibility)
            from .planner import planner_agent
            from ..agents import database_agent, analysis_agent, research_agent, report_agent

            self.planner = planner_agent
            self.agents = {
                "database": database_agent,
                "analysis": analysis_agent,
                "research": research_agent,
                "report": report_agent
            }
```

### Step 3: Update Planning Phase

**File**: `trading_agent_tp/core/multi_agent_orchestrator.py`

In the `_planning_phase` method, replace the planner agent reference:

```python
async def _planning_phase(self, cycle_num: int) -> Dict[str, Any]:
    """Execute planning phase with enhanced planner."""
    planner_input = self._format_history_for_planner()

    # Use self.planner (which is now planner_agent_enhanced)
    planner_response = await self.runner.run(self.planner, planner_input)

    # Rest of the code remains the same
    ...
```

### Step 4: Test the Integration

Create a test file:

**File**: `tests/test_enhanced_system.py`

```python
"""Test enhanced multi-timeframe system."""

import asyncio
from trading_agent_tp.core.multi_agent_orchestrator import MultiAgentOrchestrator

async def test_short_term_analysis():
    """Test short-term analysis with enhanced agents."""
    orchestrator = MultiAgentOrchestrator(use_enhanced=True)

    query = "Phân tích BTC ngắn hạn cho trading hôm nay"
    result = await orchestrator.process_query(
        query=query,
        user_id="test_user",
        session_id="test_session"
    )

    print("\n" + "="*80)
    print("SHORT-TERM ANALYSIS RESULT")
    print("="*80)
    print(result["final_answer"])
    print("\n" + "="*80)
    print("EXECUTION LOG")
    print("="*80)
    for log in result["execution_log"]:
        print(f"{log['agent']}: {log['task'][:60]}...")

    assert result["success"], "Analysis should succeed"
    assert "4H" in result["final_answer"] or "1h" in result["final_answer"].lower(), \
        "Should mention short-term timeframe"

async def test_multi_timeframe_analysis():
    """Test multi-timeframe comprehensive analysis."""
    orchestrator = MultiAgentOrchestrator(use_enhanced=True)

    query = "Phân tích BTC toàn diện cả ngắn hạn, trung hạn và dài hạn"
    result = await orchestrator.process_query(
        query=query,
        user_id="test_user",
        session_id="test_session"
    )

    print("\n" + "="*80)
    print("MULTI-TIMEFRAME ANALYSIS RESULT")
    print("="*80)
    print(result["final_answer"])

    assert result["success"], "Analysis should succeed"
    # Should have data from multiple agents
    assert result["agent_results"]["database"] is not None
    assert result["agent_results"]["analysis"] is not None

async def test_long_term_investment():
    """Test long-term investment analysis."""
    orchestrator = MultiAgentOrchestrator(use_enhanced=True)

    query = "Phân tích xu hướng dài hạn BTC để đầu tư"
    result = await orchestrator.process_query(
        query=query,
        user_id="test_user",
        session_id="test_session"
    )

    print("\n" + "="*80)
    print("LONG-TERM INVESTMENT ANALYSIS")
    print("="*80)
    print(result["final_answer"])

    assert result["success"], "Analysis should succeed"
    assert "1W" in result["final_answer"] or "weekly" in result["final_answer"].lower(), \
        "Should mention long-term timeframe"

if __name__ == "__main__":
    print("🧪 Testing Enhanced Multi-Timeframe System\n")

    asyncio.run(test_short_term_analysis())
    print("\n" + "✅ Short-term test passed\n")

    asyncio.run(test_multi_timeframe_analysis())
    print("\n" + "✅ Multi-timeframe test passed\n")

    asyncio.run(test_long_term_investment())
    print("\n" + "✅ Long-term test passed\n")

    print("🎉 All tests passed!")
```

Run tests:
```bash
cd trading-agent-tp
python tests/test_enhanced_system.py
```

---

## Option 2: Side-by-Side (For Testing)

Keep both old and new systems:

### File Structure
```
trading_agent_tp/
├── agents/
│   ├── database_agent.py           # Original
│   ├── database_agent_enhanced.py  # Enhanced
│   ├── analysis_agent.py           # Original
│   ├── analysis_agent_enhanced.py  # Enhanced
│   ├── research_agent.py           # Original
│   ├── research_agent_enhanced.py  # Enhanced
│   ├── report_agent.py             # Original
│   └── report_agent_enhanced.py    # Enhanced
├── core/
│   ├── planner_agent.py            # Original
│   ├── planner_agent_enhanced.py   # Enhanced
│   ├── multi_agent_orchestrator.py # With use_enhanced flag
│   └── orchestrator.py             # Original simple orchestrator
└── tools/
    ├── database_tool.py            # Original
    └── database_tool_enhanced.py   # Enhanced
```

### API Endpoint Selection

**File**: `trading_agent_tp/api/multi_agent_endpoints.py`

```python
from fastapi import APIRouter, Query
from trading_agent_tp.core.multi_agent_orchestrator import MultiAgentOrchestrator

router = APIRouter()

@router.post("/analyze")
async def analyze_crypto(
    query: str,
    user_id: str,
    session_id: str,
    use_enhanced: bool = Query(True, description="Use enhanced time-horizon aware agents")
):
    """
    Analyze cryptocurrency with multi-agent system.

    Args:
        query: User's question (Vietnamese or English)
        user_id: User identifier
        session_id: Session identifier
        use_enhanced: If True, use enhanced agents with time-horizon awareness

    Returns:
        Analysis result with final answer and execution trace
    """
    orchestrator = MultiAgentOrchestrator(use_enhanced=use_enhanced)

    result = await orchestrator.process_query(
        query=query,
        user_id=user_id,
        session_id=session_id
    )

    return {
        "success": result["success"],
        "answer": result["final_answer"],
        "enhanced_mode": use_enhanced,
        "cycles_used": result["cycles_used"],
        "trace": result["trace"]
    }
```

Test both:
```bash
# Test enhanced system
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query": "Phân tích BTC ngắn hạn", "user_id": "test", "session_id": "test1", "use_enhanced": true}'

# Test original system
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query": "Phân tích BTC", "user_id": "test", "session_id": "test2", "use_enhanced": false}'
```

---

## Option 3: Gradual Migration

Migrate one component at a time:

### Week 1: Database Tool Only
```python
# Update only database agent to use enhanced tool
from ..tools.database_tool_enhanced import smart_query_with_horizon

@function_tool
def database_query_tool(query: str) -> str:
    return smart_query_with_horizon(query)
```

**Test**: Verify correct table selection for short/medium/long-term queries

### Week 2: Add Enhanced Planner
```python
# Switch to enhanced planner
from .planner_agent_enhanced import planner_agent_enhanced as planner_agent
```

**Test**: Verify planner creates tasks with specific table names

### Week 3: Add Enhanced Research
```python
# Switch to enhanced research agent
from ..agents.research_agent_enhanced import research_agent_enhanced as research_agent
```

**Test**: Verify relevance scoring and filtering

### Week 4: Add Enhanced Analysis
```python
# Switch to enhanced analysis agent
from ..agents.analysis_agent_enhanced import analysis_agent_enhanced as analysis_agent
```

**Test**: Verify timeframe-specific indicators

### Week 5: Add Enhanced Report
```python
# Switch to enhanced report agent
from ..agents.report_agent_enhanced import report_agent_enhanced as report_agent
```

**Test**: Verify Vietnamese format and multi-timeframe structure

---

## Verification Checklist

After integration, verify:

- [ ] **Database queries use correct tables**:
  - Short-term → crypto_kline_hours
  - Medium-term → crypto_kline_days
  - Long-term → crypto_kline_weeks

- [ ] **Planner creates time-aware tasks**:
  - Task descriptions mention specific tables
  - Indicator sets match timeframe
  - News recency requirements specified

- [ ] **Research filters by relevance**:
  - Old news excluded for short-term
  - Relevance scores visible in output
  - Sentiment calculation uses only relevant news

- [ ] **Analysis uses correct indicators**:
  - Short-term: RSI, MACD, EMA, Bollinger
  - Medium-term: SMA, MACD divergence, Volume Profile
  - Long-term: 200W MA, cycle patterns

- [ ] **Report follows Vietnamese format**:
  - Multiple timeframe sections
  - Probability-based scenarios
  - Specific entry/TP/SL
  - Summary table included

---

## Troubleshooting Integration

### Issue: Import errors

**Error**: `ModuleNotFoundError: No module named 'trading_agent_tp.tools.database_tool_enhanced'`

**Fix**:
```python
# Ensure files are in correct locations
trading_agent_tp/
├── tools/
│   └── database_tool_enhanced.py  # ✅ Must exist here
```

### Issue: Planner still using old agent

**Error**: Tasks don't mention specific tables

**Fix**:
```python
# In multi_agent_orchestrator.py __init__
self.planner = planner_agent_enhanced  # ✅ Not planner_agent

# Also update in _planning_phase method
planner_response = await self.runner.run(self.planner, planner_input)
```

### Issue: Database tool not found

**Error**: `NameError: name 'smart_query_with_horizon' is not defined`

**Fix**:
```python
# In database_agent_enhanced.py
from ..tools.database_tool_enhanced import smart_query_with_horizon  # ✅ Correct import path
```

### Issue: Agents not registered

**Error**: `KeyError: 'database'` in orchestrator

**Fix**:
```python
# In multi_agent_orchestrator.py __init__
self.agents = {
    "database": database_agent_enhanced,  # ✅ Must be set
    "analysis": analysis_agent_enhanced,
    "research": research_agent_enhanced,
    "report": report_agent_enhanced
}
```

---

## Performance Considerations

### Database Queries

Enhanced system may make more queries (multi-timeframe):
```python
# Before: 1 query
SELECT * FROM crypto_reports_view LIMIT 100

# After: 1-3 queries (depending on request)
SELECT * FROM crypto_kline_hours LIMIT 168   # Short-term
SELECT * FROM crypto_kline_days LIMIT 30     # Medium-term
SELECT * FROM crypto_kline_weeks LIMIT 26    # Long-term
```

**Optimization**: Queries run in parallel (no sequential delay)

### Token Usage

Enhanced agents have longer prompts → more tokens:
- Planner: +2K tokens (time-horizon framework)
- Research: +1.5K tokens (relevance evaluation)
- Analysis: +2K tokens (multi-timeframe logic)
- Report: +1K tokens (format specification)

**Total increase**: ~6.5K tokens per request

**Mitigation**: Use `gpt-4o-mini` for database/research agents

---

## Rollback Plan

If issues arise, quickly rollback:

```python
# In multi_agent_orchestrator.py
class MultiAgentOrchestrator:
    def __init__(self, use_enhanced=False):  # ⬅️ Change default to False
        ...
```

Or environment variable:
```python
import os

use_enhanced = os.getenv("USE_ENHANCED_AGENTS", "false").lower() == "true"
orchestrator = MultiAgentOrchestrator(use_enhanced=use_enhanced)
```

Then:
```bash
# Disable enhanced system
export USE_ENHANCED_AGENTS=false

# Re-enable
export USE_ENHANCED_AGENTS=true
```

---

## Next Steps After Integration

1. **Monitor quality**: Compare outputs from enhanced vs original system
2. **Collect metrics**: Track success rate, cycles used, user satisfaction
3. **Fine-tune**: Adjust time horizon thresholds, indicator sets, report format
4. **Expand**: Add more cryptocurrencies, more indicators, more timeframes
5. **Optimize**: Cache common queries, reduce token usage, improve speed

---

**🎉 You're ready to integrate! Start with Option 1 (Full Replacement) for best results.**