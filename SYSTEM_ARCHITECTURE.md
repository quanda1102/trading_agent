# Enhanced Trading Agent System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER QUERY                             │
│     "Phân tích BTC ngắn hạn / trung hạn / dài hạn"             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   ENHANCED PLANNER AGENT                        │
│                                                                 │
│  Step 1: Identify Time Horizon                                 │
│  ┌──────────────────────────────────────┐                     │
│  │ "ngắn hạn" → SHORT-TERM              │                     │
│  │ "trung hạn" → MEDIUM-TERM            │                     │
│  │ "dài hạn" → LONG-TERM                │                     │
│  │ "toàn diện" → MULTI-TIMEFRAME        │                     │
│  └──────────────────────────────────────┘                     │
│                                                                 │
│  Step 2: Create Time-Aware Tasks                               │
│  ┌──────────────────────────────────────┐                     │
│  │ Task 1: Database                      │                     │
│  │   "Retrieve from crypto_kline_hours"  │                     │
│  │                                       │                     │
│  │ Task 2: Research                      │                     │
│  │   "News from LAST 24 HOURS"          │                     │
│  │                                       │                     │
│  │ Task 3: Analysis                      │                     │
│  │   "Calculate RSI, MACD, EMA on 1h"   │                     │
│  │                                       │                     │
│  │ Task 4: Report                        │                     │
│  │   "Generate SHORT-TERM report"        │                     │
│  └──────────────────────────────────────┘                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
                    ┌────────┴────────┐
                    │                 │
        ┌───────────↓──┐   ┌──────────↓──────┐
        │ TASK 1      │   │ TASK 2           │  (Parallel)
        │ Database    │   │ Research         │
        └───────────┬──┘   └──────────┬───────┘
                    │                 │
                    ↓                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                  ENHANCED DATABASE AGENT                        │
│                                                                 │
│  Input: "Retrieve BTC short-term data"                          │
│                                                                 │
│  Step 1: Detect Horizon                                         │
│  ┌──────────────────────────────────────┐                     │
│  │ "short-term" → Use SHORT-TERM config │                     │
│  └──────────────────────────────────────┘                     │
│                                                                 │
│  Step 2: Select Table & Interval                                │
│  ┌──────────────────────────────────────┐                     │
│  │ Table: crypto_kline_hours            │                     │
│  │ Interval: 1h                         │                     │
│  │ Limit: 168 (7 days)                  │                     │
│  └──────────────────────────────────────┘                     │
│                                                                 │
│  Step 3: Execute Query                                          │
│  ┌──────────────────────────────────────┐                     │
│  │ SELECT * FROM crypto_kline_hours     │                     │
│  │ WHERE symbol='btc' AND interval='1h' │                     │
│  │ ORDER BY close_time DESC LIMIT 168   │                     │
│  └──────────────────────────────────────┘                     │
│                                                                 │
│  Output:                                                        │
│  ┌──────────────────────────────────────┐                     │
│  │ Data: 168 hourly candles             │                     │
│  │ Metadata:                            │                     │
│  │   - Horizon: short                   │                     │
│  │   - Interval: 1h                     │                     │
│  │   - Recommended indicators:          │                     │
│  │     RSI, MACD, EMA, Bollinger        │                     │
│  │   - News relevance: 3 days           │                     │
│  └──────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                 ENHANCED RESEARCH AGENT                         │
│                                                                 │
│  Input: "Search BTC news from LAST 24 HOURS"                   │
│                                                                 │
│  Step 1: Execute Search                                         │
│  ┌──────────────────────────────────────┐                     │
│  │ WebSearch: "Bitcoin BTC news today"  │                     │
│  └──────────────────────────────────────┘                     │
│                                                                 │
│  Step 2: Evaluate Relevance                                     │
│  ┌──────────────────────────────────────┐                     │
│  │ News 1: "BTC breaks $110K" (6h ago)  │                     │
│  │   Age: 6h ✅                         │                     │
│  │   Relevance: 10/10 ✅ SIGNAL         │                     │
│  │                                       │                     │
│  │ News 2: "ETF approved" (1 month ago) │                     │
│  │   Age: 1 month ❌                     │                     │
│  │   Relevance: 2/10 ❌ NOISE           │                     │
│  └──────────────────────────────────────┘                     │
│                                                                 │
│  Step 3: Filter & Score                                         │
│  ┌──────────────────────────────────────┐                     │
│  │ High Relevance (≥7/10): 2 items      │                     │
│  │ Low Relevance (<7/10): 3 items       │                     │
│  │ Sentiment (filtered): Bullish 8/10   │                     │
│  └──────────────────────────────────────┘                     │
│                                                                 │
│  Output:                                                        │
│  ┌──────────────────────────────────────┐                     │
│  │ Relevant News:                       │                     │
│  │   - BTC breakout (10/10)             │                     │
│  │   - Whale activity (8/10)            │                     │
│  │ Sentiment: Bullish (8/10)            │                     │
│  │ Confidence: HIGH                     │                     │
│  └──────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘

                             │
                             ↓
                      (Loop Back to Planner)
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   PLANNER EVALUATION                            │
│                                                                 │
│  Received:                                                      │
│  ✅ Database: 168 hours of 1h data                             │
│  ✅ Research: 2 relevant news items                            │
│                                                                 │
│  Evaluation:                                                    │
│  ✅ Data quality: HIGH                                         │
│  ✅ Information relevant: YES                                  │
│  ✅ Ready for analysis: YES                                    │
│                                                                 │
│  Decision: Proceed to Analysis Task                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                  ENHANCED ANALYSIS AGENT                        │
│                                                                 │
│  Input: Database results + Research context                    │
│                                                                 │
│  Step 1: Identify Timeframe from Data                          │
│  ┌──────────────────────────────────────┐                     │
│  │ Data interval: 1h → SHORT-TERM       │                     │
│  └──────────────────────────────────────┘                     │
│                                                                 │
│  Step 2: Calculate Timeframe-Specific Indicators                │
│  ┌──────────────────────────────────────┐                     │
│  │ For 1h data:                         │                     │
│  │   - RSI(14) = 67.8                   │                     │
│  │   - MACD = 145.2 vs Signal 132.4     │                     │
│  │   - EMA(20) = $108,450               │                     │
│  │   - EMA(50) = $107,200               │                     │
│  │   - Bollinger Upper = $110,500       │                     │
│  │   - Bollinger Lower = $106,700       │                     │
│  └──────────────────────────────────────┘                     │
│                                                                 │
│  Step 3: Identify S/R (Intraday for short-term)                │
│  ┌──────────────────────────────────────┐                     │
│  │ Resistance:                          │                     │
│  │   R1: $110,500 (Upper BB + recent)   │                     │
│  │   R2: $111,000 (psychological)       │                     │
│  │ Support:                             │                     │
│  │   S1: $108,450 (EMA20)               │                     │
│  │   S2: $107,200 (EMA50)               │                     │
│  └──────────────────────────────────────┘                     │
│                                                                 │
│  Step 4: Interpret in Context                                   │
│  ┌──────────────────────────────────────┐                     │
│  │ Trend: BULLISH (price > EMAs)        │                     │
│  │ Momentum: POSITIVE (MACD > Signal)   │                     │
│  │ Risk: MODERATE (RSI high, near R)    │                     │
│  └──────────────────────────────────────┘                     │
│                                                                 │
│  Output:                                                        │
│  ┌──────────────────────────────────────┐                     │
│  │ SHORT-TERM Technical Analysis:       │                     │
│  │   - Current: $109,250                │                     │
│  │   - Trend: Bullish                   │                     │
│  │   - RSI: 67.8 (approaching overbought)│                    │
│  │   - MACD: Bullish crossover 8h ago   │                     │
│  │   - R1: $110,500, S1: $108,450       │                     │
│  │   - Signal: WAIT or PARTIAL TP       │                     │
│  └──────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘

                             │
                             ↓
                      (Loop Back to Planner)
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   PLANNER FINAL CHECK                           │
│                                                                 │
│  Received:                                                      │
│  ✅ Database results                                           │
│  ✅ Research results (relevant news)                           │
│  ✅ Analysis results (indicators + S/R)                        │
│                                                                 │
│  Decision: Ready for Final Report                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                  ENHANCED REPORT AGENT                          │
│                                                                 │
│  Input: All aggregated results                                 │
│                                                                 │
│  Step 1: Extract Data                                           │
│  ┌──────────────────────────────────────┐                     │
│  │ From Database:                       │                     │
│  │   - Current price: $109,250          │                     │
│  │   - 24h high/low: $112K/$108K        │                     │
│  │ From Analysis:                       │                     │
│  │   - RSI, MACD, EMAs, BB              │                     │
│  │   - S/R levels                       │                     │
│  │ From Research:                       │                     │
│  │   - Relevant news (bullish)          │                     │
│  └──────────────────────────────────────┘                     │
│                                                                 │
│  Step 2: Calculate Probabilities                                │
│  ┌──────────────────────────────────────┐                     │
│  │ Bullish factors:                     │                     │
│  │   +10% (MACD bullish)                │                     │
│  │   +10% (price > EMAs)                │                     │
│  │   +10% (news positive)               │                     │
│  │   -5% (RSI high)                     │                     │
│  │   -5% (near resistance)              │                     │
│  │ Result: 60% bullish, 40% bearish     │                     │
│  └──────────────────────────────────────┘                     │
│                                                                 │
│  Step 3: Generate Vietnamese Report                             │
│  ┌──────────────────────────────────────┐                     │
│  │ ## 🕓 1. Phân tích khung 4H          │                     │
│  │ ### 🔸 Diễn biến giá                 │                     │
│  │ Giá hiện tại: $109,250               │                     │
│  │ Biên độ 24h: $108,000 - $112,000     │                     │
│  │ [Analysis...]                        │                     │
│  │                                       │                     │
│  │ ### 🔸 Hỗ trợ - Kháng cự             │                     │
│  │ Kháng cự: $110,500 / $111,000        │                     │
│  │ Hỗ trợ: $108,450 / $107,200          │                     │
│  │                                       │                     │
│  │ ### 🔸 Nhận định xác suất            │                     │
│  │ ✅ Xác suất hồi lên ~60%             │                     │
│  │ ❌ Xác suất giảm ~40%                │                     │
│  │                                       │                     │
│  │ ### 📌 Gợi ý điểm vào - ra           │                     │
│  │ Long: Vào $108,000-$108,500          │                     │
│  │ TP1: $109,600, TP2: $111,000         │                     │
│  │ SL: Dưới $107,000                    │                     │
│  └──────────────────────────────────────┘                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                         USER OUTPUT                             │
│                                                                 │
│  Professional Vietnamese Report with:                           │
│  ✅ Multi-timeframe analysis (4H, 1D, 1W)                      │
│  ✅ Probability-based scenarios                                │
│  ✅ Specific entry/TP/SL                                       │
│  ✅ Summary table                                              │
│  ✅ Trader-type recommendations                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Multi-Timeframe Flow

```
User: "Phân tích BTC toàn diện"
│
↓
┌─────────────────────────────────────────────────────────────────┐
│ PLANNER: Detects MULTI-TIMEFRAME request                       │
└──┬────────────────┬────────────────┬──────────────────────────┘
   │                │                │
   ↓                ↓                ↓
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Task 1   │  │ Task 2   │  │ Task 3   │  (PARALLEL)
│ Get 1h   │  │ Get 1d   │  │ Get 1w   │
│ data     │  │ data     │  │ data     │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     ↓             ↓             ↓
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Database │  │ Database │  │ Database │
│ hours    │  │ days     │  │ weeks    │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────────┴─────────────┘
                   │
                   ↓ (Loop back to Planner)
                   │
     ┌─────────────┴─────────────┐
     │                           │
     ↓                           ↓
┌──────────┐              ┌──────────┐
│ Task 4   │              │ Task 5   │  (PARALLEL)
│ Analyze  │              │ Research │
│ 1h data  │              │ Multi-   │
│          │              │ horizon  │
└────┬─────┘              └────┬─────┘
     │                           │
     ↓                           ↓
┌──────────┐              ┌──────────┐
│ Analysis │              │ Research │
│ SHORT    │              │ Filtered │
└────┬─────┘              └────┬─────┘
     │                           │
     ↓                           │
┌──────────┐                     │
│ Task 6   │                     │
│ Analyze  │                     │
│ 1d data  │                     │
└────┬─────┘                     │
     │                           │
     ↓                           │
┌──────────┐                     │
│ Analysis │                     │
│ MEDIUM   │                     │
└────┬─────┘                     │
     │                           │
     ↓                           │
┌──────────┐                     │
│ Task 7   │                     │
│ Analyze  │                     │
│ 1w data  │                     │
└────┬─────┘                     │
     │                           │
     ↓                           │
┌──────────┐                     │
│ Analysis │                     │
│ LONG     │                     │
└────┬─────┘                     │
     │                           │
     └───────────────┬───────────┘
                     │
                     ↓ (Loop back to Planner)
                     │
                     ↓
               ┌──────────┐
               │ Task 8   │
               │ Generate │
               │ Multi-TF │
               │ Report   │
               └────┬─────┘
                    │
                    ↓
               ┌──────────┐
               │ Report   │
               │ 3 Sections│
               │ + Synth  │
               └────┬─────┘
                    │
                    ↓
            USER RECEIVES:
            ┌────────────────┐
            │ ## 4H Analysis │
            │ ## 1D Analysis │
            │ ## 1W Analysis │
            │ ## Summary     │
            └────────────────┘
```

---

## 🎯 Information Relevance Flow

```
Research Agent receives task:
"Search BTC news for SHORT-TERM trading"
│
↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Extract Requirements                                   │
│ ┌─────────────────────────────────┐                            │
│ │ Time Horizon: SHORT-TERM        │                            │
│ │ Recency: Last 1-3 days          │                            │
│ │ News Relevance Window: 3 days   │                            │
│ └─────────────────────────────────┘                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Search Web                                             │
│ Query: "Bitcoin BTC news today"                                │
│                                                                 │
│ Results:                                                        │
│ ┌─────────────────────────────────┐                            │
│ │ 1. BTC breaks $110K (6h ago)    │                            │
│ │ 2. Whale moves 10K BTC (18h)    │                            │
│ │ 3. ETF approved (1 month ago)   │                            │
│ │ 4. Halving analysis (3 weeks)   │                            │
│ │ 5. Regulation change (2 months) │                            │
│ └─────────────────────────────────┘                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Evaluate Each Item                                     │
│                                                                 │
│ Item 1: BTC breaks $110K (6h ago)                              │
│ ┌─────────────────────────────────┐                            │
│ │ Age: 6 hours ✅                 │                            │
│ │ vs Requirement: <3 days ✅      │                            │
│ │ Impact: Immediate (hours) ✅    │                            │
│ │ Timeframe match: SHORT ✅       │                            │
│ │ RELEVANCE: 10/10 → SIGNAL ✅    │                            │
│ └─────────────────────────────────┘                            │
│                                                                 │
│ Item 2: Whale moves 10K BTC (18h ago)                          │
│ ┌─────────────────────────────────┐                            │
│ │ Age: 18 hours ✅                │                            │
│ │ vs Requirement: <3 days ✅      │                            │
│ │ Impact: 24-48h ✅               │                            │
│ │ Timeframe match: SHORT ✅       │                            │
│ │ RELEVANCE: 8/10 → SIGNAL ✅     │                            │
│ └─────────────────────────────────┘                            │
│                                                                 │
│ Item 3: ETF approved (1 month ago)                             │
│ ┌─────────────────────────────────┐                            │
│ │ Age: 1 month ❌                  │                            │
│ │ vs Requirement: <3 days ❌       │                            │
│ │ Impact: Long-term (priced in) ❌│                            │
│ │ Timeframe match: LONG ❌        │                            │
│ │ RELEVANCE: 2/10 → NOISE ❌      │                            │
│ │ (Would be 8/10 for LONG-TERM)   │                            │
│ └─────────────────────────────────┘                            │
│                                                                 │
│ Item 4: Halving analysis (3 weeks ago)                         │
│ ┌─────────────────────────────────┐                            │
│ │ Age: 3 weeks ❌                  │                            │
│ │ vs Requirement: <3 days ❌       │                            │
│ │ Impact: Cycle-level ❌          │                            │
│ │ Timeframe match: VERY LONG ❌   │                            │
│ │ RELEVANCE: 1/10 → NOISE ❌      │                            │
│ └─────────────────────────────────┘                            │
│                                                                 │
│ Item 5: Regulation change (2 months ago)                       │
│ ┌─────────────────────────────────┐                            │
│ │ Age: 2 months ❌                 │                            │
│ │ vs Requirement: <3 days ❌       │                            │
│ │ Impact: Fundamental (old) ❌    │                            │
│ │ Timeframe match: LONG ❌        │                            │
│ │ RELEVANCE: 1/10 → NOISE ❌      │                            │
│ └─────────────────────────────────┘                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Categorize & Report                                    │
│                                                                 │
│ HIGH RELEVANCE (≥7/10):                                         │
│ ┌─────────────────────────────────┐                            │
│ │ 1. BTC breakout (10/10)         │                            │
│ │ 2. Whale activity (8/10)        │                            │
│ └─────────────────────────────────┘                            │
│                                                                 │
│ LOW RELEVANCE (<7/10):                                          │
│ ┌─────────────────────────────────┐                            │
│ │ 3. ETF (2/10) - Too old         │                            │
│ │ 4. Halving (1/10) - Wrong TF    │                            │
│ │ 5. Regulation (1/10) - Old      │                            │
│ └─────────────────────────────────┘                            │
│                                                                 │
│ SENTIMENT (Only from HIGH relevance):                          │
│ ┌─────────────────────────────────┐                            │
│ │ Bullish: 2 signals              │                            │
│ │ Neutral: 0                      │                            │
│ │ Bearish: 0                      │                            │
│ │ OVERALL: BULLISH (8/10) ✅      │                            │
│ └─────────────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Comparison: Before vs After

### Before (Generic System)
```
User Query
    ↓
Generic Planner
    ↓
"Get BTC data" (vague)
    ↓
Database: crypto_reports_view (generic)
    ↓
Analysis: MA200 on 1h data (wrong!)
    ↓
Research: All news (unfiltered)
    ↓
Report: Generic format
```

### After (Enhanced System)
```
User Query
    ↓
Enhanced Planner (Time-Horizon Aware)
    ↓
Identify: SHORT-TERM
    ↓
"Get from crypto_kline_hours (1h)" (specific)
    ↓
Database: Correct table + metadata
    ↓
Research: News <3 days + relevance scoring
    ↓
Analysis: RSI,MACD,EMA on 1h (correct!)
    ↓
Planner: Evaluate relevance
    ↓
Report: Vietnamese multi-TF format
```

---

**This architecture ensures every component understands TIME CONTEXT and makes decisions accordingly.**