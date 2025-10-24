# Planner-Executor Agent Implementation

This document describes the planner-executor agent implementation for the trading-agent-tp project, inspired by FlyAgent's hierarchical architecture.

## Overview

The planner-executor agent implements a two-stage hierarchical system:

1. **Planner Agent** (gpt-4o): Decomposes complex trading tasks into executable steps
2. **Executor Agent** (gpt-4o-mini): Executes individual tasks using available tools
3. **Orchestrator**: Coordinates the planning-execution loop (max 3 cycles)

## Architecture

```
User Query
    ↓
AgentRouter (keyword-based routing)
    ↓
┌─────────────────────────────────┐
│  PlannerExecutorOrchestrator    │
│                                 │
│  Cycle 1-3:                     │
│  ┌──────────────────────────┐ │
│  │ Planner: Create plan     │ │
│  │ Output: JSON task list   │ │
│  └──────────┬───────────────┘ │
│             ↓                   │
│  ┌──────────────────────────┐ │
│  │ Executor: Execute tasks  │ │
│  │ Tools: CodeInterpreter   │ │
│  └──────────┬───────────────┘ │
│             ↓                   │
│  Check: Complete or Replan?     │
└─────────────────────────────────┘
    ↓
Final Answer
```

## Files Created

### Core Components

1. **planner_agent.py** - Planner agent definition
   - Model: gpt-4o
   - Role: Task decomposition and synthesis
   - Output: JSON plans or final answers

2. **executor_agent.py** - Executor agent definition
   - Model: gpt-4o-mini
   - Role: Task execution
   - Tools: CodeInterpreterTool
   - Output: Concise task results

3. **planner_executor_orchestrator.py** - Coordination logic
   - Planning-execution loop (max 3 cycles)
   - Shared history management
   - Plan parsing and validation
   - Error handling

### Updated Files

4. **agent_router.py** - Added planning pattern detection
   - New `PLANNING_PATTERN` regex
   - Updated `AgentType` to include "planner"
   - Priority-based routing

5. **agent_endpoints.py** - Integrated orchestrator
   - Handles "planner" agent type
   - Returns execution metadata
   - Stores results in memory

## Routing Keywords

The agent router detects planning queries using these keywords:

**Vietnamese:**
- kế hoạch, chiến lược, lập kế, phương án
- bước thực hiện, đầu tư strategy

**English:**
- strategy, plan, trading plan, investment plan

**Priority Order:**
1. Planning keywords → PlannerExecutorAgent
2. Analysis keywords (phân tích) → TradingAgent
3. Default → ConversationalAgent

## API Usage

### Basic Request

```bash
curl -X POST "http://localhost:8888/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "question": "Lập kế hoạch đầu tư BTC cho tháng tới"
  }'
```

### Response Format

```json
{
  "status": "success",
  "response": "Đây là kế hoạch đầu tư BTC...",
  "agent_used": "PlannerExecutorAgent",
  "agent_type": "planner",
  "session_id": "session_20241022_143022",
  "user_id": "user123",
  "timestamp": "2024-10-22T14:30:22.123456Z",
  "metadata": {
    "plan_history": [
      {
        "cycle": 1,
        "plan": [
          {"id": 1, "description": "Phân tích xu hướng BTC hiện tại"},
          {"id": 2, "description": "Đánh giá các chỉ báo kỹ thuật"},
          {"id": 3, "description": "Xác định mức giá mục tiêu"}
        ]
      }
    ],
    "execution_log": [
      {
        "cycle": 1,
        "task_id": 1,
        "task": "Phân tích xu hướng BTC hiện tại",
        "result": "BTC đang trong xu hướng tăng...",
        "success": true
      }
    ],
    "cycles_used": 1,
    "timeout": false,
    "error": false
  }
}
```

## Example Queries

### Planning Queries (Use PlannerExecutorAgent)

```python
# Vietnamese
"Lập kế hoạch đầu tư BTC cho tháng tới"
"Tạo chiến lược trading cho ETH"
"Phương án phân tích và giao dịch SOL"
"Đưa ra bước thực hiện để trade BTC"

# English
"Create a trading strategy for Bitcoin"
"Plan an investment approach for ETH"
"Develop a trading plan for the next week"
```

### Analysis Queries (Use TradingAgent)

```python
"Phân tích kỹ thuật BTC"
"Phân tích xu hướng thị trường"
"Technical analysis for ETH"
```

### General Queries (Use ConversationalAgent)

```python
"What is Bitcoin?"
"Giá BTC hiện tại là bao nhiêu?"
"How does blockchain work?"
```

## Testing

### Run the Test Suite

```bash
# Start the API server
cd /home/quan-ubuntu/Desktop/projects/trading-agent-tp
python -m trading_agent_tp.main

# In another terminal, run tests
python test_planner_agent.py
```

### Test Coverage

The test suite includes:
1. **Routing Tests** - Verify queries route to correct agent
2. **Complex Planning Tests** - Test multi-step planning scenarios
3. **Execution Validation** - Check task execution and results

## Configuration

### Environment Variables

```bash
# .env file
OPENAI_API_KEY=your_api_key_here
```

### Model Configuration

Edit in `planner_agent.py` and `executor_agent.py`:

```python
# Planner
model="gpt-4o"  # Or gpt-4, claude-3-5-sonnet, etc.

# Executor
model="gpt-4o-mini"  # Faster, cheaper for execution
```

### Orchestrator Settings

Edit in `planner_executor_orchestrator.py`:

```python
MAX_CYCLES = 3  # Maximum planning-execution cycles
```

## Planner Output Format

The planner must output JSON in this format:

```json
{
  "plan": [
    {"id": 1, "description": "Clear task description"},
    {"id": 2, "description": "Another task"},
    {"id": 3, "description": "Final task"}
  ]
}
```

Or for final answer:

```
FINAL ANSWER: The complete answer goes here...
```

## Troubleshooting

### Planner Not Being Used

**Issue:** Queries not routing to planner agent

**Solution:** Check routing keywords in `agent_router.py`:
- Add more Vietnamese/English planning keywords
- Adjust regex patterns
- Check query contains planning intent

### Plan Parsing Errors

**Issue:** `[Planning Error] Cannot parse JSON plan`

**Causes:**
- Planner outputting malformed JSON
- Extra text around JSON
- Missing "plan" key

**Solution:**
- Planner system prompt enforces JSON-only output
- Orchestrator has robust parsing with regex fallbacks
- Check planner response in logs

### Execution Failures

**Issue:** Tasks failing during execution

**Check:**
- Executor has appropriate tools (CodeInterpreterTool)
- API keys are valid (OPENAI_API_KEY)
- Network connectivity for tool calls
- Task descriptions are clear and executable

### Max Cycles Reached

**Issue:** `Maximum planning cycles reached`

**Causes:**
- Complex task requires > 3 cycles
- Planner not outputting "FINAL ANSWER"
- Execution results insufficient

**Solutions:**
- Increase `MAX_CYCLES` in orchestrator
- Improve planner instructions
- Simplify task complexity

## Memory Integration

The planner-executor agent integrates with existing memory:

```python
# Memory is automatically included
memory_context = await get_session_memory(user_id, session_id, n=5)

# Planner sees previous conversation
planner_input = f"Previous conversation:\n{memory_context}\n\nCurrent question: {query}"

# Results stored automatically
await ai_memory.write(user_id, session_id, response_content, role="assistant")
```

## Performance

### Response Times

- **Simple plans (1-3 tasks):** 10-20 seconds
- **Complex plans (4-5 tasks):** 20-40 seconds
- **Multi-cycle planning:** 40-90 seconds

### Cost Optimization

- Planner uses gpt-4o (expensive but accurate)
- Executor uses gpt-4o-mini (cheap and fast)
- Shared history minimizes context length
- Max 3 cycles prevents runaway costs

## Future Enhancements

### 1. Custom Trading Tools

```python
# Add to executor_agent.py
from trading_tools import get_market_data, calculate_indicators

executor_agent = Agent(
    name="ExecutorAgent",
    model="gpt-4o-mini",
    tools=[
        CodeInterpreterTool(),
        get_market_data,
        calculate_indicators
    ]
)
```

### 2. Plan Templates

```python
# Create plan templates for common strategies
TREND_FOLLOWING_TEMPLATE = {
    "plan": [
        {"id": 1, "description": "Identify trend direction"},
        {"id": 2, "description": "Find entry points"},
        {"id": 3, "description": "Set stop-loss and targets"}
    ]
}
```

### 3. Parallel Task Execution

```python
# Execute independent tasks in parallel
import asyncio

async def execute_tasks_parallel(tasks):
    results = await asyncio.gather(
        *[execute_task(task) for task in tasks]
    )
    return results
```

### 4. Case-Based Reasoning (CBR)

```python
# Store successful plans for retrieval
await cbr_memory.store_plan(
    query=query,
    plan=plan,
    reward=success_score
)

# Retrieve similar plans
similar_plans = await cbr_memory.retrieve(query, top_k=3)
```

## Comparison: FlyAgent vs Trading Agent

| Feature | FlyAgent | Trading Agent |
|---------|----------|---------------|
| Framework | Custom LLM chat | OpenAI Agents |
| Tool System | MCP (stdio) | OpenAI Tools |
| Memory | Shared list | SQLite + ChromaDB |
| Message Trimming | Manual (tiktoken) | Framework-handled |
| Models | gpt-4.1 + o3 | gpt-4o + gpt-4o-mini |
| Tool Resolution | Fuzzy matching | Predefined |
| CBR Memory | Optional | Not yet |
| Max Cycles | 3 | 3 |

## Contributing

To add new agent types:

1. Create agent definition in `core/`
2. Add routing pattern to `agent_router.py`
3. Update `agent_endpoints.py` to handle new type
4. Add tests to `test_planner_agent.py`

## License

Same as trading-agent-tp project.

## Support

For issues or questions:
1. Check this README
2. Review the guide: `PLANNER_EXECUTOR_GUIDE.md`
3. Examine test cases: `test_planner_agent.py`
4. Check agent logs in console output