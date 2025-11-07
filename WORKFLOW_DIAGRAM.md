# Back Testing Workflow - Visual Diagrams

## 1. HIGH-LEVEL ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CRYPTOCURRENCY BACKTESTING SYSTEM                │
└─────────────────────────────────────────────────────────────────────┘

        ┌──────────────────┐
        │  MySQL Database  │
        │  (4H Klines)     │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │  Fetch Data      │
        │  (Analysis +     │
        │   Review Periods)│
        └────────┬─────────┘
                 │
         ┌───────┴──────────┐
         │                  │
         ▼                  ▼
    ┌─────────┐      ┌─────────────┐
    │ Analysis │      │ Review Data │
    │ Period   │      │ (Future)    │
    │ (7 days) │      │ (7 days)    │
    └────┬────┘      └─────────────┘
         │
         ▼
    ┌──────────────────────────┐
    │ Technical Analysis Agent  │ ◄─── Agent 1
    │ (gpt-5-mini)             │
    │ - Support/Resistance      │
    │ - Price Predictions       │
    │ - Entry/Exit Signals      │
    └────────┬─────────────────┘
             │
             ▼
    ┌──────────────────────────┐
    │ Reviewer Agent           │ ◄─── Agent 2
    │ (gpt-5-mini)             │
    │ - Evaluate Predictions   │
    │ - Compare to Actuals     │
    │ - Score Accuracy         │
    └────────┬─────────────────┘
             │
             ▼
    ┌──────────────────────────┐
    │ Final Backtest Report    │
    │ - Analysis Results       │
    │ - Review Results         │
    │ - Cost Tracking          │
    │ - Performance Metrics    │
    └──────────────────────────┘
```

---

## 2. SLIDING WINDOW STRATEGY

```
Timeline: 2025-06-01 ════════════════════════════════════════════ 2025-11-03

Window 1: [Analysis 7d] [Review 7d]
          ├─────────────┤├─────────────┤
          2025-06-01    2025-06-08    2025-06-15
          
          ▼ Stride=3 days ▼
          
Window 2:       [Analysis 7d] [Review 7d]
                ├─────────────┤├─────────────┤
                2025-06-04    2025-06-11    2025-06-18
                
                ▼ Stride=3 days ▼
                
Window 3:             [Analysis 7d] [Review 7d]
                      ├─────────────┤├─────────────┤
                      2025-06-07    2025-06-14    2025-06-21

Note: Stride=3 creates overlaps because:
      - Each window is 14 days (7+7)
      - Sliding by only 3 days means 11-day overlap between windows
      - This maximizes data utilization and increases sample size
```

---

## 3. TWO-PHASE BATCH PROCESSING

```
PHASE 1: TECHNICAL ANALYSIS BATCH
═════════════════════════════════

Step 1: Generate Batch Requests
┌─────────────────────────────────┐
│ generate_batch_requests_file()  │
│                                 │
│ For each sliding window:         │
│ - Create custom_id              │
│ - Add analysis prompt           │
│ - Add market data               │
│ - Package as JSONL              │
└────────────┬────────────────────┘
             │
             ▼
      [batch_tech_requests.jsonl]
      ├─ Window 1: tech analysis request
      ├─ Window 2: tech analysis request
      ├─ Window 3: tech analysis request
      └─ ... (one per window)

Step 2: Preview & Safety Check
┌─────────────────────────────────┐
│ preview_batch_requests()        │
│                                 │
│ - Display sample requests       │
│ - Check for policy violations   │
│ - Estimate token counts         │
│ - Review costs                  │
└─────────────────────────────────┘

Step 3: Submit to OpenAI
┌─────────────────────────────────┐
│ submit_batch_job()              │
│                                 │
│ 1. Upload JSONL file            │
│    └─► Returns file_id          │
│                                 │
│ 2. Create batch job             │
│    └─► Returns batch_id         │
│                                 │
│ 3. Monitor status               │
│    └─► Queued → In Progress     │
│        → Completed              │
└────────────┬────────────────────┘
             │
             ▼ (typically minutes/hours)
      [batch_tech_results.jsonl]
      ├─ Window 1: {model: "gpt-5-mini", message: "...analysis..."}
      ├─ Window 2: {model: "gpt-5-mini", message: "...analysis..."}
      └─ ...

Step 4: Process Results
┌─────────────────────────────────┐
│ process_batch_results()         │
│                                 │
│ - Parse JSONL results           │
│ - Correlate with metadata       │
│ - Extract analysis text         │
│ - Count tokens used             │
│ - Calculate costs               │
└────────────┬────────────────────┘
             │
             ▼
      [tech_analysis_results.json]
      ├─ Window 1: {
      │     "custom_id": "...",
      │     "analysis": "...",
      │     "tokens_used": 1234,
      │     "cost_usd": 0.05
      │   }
      └─ ...


PHASE 2: REVIEW BATCH
═════════════════════

Step 5: Generate Review Batch
┌─────────────────────────────────┐
│ generate_review_batch_from      │
│ _tech_results()                 │
│                                 │
│ For each tech analysis result:  │
│ - Load the analysis from Phase1 │
│ - Fetch actual outcome data     │
│ - Create reviewer prompt        │
│ - Package as JSONL              │
└────────────┬────────────────────┘
             │
             ▼
      [batch_review_requests.jsonl]
      ├─ Window 1: {
      │     "custom_id": "...",
      │     "body": {
      │       "messages": [
      │         "system: evaluate...",
      │         "user: agent predicted X, actual was Y..."
      │       ]
      │     }
      │   }
      └─ ...

Step 6 & 7: Submit & Download
┌─────────────────────────────────┐
│ submit_batch_job()              │
│ (same as Phase 1)               │
│                                 │
│ Returns: [batch_review_results] │
└────────────┬────────────────────┘
             │
             ▼
      [batch_review_results.jsonl]
      ├─ Window 1: {
      │     "custom_id": "...",
      │     "message": {
      │       "content": "Evaluation: agent accuracy 87%..."
      │     }
      │   }
      └─ ...

Step 8: Final Processing
┌─────────────────────────────────┐
│ process_review_results()        │
│                                 │
│ - Load review results           │
│ - Load tech results (Phase 1)   │
│ - Load metadata                 │
│ - Combine all data              │
│ - Create BacktestReport objects │
│ - Calculate total costs         │
│ - Generate final report         │
└────────────┬────────────────────┘
             │
             ▼
      [backtest_report.json]
      ├─ Window 1: {
      │     "analysis_start": "2025-06-01",
      │     "analysis_end": "2025-06-08",
      │     "review_end": "2025-06-15",
      │     "analysis": "...technical analysis...",
      │     "review": "...reviewer evaluation...",
      │     "analysis_input_tokens": 2345,
      │     "analysis_output_tokens": 1234,
      │     "review_input_tokens": 3456,
      │     "review_output_tokens": 2345,
      │     "analysis_cost_usd": 0.05,
      │     "review_cost_usd": 0.08,
      │     "total_cost_usd": 0.13
      │   }
      └─ ... (one per window)
```

---

## 4. DATA FLOW - SINGLE WINDOW EXAMPLE

```
Window: Analysis 2025-06-01 → 2025-06-08, Review 2025-06-08 → 2025-06-15

┌──────────────────────────────────────────────────────────────────┐
│ fetch_backtest_data("2025-06-01", "2025-06-08", "2025-06-15")  │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ├─► Query DB: "SELECT * FROM klines WHERE date BETWEEN 2025-06-01 AND 2025-06-08"
             │   └─► Returns: 4H candlestick data for agent to analyze
             │
             └─► Query DB: "SELECT * FROM klines WHERE date BETWEEN 2025-06-08 AND 2025-06-15"
                 └─► Returns: Actual price movement (for evaluation)

┌──────────────────────────────────────────────────────────────────┐
│ Technical Analysis Agent Prompt                                  │
├──────────────────────────────────────────────────────────────────┤
│ System: "You are a technical analysis expert. Analyze klines...  │
│                                                                  │
│ User: "Analyze BTC from 2025-06-01 to 2025-06-08:              │
│        Date        Open      High      Low      Close  Volume    │
│        2025-06-01  43,200    44,500    42,800   44,200 1.2M      │
│        2025-06-02  44,200    45,600    43,900   45,100 1.5M      │
│        ...                                                       │
│        2025-06-08  45,000    46,200    44,800   45,800 1.3M      │
│                                                                  │
│        What are your predictions for the next week?             │
│        Support/Resistance levels?                                │
│        Entry/Exit signals?                                       │
│                                                                  │
│ Response: "Support at 44,500, Resistance at 46,200.             │
│            Expected movement: 45,800 → 46,500 (bullish break)   │
│            Entry: on close above 46,100                          │
│            Stop: 44,200"                                         │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ Reviewer Agent Prompt                                            │
├──────────────────────────────────────────────────────────────────┤
│ System: "Review and evaluate technical analysis accuracy..."    │
│                                                                  │
│ User: "Agent predicted: 45,800 → 46,500 (bullish)               │
│        Actual outcome: 45,800 → 45,200 (bearish reversal)       │
│                                                                  │
│        Was the prediction accurate?                              │
│        Did they use data correctly?                              │
│        Score: ___/100                                            │
│                                                                  │
│ Response: "Prediction: INCORRECT (opposite direction)            │
│            Accuracy: 25/100                                      │
│            Issues: Missed bearish divergence signal, funding    │
│            rate change of -15%"                                  │
└──────────────────────────────────────────────────────────────────┘

Final Report Entry:
┌──────────────────────────────────────────────────────────────────┐
│ {                                                                │
│   "analysis_start": "2025-06-01",                               │
│   "analysis_end": "2025-06-08",                                 │
│   "review_end": "2025-06-15",                                   │
│   "analysis": "Support at 44,500...",                           │
│   "review": "Prediction: INCORRECT (opposite...)...",           │
│   "analysis_input_tokens": 2,500,                               │
│   "analysis_output_tokens": 1,200,                              │
│   "review_input_tokens": 3,000,                                 │
│   "review_output_tokens": 900,                                  │
│   "total_cost_usd": 0.13,                                       │
│   "status": "completed"                                          │
│ }                                                                │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. BATCH REQUEST FORMAT (JSONL)

```
File: batch_tech_requests.jsonl (one JSON object per line)

Line 1:
{
  "custom_id": "window_20250601_20250608_20250615",
  "method": "POST",
  "url": "/v1/chat/completions",
  "body": {
    "model": "gpt-5-mini",
    "messages": [
      {
        "role": "system",
        "content": "You are a technical analysis expert..."
      },
      {
        "role": "user",
        "content": "Analyze BTC from 2025-06-01 to 2025-06-08:\n[OHLCV DATA HERE]\n..."
      }
    ]
  }
}

Line 2:
{
  "custom_id": "window_20250604_20250611_20250618",
  "method": "POST",
  "url": "/v1/chat/completions",
  "body": { ... }
}

... (one per window)
```

---

## 6. COST ESTIMATION EXAMPLE

```
Full Backtest: 2025-06-01 → 2025-11-03 (155 days)
Parameters: analysis_days=7, review_days=7, stride=3

Window Count: ~48 windows (155 / 3 ≈ 51, minus last incomplete)

Per Window Cost Estimate:
  Technical Analysis:
    Input tokens: ~3,000 (prompt + data)
    Output tokens: ~1,500 (analysis)
    Cost: (3,000 * 0.005 + 1,500 * 0.015) / 1000 = $0.0345
    
  Reviewer:
    Input tokens: ~4,000 (analysis + instructions + actual data)
    Output tokens: ~1,200 (evaluation)
    Cost: (4,000 * 0.005 + 1,200 * 0.015) / 1000 = $0.038
    
  Total per window: $0.0725

Total Backtest Cost: 48 windows × $0.0725 = $3.48

Total Tokens Used:
  Technical Analysis: 48 × (3,000 + 1,500) = 216,000 tokens
  Reviews: 48 × (4,000 + 1,200) = 249,600 tokens
  Combined: 465,600 tokens for entire backtest
```

---

## 7. ERROR HANDLING & RECOVERY

```
Batch Processing Failure Scenarios:

Scenario 1: Batch Job Fails Mid-Process
┌─────────────────────────────────────┐
│ check_batch_status() returns ERROR  │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ download_batch_results()            │
│ (returns partial results)           │
│                                     │
│ Some windows completed:             │
│ ├─ Window 1: SUCCESS                │
│ ├─ Window 2: SUCCESS                │
│ ├─ Window 3: FAILED (timeout)       │
│ └─ Window 4: FAILED (timeout)       │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ extract_partial_results_from        │
│ _exception()                        │
│                                     │
│ - Save completed windows            │
│ - Identify which failed             │
│ - Resubmit only failed windows      │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Retry failed windows in new batch   │
│ Then combine all results            │
└─────────────────────────────────────┘

Scenario 2: Results File Not Found
┌─────────────────────────────────────┐
│ process_batch_results() fails       │
│ (missing metadata file)             │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Try/Catch: Auto-detect metadata     │
│ file location                       │
│                                     │
│ - Check standard locations          │
│ - Use results_file name as hint     │
│ - Create empty metadata if needed   │
└─────────────────────────────────────┘
```

---

## 8. ASYNC EXECUTION (PARALLEL vs SEQUENTIAL)

```
PARALLEL EXECUTION (Faster):
═════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│ entry_point(parallel=True)                                      │
│                                                                 │
│ tasks = [                                                       │
│   run_back_testing(win1),  ─┐                                   │
│   run_back_testing(win2),  ─┼─► await asyncio.gather(tasks)   │
│   run_back_testing(win3),  ─┤                                   │
│   run_back_testing(win4),  ─┘                                   │
│ ]                                                               │
│                                                                 │
│ Execution timeline:                                             │
│ Window 1: ████████████ (2 min)                                 │
│ Window 2:   ████████████ (2 min)                               │
│ Window 3:     ████████████ (2 min)                             │
│ Window 4:       ████████████ (2 min)                           │
│                                                                 │
│ Total time: ~2 min (concurrent)                                │
└─────────────────────────────────────────────────────────────────┘

SEQUENTIAL EXECUTION (Slower but safe):
═════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│ entry_point(parallel=False)                                     │
│                                                                 │
│ for window in windows:                                          │
│   result = await run_back_testing(window)                       │
│                                                                 │
│ Execution timeline:                                             │
│ Window 1: ████████████ (2 min)                                 │
│ Window 2: ████████████ (2 min)                                 │
│ Window 3: ████████████ (2 min)                                 │
│ Window 4: ████████████ (2 min)                                 │
│                                                                 │
│ Total time: ~8 min (sequential)                                │
└─────────────────────────────────────────────────────────────────┘
```

