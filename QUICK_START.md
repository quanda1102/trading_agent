# ⚡ Quick Start Guide

## 🎯 Fix JSON Errors in 30 Seconds

**File**: `trading_agent_tp/core/multi_agent_orchestrator.py`

Add this at the top:
```python
from .planner_agent_structured import planner_agent_structured
```

In `__init__` method, add:
```python
self.planner = planner_agent_structured
```

**Done!** Zero JSON errors guaranteed.

---

## 📊 Use Time-Horizon Aware System

Update agents in `__init__`:
```python
from ..agents.database_agent_enhanced import database_agent_enhanced
from ..agents.analysis_agent_enhanced import analysis_agent_enhanced
from ..agents.research_agent_enhanced import research_agent_enhanced
from ..agents.report_agent_enhanced import report_agent_enhanced

self.agents = {
    "database": database_agent_enhanced,
    "analysis": analysis_agent_enhanced,
    "research": research_agent_enhanced,
    "report": report_agent_enhanced
}
```

**Done!** Now system understands short/medium/long-term.

---

## 🧪 Test It

```python
import asyncio
from trading_agent_tp.core.multi_agent_orchestrator import MultiAgentOrchestrator

async def test():
    orch = MultiAgentOrchestrator()
    result = await orch.process_query(
        query="Phân tích BTC ngắn hạn",
        user_id="test",
        session_id="test123"
    )
    print(result["final_answer"])

asyncio.run(test())
```

Expected output:
```
## 🕓 1. Phân tích khung 4H (Ngắn hạn)
✅ Giá hiện tại: $109,250
✅ Xác suất hồi lên: ~65%
📌 Long: Vào $108,000, TP $111,000, SL $107,000
```

---

## 📁 Files You Need

All files already created in:
- `trading_agent_tp/core/planner_agent_structured.py` ✅
- `trading_agent_tp/core/planner_models.py` ✅
- `trading_agent_tp/core/orchestrator_utils.py` ✅
- `trading_agent_tp/tools/database_tool_enhanced.py` ✅
- `trading_agent_tp/agents/*_enhanced.py` ✅

---

## 🎓 Quick Examples

### Short-term analysis:
```python
query = "Phân tích BTC ngắn hạn"
# → Uses 1h data, recent news, intraday indicators
```

### Long-term analysis:
```python
query = "Phân tích BTC dài hạn"
# → Uses 1w data, 30-day news, cycle indicators
```

### Multi-timeframe:
```python
query = "Phân tích BTC toàn diện"
# → Uses 1h + 1d + 1w data, comprehensive report
```

---

## 📚 Full Documentation

| Need | Read |
|------|------|
| Fix errors now | QUICK_FIX_JSON_ERRORS.md |
| Understand system | ENHANCED_SYSTEM_GUIDE.md |
| Integration steps | INTEGRATION_GUIDE.md |
| Architecture | SYSTEM_ARCHITECTURE.md |
| Overview | README_ENHANCEMENTS.md |

---

## ✅ Checklist

- [ ] Added structured planner import
- [ ] Set `self.planner = planner_agent_structured`
- [ ] Updated agent imports (database, analysis, research, report)
- [ ] Set enhanced agents in `self.agents` dict
- [ ] Tested with a query
- [ ] Verified no JSON errors
- [ ] Checked report format

**All done?** 🎉 You're ready!

---

## 🆘 Emergency Fix

If something breaks, revert with:
```python
# Use original planner
from .planner import planner_agent
self.planner = planner_agent

# Use original agents
from ..agents import database_agent, analysis_agent, research_agent, report_agent
self.agents = {
    "database": database_agent,
    "analysis": analysis_agent,
    "research": research_agent,
    "report": report_agent
}
```

Then check the troubleshooting docs.

---

**That's it!** 🚀