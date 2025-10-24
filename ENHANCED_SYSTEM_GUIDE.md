# Enhanced Multi-Timeframe Trading Agent System

## 🎯 Overview

This enhanced system provides **state-of-the-art** multi-timeframe trading analysis with intelligent planner-executor architecture. The system understands that different trading time horizons require different data sources, indicators, and information relevance.

### Key Enhancements

1. **Time-Horizon Aware Data Retrieval**: Automatically selects the correct database table based on analysis horizon
2. **Information Relevance Evaluation**: Filters news and research by age and relevance to the trading timeframe
3. **Intelligent Planner**: Understands time horizons and selects appropriate strategies
4. **Multi-Timeframe Analysis**: Comprehensive technical analysis across short/medium/long-term
5. **Professional Vietnamese Reports**: Matches your exact format with probability-based scenarios

---

## 📊 Time-Horizon Framework

### Short-Term (< 3 weeks)
- **Data Source**: `crypto_kline_hours` table
- **Intervals**: 1h, 4h
- **Indicators**: RSI(14), MACD(12,26,9), EMA(20,50), Bollinger Bands(20,2)
- **Support/Resistance**: Intraday levels, recent swing highs/lows
- **News Relevance**: Last 1-3 days only
- **Use Cases**: Scalping, day trading, intraday positioning

### Medium-Term (3 weeks - 3 months)
- **Data Source**: `crypto_kline_days` table
- **Intervals**: 1d (daily)
- **Indicators**: SMA(20,50,200), MACD divergence, RSI divergence, Volume Profile
- **Support/Resistance**: Swing levels, major trendlines, MA levels
- **News Relevance**: Last 7-14 days
- **Use Cases**: Swing trading, position building

### Long-Term (3-6 months)
- **Data Source**: `crypto_kline_weeks` table
- **Intervals**: 1w (weekly)
- **Indicators**: 200-week MA, Long-term SMAs, Fibonacci retracements
- **Support/Resistance**: Historical cycle bottoms/tops, psychological levels
- **News Relevance**: Last 30 days
- **Use Cases**: Position trading, strategic accumulation

### Very Long-Term (> 6 months)
- **Data Source**: `crypto_kline_months` table
- **Intervals**: 1M (monthly)
- **Indicators**: Market cycles, SMA(12,24), Fundamental value zones
- **Support/Resistance**: Multi-year levels
- **News Relevance**: Last 90 days
- **Use Cases**: HODL, DCA strategies

---

## 🏗️ Architecture

### Enhanced Components

#### 1. Enhanced Database Tool (`database_tool_enhanced.py`)

**Features**:
- Auto-detects time horizon from queries
- Retrieves data from correct table (hours/days/weeks/months)
- Provides metadata about data source and recommended indicators
- Supports multi-horizon queries

**Usage**:
```python
from trading_agent_tp.tools.database_tool_enhanced import smart_query_with_horizon

# Auto-detect horizon from query
result = smart_query_with_horizon("Get BTC data for short-term analysis")
# → Uses crypto_kline_hours with 1h interval

result = smart_query_with_horizon("Get BTC long-term trend data")
# → Uses crypto_kline_weeks with 1w interval

# Get multi-timeframe data
result = enhanced_db_tool.get_multi_horizon_data("btc", ["short", "medium", "long"])
# → Returns data from all three tables
```

**Configuration**:
```python
TimeHorizonConfig.SHORT_TERM = {
    "horizon": "short",
    "description": "< 3 weeks",
    "table": "crypto_kline_hours",
    "interval": "1h",
    "default_limit": 168,  # 1 week
    "indicators": ["RSI(14)", "MACD(12,26,9)", "EMA(20,50)", "Bollinger(20,2)"],
    "news_relevance_days": 3,
}
```

#### 2. Enhanced Planner Agent (`planner_agent_enhanced.py`)

**Intelligence**:
- Identifies time horizon from user question (Vietnamese & English)
- Selects appropriate data sources in task descriptions
- Specifies indicator sets matching the timeframe
- Evaluates information relevance on loop-back
- Creates multi-timeframe analysis plans when needed

**Example Planning**:

**User**: "Phân tích BTC ngắn hạn"

**Planner Output**:
```json
{
  "plan": [
    {
      "id": 1,
      "agent": "database",
      "description": "Retrieve BTC data from crypto_kline_hours (1h interval) for last 168 hours (7 days) for short-term analysis",
      "loop_back": true,
      "depends_on": null,
      "required_confidence": 0.9
    },
    {
      "id": 2,
      "agent": "research",
      "description": "Search for BTC news from LAST 24-48 HOURS ONLY (short-term relevance). Ignore news older than 3 days.",
      "loop_back": true,
      "depends_on": null,
      "required_confidence": 0.6
    },
    {
      "id": 3,
      "agent": "analysis",
      "description": "Calculate SHORT-TERM indicators: RSI(14), MACD(12,26,9), EMA(20,50), Bollinger Bands(20,2) on 1h data",
      "loop_back": true,
      "depends_on": [1],
      "required_confidence": 0.8
    },
    {
      "id": 4,
      "agent": "report",
      "description": "Generate SHORT-TERM Vietnamese report with 4H analysis, intraday S/R levels, immediate scenarios",
      "loop_back": false,
      "depends_on": [1, 2, 3],
      "required_confidence": 0.9
    }
  ],
  "estimated_cycles": 2
}
```

#### 3. Enhanced Research Agent (`research_agent_enhanced.py`)

**Relevance Evaluation**:
- Scores each news item (0-10) based on time horizon
- Filters by age (old news for short-term = irrelevant)
- Evaluates impact duration (flash crash vs regulation)
- Reports high-relevance vs low-relevance separately

**Example Output**:
```
## Market Research Report

**Time Horizon**: SHORT-TERM (< 3 weeks)
**Recency Requirement**: Last 1-3 days

### 📰 Relevant Findings (≥ 7/10)

**1. BTC breaks $110K (6 hours ago)**
- **Relevance Score**: 10/10 ✅
- **Age**: 6 hours ✅
- **Impact**: Immediate bullish momentum
- **Summary**: Bitcoin broke $110,000 with high volume...

### ⚠️ Low Relevance Findings (< 5/10)

**2. Bitcoin ETF approval (1 month ago)**
- **Relevance Score**: 2/10 ❌
- **Age**: 1 month ❌ (Too old for short-term)
- **Reason**: Old news, already priced in
- **Note**: Would be 8/10 for long-term analysis

### 📊 Sentiment (Filtered by Relevance)
Only considering RELEVANT news (≥7/10):
- Overall: BULLISH (8/10)
```

#### 4. Enhanced Analysis Agent (`analysis_agent_enhanced.py`)

**Multi-Timeframe Support**:
- Adjusts indicators based on data timeframe
- Interprets signals in context (RSI 70 on 1h ≠ RSI 70 on 1W)
- Provides horizon-specific support/resistance
- Synthesizes multiple timeframes

**Example**:
```python
# SHORT-TERM (1h data)
Indicators: RSI(14), MACD(12,26,9), EMA(20,50), Bollinger Bands
S/R: Intraday levels (last 3-7 days)
Output: Entry/exit for next 6-24 hours

# MEDIUM-TERM (1d data)
Indicators: SMA(20,50,200), MACD divergence, Volume Profile
S/R: Swing levels (last 30-90 days)
Output: Position for days to weeks

# LONG-TERM (1w data)
Indicators: 200-week MA, Long-term SMAs, Fibonacci
S/R: Multi-month/year levels
Output: Investment positioning
```

#### 5. Enhanced Report Agent (`report_agent_enhanced.py`)

**Vietnamese Format**:
- Matches your exact format specification
- Multi-timeframe sections (4H, 1D, 1W)
- Probability-based scenarios (~60% bullish, ~40% bearish)
- Specific entry/TP/SL for each timeframe
- Summary table and action recommendations

**Structure**:
```markdown
# Phân Tích BTC - Đa Khung Thời Gian

## 🕓 1. Phân tích khung 4H (Ngắn hạn)
### 🔸 Diễn biến giá
### 🔸 Hỗ trợ - Kháng cự ngắn hạn
### 🔸 Nhận định xác suất
### 📌 Gợi ý điểm vào - ra

## 📅 2. Phân tích khung 1D (Trung hạn)
[Same structure]

## 📅 3. Phân tích khung 1W (Dài hạn)
[Same structure]

## 📊 Tổng hợp chiến lược giao dịch
[Summary table]

## 🧭 Gợi ý hành động
- Trader ngắn hạn: [specific]
- Trader trung hạn: [specific]
- Holder dài hạn: [specific]
```

---

## 🚀 Usage

### Setup

1. **Install dependencies** (if not already installed):
```bash
cd trading-agent-tp
pip install -r requirements.txt
```

2. **Configure database** (`.env` file):
```env
MYSQL_HOST=your_host
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=finance_services
```

3. **Update orchestrator** to use enhanced agents:

```python
# In multi_agent_orchestrator.py
from ..core.planner_agent_enhanced import planner_agent_enhanced
from ..agents.database_agent_enhanced import database_agent_enhanced
from ..agents.analysis_agent_enhanced import analysis_agent_enhanced
from ..agents.research_agent_enhanced import research_agent_enhanced
from ..agents.report_agent_enhanced import report_agent_enhanced

# Replace imports
self.planner = planner_agent_enhanced
self.agents = {
    "database": database_agent_enhanced,
    "analysis": analysis_agent_enhanced,
    "research": research_agent_enhanced,
    "report": report_agent_enhanced,
}
```

### Example Queries

#### Short-Term Analysis
```python
query = "Phân tích BTC ngắn hạn cho trading hôm nay"
# System will:
# 1. Detect: SHORT-TERM horizon
# 2. Retrieve: crypto_kline_hours (1h data)
# 3. Research: News from last 24-48 hours
# 4. Analyze: RSI, MACD, EMA, Bollinger on 1h
# 5. Report: 4H analysis with intraday S/R
```

#### Multi-Timeframe Analysis
```python
query = "Phân tích BTC toàn diện cả ngắn hạn, trung hạn và dài hạn"
# System will:
# 1. Detect: MULTI-TIMEFRAME request
# 2. Retrieve: 1h, 1d, 1w data (parallel)
# 3. Research: News categorized by timeframe relevance
# 4. Analyze: Each timeframe with appropriate indicators
# 5. Report: Comprehensive 3-section report with synthesis
```

#### Long-Term Investment Analysis
```python
query = "Phân tích xu hướng dài hạn BTC cho đầu tư"
# System will:
# 1. Detect: LONG-TERM horizon
# 2. Retrieve: crypto_kline_weeks (1w data)
# 3. Research: News from last 30 days (fundamentals)
# 4. Analyze: 200W MA, cycle position, major S/R
# 5. Report: 1W analysis with accumulation zones
```

---

## 🔄 Workflow

### Step 1: User Query → Planner
User sends query (Vietnamese or English)
→ Planner identifies time horizon
→ Planner creates tasks with correct data sources

### Step 2: Parallel Task Execution
Tasks without dependencies run in parallel:
- DatabaseAgent retrieves data from correct table
- ResearchAgent searches for time-relevant news

### Step 3: Sequential Analysis
After data arrives:
- AnalysisAgent calculates indicators (depends on data)
- Uses indicators appropriate for the timeframe

### Step 4: Loop-Back Evaluation
Results loop back to Planner:
- Planner evaluates information relevance
- If irrelevant news → Replans with better criteria
- If sufficient data → Proceeds to report

### Step 5: Final Report Generation
ReportAgent receives all results:
- Synthesizes data, analysis, research
- Generates Vietnamese report
- Matches exact format specification
- Returns to user

---

## 📝 Configuration

### Adjusting Time Horizons

Edit `database_tool_enhanced.py`:
```python
TimeHorizonConfig.SHORT_TERM = {
    "horizon": "short",
    "table": "crypto_kline_hours",
    "interval": "1h",  # Change to "4h" if preferred
    "default_limit": 168,  # Adjust number of records
    "news_relevance_days": 3,  # Adjust news age threshold
}
```

### Adding Custom Indicators

Edit `analysis_agent_enhanced.py`:
```python
# Add to SHORT_TERM section:
"indicators": [
    "RSI(14)",
    "MACD(12,26,9)",
    "EMA(20,50)",
    "Bollinger(20,2)",
    "ATR(14)",  # ADD NEW
]
```

### Customizing Report Format

Edit `report_agent_enhanced.py` instructions:
- Adjust section headers
- Change probability calculation logic
- Modify Vietnamese terminology
- Add/remove emojis

---

## 🎯 Best Practices

### 1. Time Horizon Clarity

**Good**:
- "Phân tích BTC **ngắn hạn** cho trading hôm nay"
- "Xu hướng **dài hạn** BTC để đầu tư"
- "Phân tích **toàn diện** BTC cả 3 khung thời gian"

**Avoid**:
- "Phân tích BTC" (ambiguous → defaults to medium-term)
- Mixing timeframes without clarity

### 2. Information Relevance

The system automatically filters:
- Short-term analysis ignores news > 3 days old
- Long-term analysis ignores daily noise
- Research agent scores relevance explicitly

Trust the relevance scores in the output.

### 3. Multi-Timeframe Synthesis

When all timeframes align → High confidence signal
When timeframes diverge → Context-dependent action

Example:
- Short-term: Bearish (pullback)
- Medium-term: Bullish (uptrend intact)
- Long-term: Bullish (macro trend)

→ **Action**: Dip buying opportunity for swing/long-term traders

### 4. Stop-Loss Discipline

The system provides specific SL levels for each timeframe:
- Short-term: Tight SL (2-3% below support)
- Medium-term: Wider SL (5-7% below swing low)
- Long-term: Strategic SL (10%+ below major support)

Always use the SL matching your trading horizon.

---

## 🔧 Troubleshooting

### Issue: Wrong data table used

**Cause**: Time horizon not detected correctly

**Solution**:
- Be explicit: "ngắn hạn", "dài hạn", "1h", "weekly"
- Check planner output for table selection
- Adjust `TimeHorizonConfig.auto_detect_horizon()` keywords

### Issue: Irrelevant news in report

**Cause**: Research agent didn't filter properly

**Solution**:
- Check research agent output for relevance scores
- Verify news age vs timeframe requirement
- Adjust `news_relevance_days` in config

### Issue: Indicators don't match timeframe

**Cause**: Analysis agent received wrong data or instructions

**Solution**:
- Verify data source (check `interval` field)
- Ensure planner specified correct indicators in task
- Check analysis agent output for warnings

### Issue: Report format doesn't match example

**Cause**: Report agent not following template

**Solution**:
- Verify all input data is available (data, analysis, research)
- Check for partial data warnings
- Review report agent prompt if customization needed

---

## 📊 Database Schema Reference

### crypto_kline_hours
```sql
SELECT * FROM finance_services.crypto_kline_hours
WHERE symbol = 'btc' AND interval = '1h'
ORDER BY close_time DESC
LIMIT 168;

-- Columns:
-- id, symbol, interval, open_price, high_price, low_price, close_price,
-- volume, quote_volume, trade_count, taker_buy_base_volume,
-- taker_buy_quote_volume, open_time, close_time, updated_at
```

### crypto_kline_days
```sql
SELECT * FROM finance_services.crypto_kline_days
WHERE symbol = 'btc' AND interval = '1d'
ORDER BY close_time DESC
LIMIT 30;
```

### crypto_kline_weeks
```sql
SELECT * FROM finance_services.crypto_kline_weeks
WHERE symbol = 'btc' AND interval = '1w'
ORDER BY close_time DESC
LIMIT 26;
```

### crypto_kline_months
```sql
SELECT * FROM finance_services.crypto_kline_months
WHERE symbol = 'btc' AND interval = '1M'
ORDER BY close_time DESC
LIMIT 24;
```

---

## 🎓 Learning Resources

### Understanding Time Horizons

- **Short-term**: Focus on momentum, fast indicators, intraday levels
- **Medium-term**: Focus on trends, divergences, swing levels
- **Long-term**: Focus on cycles, fundamentals, macro levels

### Indicator Selection by Timeframe

| Timeframe | Fast Indicators | Trend Indicators | S/R Levels |
|-----------|----------------|------------------|------------|
| 1h / 4h   | RSI, MACD, Stochastic | EMA(20,50) | Intraday |
| 1d        | RSI divergence, MACD | SMA(20,50,200) | Swing |
| 1w / 1M   | Cycle patterns | 200W MA, Long SMAs | Historical |

### Information Relevance by Horizon

| Horizon | Relevant News Age | Example Relevant | Example Irrelevant |
|---------|------------------|------------------|-------------------|
| Short   | 1-3 days         | Flash crash today | ETF approved 2 months ago |
| Medium  | 7-14 days        | Exchange listing | Daily price noise |
| Long    | 30-90 days       | Regulation change | Intraday whale trade |

---

## 🚀 Next Steps

1. **Test the enhanced system**:
   - Run short-term query
   - Run long-term query
   - Run multi-timeframe query
   - Compare outputs

2. **Customize for your needs**:
   - Adjust time horizon definitions
   - Add custom indicators
   - Modify report format
   - Tune relevance thresholds

3. **Monitor quality**:
   - Check planner's table selection
   - Verify research relevance scores
   - Validate indicator calculations
   - Review report format adherence

4. **Iterate and improve**:
   - Collect user feedback
   - Adjust probability calculations
   - Fine-tune S/R detection
   - Enhance Vietnamese terminology

---

## 📞 Support

For issues or questions:
1. Check this guide first
2. Review agent prompts in source files
3. Enable debug logging to see agent reasoning
4. Test individual agents standalone

---

**🎉 Congratulations! You now have a state-of-the-art multi-timeframe trading analysis system with intelligent time-horizon awareness and professional Vietnamese reporting.**