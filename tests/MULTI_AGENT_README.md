# Multi-Agent Trading Analysis System

## 🎯 Overview

An advanced cryptocurrency trading analysis system powered by **4 specialized AI agents** that work together to provide comprehensive market analysis in Vietnamese.

### Architecture: Planner-Executor with Specialized Agents

```
User Question
      ↓
┌─────────────────┐
│  META-PLANNER   │ ← Analyzes question, creates task plan
└─────────────────┘
      ↓
┌─────────────────────────────────────────────────┐
│         MULTI-AGENT ORCHESTRATOR                │
│  (Intelligent Task Delegation)                  │
└─────────────────────────────────────────────────┘
      ↓
┌────────────┬────────────┬────────────┬──────────┐
│ DATABASE   │ ANALYSIS   │ RESEARCH   │ REPORT   │
│ Agent      │ Agent      │ Agent      │ Agent    │
├────────────┼────────────┼────────────┼──────────┤
│ Data       │ Technical  │ Web        │ Format   │
│ Retrieval  │ Analysis   │ Research   │ Output   │
└────────────┴────────────┴────────────┴──────────┘
      ↓
┌─────────────────────────────────────────────────┐
│  Structured Vietnamese Trading Report          │
│  with Emojis, Tables, and Recommendations      │
└─────────────────────────────────────────────────┘
```

## 🤖 Specialized Agents

### 1. **DatabaseAgent** (gpt-4o-mini)
**Specialization**: Data retrieval and validation

**Tools**:
- `database_query_tool` - Smart SQL agent with natural language to SQL conversion

**Capabilities**:
- Fetch OHLCV data from MySQL database
- Validate data quality and completeness
- Cross-check data consistency
- Handle 10 cryptocurrencies: BTC, ETH, SOL, BNB, XRP, ADA, DOGE, AVAX, LINK, DOT

**Example Task**: "Retrieve and validate BTC price data for last 100 records"

---

### 2. **AnalysisAgent** (gpt-4o)
**Specialization**: Technical analysis with indicators

**Tools**:
- `CodeInterpreterTool` - Python execution with pandas, numpy, ta-lib

**Capabilities**:
- Calculate technical indicators:
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Moving Averages (SMA, EMA 20/50/200)
  - Bollinger Bands
  - ATR (Average True Range)
  - Volume analysis
- Identify support and resistance levels
- Detect candlestick patterns
- Statistical analysis (volatility, correlations)
- Trend identification

**Example Task**: "Calculate RSI, MACD, and MA20/50/200 for BTC, identify support/resistance levels"

---

### 3. **ResearchAgent** (gpt-4o-mini)
**Specialization**: Web research and fact-checking

**Tools**:
- `WebSearchTool` - Real-time web search

**Capabilities**:
- Search latest cryptocurrency news
- Analyze market sentiment (bullish/bearish/neutral)
- Fact-check information from multiple sources
- Track regulatory updates
- Monitor social media sentiment
- Cross-validate database data with web sources

**Example Task**: "Search for latest BTC news and analyze overall market sentiment"

---

### 4. **ReportAgent** (gpt-4o)
**Specialization**: Vietnamese structured output formatting

**Tools**: None (pure formatting)

**Capabilities**:
- Generate professional Vietnamese trading reports
- Format with emojis, tables, and visual structure
- Synthesize results from other agents
- Create actionable trading strategies (Scenario A/B)
- Provide risk warnings and disclaimers
- Include source citations

**Example Task**: "Format all analysis results into Vietnamese structured report with trading recommendations"

---

## 📊 Output Format

The system generates comprehensive Vietnamese reports with 6 main sections:

### 1️⃣ Process Steps Display
```
🤖 Process Display:
✅ Aime có sẵn câu trả lời
✅ Phân tích câu hỏi hoàn tất
✅ Lấy dữ liệu BTC thành công
✅ Phân tích kỹ thuật hoàn tất
✅ Kiểm tra tin tức hoàn tất
```

### 2️⃣ Quick Summary
Emoji-rich 2-3 sentence summary using:
- 🚀 (bullish) 📉 (bearish) ⚠️ (warning) 📊 (analysis) 💡 (insight)

### 3️⃣ Price & Volume
- Current price with 24h change
- Volume comparison vs average

### 4️⃣ Support & Resistance Table
| Mức | Giá trị | Độ mạnh | Ghi chú |
|-----|---------|---------|---------|
| Kháng cự 2 | $XX,XXX | ⭐⭐⭐ | ... |
| Kháng cự 1 | $XX,XXX | ⭐⭐ | ... |
| Giá hiện tại | **$XX,XXX** | - | - |
| Hỗ trợ 1 | $XX,XXX | ⭐⭐⭐ | ... |
| Hỗ trợ 2 | $XX,XXX | ⭐⭐⭐⭐ | ... |

### 5️⃣ Momentum Indicators
- MACD (12, 26, 9) with interpretation
- RSI(14) with overbought/oversold status
- Moving Averages (20/50/200) positions

### 6️⃣ Market Updates & News
- Latest news with source citations
- Market sentiment analysis
- Fear & Greed Index (if available)

### 7️⃣ Trading Strategy Suggestions

**Scenario A: Bullish (Probability: XX%)**
- Conditions
- Entry point
- Targets (T1, T2)
- Stop loss

**Scenario B: Bearish/Correction (Probability: XX%)**
- Conditions
- Wait/entry strategy
- Targets
- Stop loss

### 8️⃣ Final Advice
- Overall recommendation (HOLD/BUY/SELL/WAIT)
- Important warnings
- Key levels to monitor
- Risk management tips

### 9️⃣ Sources
- Database details
- Technical analysis methods
- News sources
- Timestamp

---

## 🚀 Quick Start

### Installation

```bash
cd trading-agent-tp

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and database credentials
```

### Running the System

```bash
# Start multi-agent system
python main_multi_agent.py

# Server will start on http://localhost:8000
# Access API docs at http://localhost:8000/docs
```

### Basic Usage

```python
import requests

# Simple technical analysis
response = requests.post("http://localhost:8000/api/v2/chat", json={
    "question": "Phân tích kỹ thuật BTC hiện tại",
    "user_id": "trader123",
    "session_id": "session456",
    "use_memory": True
})

print(response.json()["final_answer"])
```

### Quick Analysis Endpoint

```python
# Quick analysis without constructing full query
response = requests.post(
    "http://localhost:8000/api/v2/analyze",
    params={
        "symbol": "BTC",
        "analysis_type": "full"  # technical, fundamental, sentiment, full
    }
)

print(response.json()["final_answer"])
```

---

## 🔧 API Endpoints

### 1. `/api/v2/chat` (POST)
Main chat endpoint with multi-agent orchestration.

**Request**:
```json
{
    "question": "Phân tích kỹ thuật BTC và đưa ra dự đoán",
    "user_id": "user123",
    "session_id": "session456",
    "use_memory": true
}
```

**Response**:
```json
{
    "success": true,
    "final_answer": "... Vietnamese structured report ...",
    "plan_history": [...],
    "execution_log": [...],
    "agent_results": {
        "database": [...],
        "analysis": [...],
        "research": [...],
        "report": [...]
    },
    "cycles_used": 2,
    "error": null,
    "timeout": false
}
```

### 2. `/api/v2/analyze` (POST)
Quick analysis for specific symbols.

**Parameters**:
- `symbol`: BTC, ETH, SOL, etc.
- `analysis_type`: technical, fundamental, sentiment, full

### 3. `/api/v2/agents` (GET)
List all available agents and their capabilities.

### 4. `/api/v2/health` (GET)
Health check - verify all agents loaded correctly.

### 5. `/api/v2/memory/{user_id}/{session_id}` (GET)
Get conversation memory summary.

### 6. `/api/v2/memory/{user_id}/{session_id}` (DELETE)
Clear conversation memory for fresh start.

---

## 🎓 Example Queries

### Technical Analysis
```
"Phân tích kỹ thuật BTC hiện tại"
"BTC có nên mua không? Phân tích RSI và MACD"
"Cho tôi biết hỗ trợ và kháng cự của ETH"
```

### Market Research
```
"Tin tức mới nhất về Bitcoin là gì?"
"Tâm lý thị trường BTC hiện tại như thế nào?"
"Có sự kiện quan trọng nào sắp diễn ra với ETH không?"
```

### Comprehensive Analysis
```
"Phân tích toàn diện BTC: kỹ thuật, tin tức, và khuyến nghị"
"ETH nên mua hay bán? Phân tích đầy đủ"
"Đánh giá tổng quan thị trường SOL"
```

### Fact-Checking
```
"Kiểm tra xem giá BTC có đúng là $43,000 không?"
"Xác minh thông tin về ETF Bitcoin mới"
"So sánh giá BTC từ database và web"
```

---

## 🏗️ Architecture Details

### Task Delegation Logic

The **MultiAgentOrchestrator** intelligently delegates tasks to appropriate agents based on keywords:

```python
# Keywords for each agent
Database: retrieve, fetch, get data, query, ohlcv, price data
Analysis: calculate, analyze, indicator, rsi, macd, support, resistance
Research: search, news, sentiment, web, fact check, verify
Report: format, report, generate, structure, vietnamese
```

### Planning-Execution Loop

1. **User sends question** → Orchestrator receives
2. **META-PLANNER analyzes** → Creates task plan (JSON)
3. **For each task**:
   - Orchestrator identifies appropriate agent
   - Agent executes task with its specialized tools
   - Result added to shared history
4. **After all tasks**:
   - Planner reviews results
   - If complete → Outputs "FINAL ANSWER"
   - If incomplete → Creates new plan (max 3 cycles)

### Shared History Pattern

All agents communicate via shared conversation history:
```
User: "Phân tích BTC"
Planner: {"plan": [...]}
DatabaseAgent: "Retrieved 100 BTC records, latest price: $43,250"
AnalysisAgent: "RSI: 67.8 (overbought), MACD: bullish crossover"
ResearchAgent: "Latest news: BTC broke resistance, sentiment: 7/10 bullish"
Planner: "FINAL ANSWER: [Vietnamese report]"
```

---

## 📦 File Structure

```
trading-agent-tp/
├── trading_agent_tp/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── database_agent.py    # DatabaseAgent with validation
│   │   ├── analysis_agent.py    # AnalysisAgent with TA-Lib
│   │   ├── research_agent.py    # ResearchAgent with fact-checking
│   │   └── report_agent.py      # ReportAgent for Vietnamese output
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── planner.py           # META-PLANNER agent
│   │   ├── executor.py          # Legacy executor (for compatibility)
│   │   ├── orchestrator.py      # Legacy orchestrator
│   │   └── multi_agent_orchestrator.py  # New multi-agent coordinator
│   │
│   ├── tools/
│   │   ├── database_tool.py     # Smart SQL agent
│   │   ├── code_tool.py         # Code execution wrapper
│   │   └── web_search_tool.py   # Web search wrapper
│   │
│   ├── api/
│   │   ├── endpoints.py         # Legacy API
│   │   └── multi_agent_endpoints.py  # New multi-agent API
│   │
│   ├── memory/
│   │   └── memory_manager.py    # Conversation memory
│   │
│   └── database/
│       └── connection.py        # MySQL connection
│
├── main_multi_agent.py          # Main application entry
├── requirements.txt
├── .env.example
└── MULTI_AGENT_README.md       # This file
```

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file:

```bash
# OpenAI API Key (required for agents)
OPENAI_API_KEY=sk-...

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=crypto_trading

# Optional: Web Search API (if using custom provider)
SEARCH_API_KEY=...
```

### Agent Configuration

Modify agent settings in respective files:
- `trading_agent_tp/agents/database_agent.py` - Change model, tools
- `trading_agent_tp/agents/analysis_agent.py` - Add indicators, patterns
- `trading_agent_tp/agents/research_agent.py` - Configure search parameters
- `trading_agent_tp/agents/report_agent.py` - Customize output format

### Orchestrator Configuration

In `trading_agent_tp/core/multi_agent_orchestrator.py`:

```python
class MultiAgentOrchestrator:
    MAX_CYCLES = 3  # Maximum planning-execution cycles
```

---

## 🧪 Testing

### Test Individual Agents

```python
from agents import Runner
from trading_agent_tp.agents import database_agent, analysis_agent

runner = Runner()

# Test DatabaseAgent
result = await runner.run(
    database_agent,
    "Retrieve latest 100 BTC price records"
)
print(result.content)

# Test AnalysisAgent
result = await runner.run(
    analysis_agent,
    "Calculate RSI(14) and MACD for the provided BTC data"
)
print(result.content)
```

### Test Full System

```bash
# Start server
python main_multi_agent.py

# In another terminal, test with curl
curl -X POST http://localhost:8000/api/v2/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Phân tích kỹ thuật BTC",
    "user_id": "test",
    "session_id": "test_session"
  }'
```

---

## 🐛 Troubleshooting

### Issue: Agent not loading
**Solution**: Check OpenAI API key in `.env`

### Issue: Database connection failed
**Solution**: Verify MySQL credentials and ensure database is running

### Issue: "Maximum cycles reached"
**Solution**: Question may be too complex. Try:
- Breaking into smaller questions
- Being more specific about requirements
- Checking if database has required data

### Issue: JSON parsing error in planner
**Solution**: Usually self-recovers in next cycle. If persistent:
- Check planner prompt for formatting issues
- Increase MAX_CYCLES if tasks are complex

---

## 📈 Performance

### Speed Optimization
- DatabaseAgent uses `gpt-4o-mini` for fast queries
- ResearchAgent uses `gpt-4o-mini` for quick searches
- AnalysisAgent and ReportAgent use `gpt-4o` for quality

### Cost Optimization
- Average query: $0.02 - $0.10 depending on complexity
- Simple technical analysis: ~$0.02
- Full comprehensive report: ~$0.08
- With web search: +$0.02

### Caching
- Conversation memory reduces context tokens
- Database query results can be cached (future enhancement)

---

## 🔒 Security

### API Key Protection
- Never commit `.env` file
- Use environment variables only
- Rotate keys regularly

### Database Security
- Use read-only database user for agents
- SQL injection protection via parameterized queries
- Validate all inputs before database queries

### Rate Limiting (Recommended)
```python
# Add to main_multi_agent.py
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v2/chat")
@limiter.limit("10/minute")
async def chat_endpoint(request: ChatRequest):
    ...
```

---

## 🚀 Future Enhancements

### Planned Features
- [ ] Real-time streaming responses
- [ ] Chart generation with matplotlib
- [ ] Backtesting capabilities
- [ ] Portfolio analysis
- [ ] Multiple timeframe analysis
- [ ] Alert system for price levels
- [ ] Telegram bot integration
- [ ] WebSocket support

### Agent Enhancements
- [ ] **DatabaseAgent**: Add more cryptocurrencies, timeframes
- [ ] **AnalysisAgent**: Add more indicators (Ichimoku, Fibonacci, Elliott Wave)
- [ ] **ResearchAgent**: Integrate Twitter/Reddit sentiment analysis
- [ ] **ReportAgent**: Add PDF export, email reports

---

## 📚 References

### Technical Analysis
- [TA-Lib Documentation](https://ta-lib.org/)
- [Technical Analysis Patterns](https://www.investopedia.com/technical-analysis-4689657)

### OpenAI Agents Framework
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-sdk)
- [OpenAI API Documentation](https://platform.openai.com/docs)

### Vietnamese Trading Terminology
- See `trading_agent_tp/agents/report_agent.py` for complete glossary

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 💬 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact: [your contact info]

---

**Built with ❤️ using OpenAI Agents Framework**