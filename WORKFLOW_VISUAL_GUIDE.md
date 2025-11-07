# Visual Workflow Guide: 7-Step Backtesting System

## Overall Architecture Diagram

```
INPUT DATA
    |
    v
┌─────────────────────────────────────────────────────────────┐
│ SLIDING WINDOWS GENERATION                                  │
│ (Window size: 7 days, Slide: 3 days)                         │
│                                                              │
│ Window 0: Oct 1-8    │  Window 1: Oct 4-11  │  Window 2: Oct 7-14 ... │
└─────────────────────────────────────────────────────────────┘
    |
    v
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 1: TECHNICAL ANALYSIS (Steps 1-3)                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ STEP 1: Fetch 4h Market Data                                    │
│ ├─ OHLCV (Open, High, Low, Close, Volume)                      │
│ ├─ Funding Rates (min, max, avg)                               │
│ └─ Open Interest (4h aggregated)                               │
│       │                                                         │
│       v                                                         │
│ STEP 2: Create TA Batch Requests                               │
│ ├─ Format market data with prepare_market_data_text()         │
│ ├─ Add TA_AGENT_PROMPT template                               │
│ └─ Create one request per window                              │
│       │                                                         │
│       v                                                         │
│ STEP 3: Submit & Process TA Batch                              │
│ ├─ submit_batch(ta_file) → returns batch_id                    │
│ ├─ wait_for_batch(batch_id) → polls every 30s                 │
│ ├─ download_batch_results() → saves to JSONL                  │
│ └─ process_ta_results() → updates window.analysis_data        │
│       │                                                         │
│       v                                                         │
│ OUTPUT: window.analysis_data (TA predictions & signals)        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
    |
    v
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 2: TRADING SIMULATION (Steps 4-5)                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ STEP 4: Fetch 1h Future Market Data                             │
│ ├─ Range: window.end_date to window.end_date + 7 days        │
│ ├─ Data: 1h klines (time + price only)                        │
│ └─ Used to simulate trades post-prediction window             │
│       │                                                         │
│       v                                                         │
│ STEP 4 (cont): Create Simulator Batch Requests                 │
│ ├─ Include window.analysis_data from Phase 1                   │
│ ├─ Include 1h future price data                                │
│ ├─ Add SIMULATOR_AGENT_PROMPT template                         │
│ ├─ Specify TradeSimulationOutput structured schema            │
│ └─ Create one request per window                              │
│       │                                                         │
│       v                                                         │
│ STEP 5: Submit & Process Simulator Batch                        │
│ ├─ submit_batch(sim_file) → returns batch_id                   │
│ ├─ wait_for_batch(batch_id) → polls every 30s                 │
│ ├─ download_batch_results() → saves structured outputs        │
│ └─ process_simulator_results() → parses TradeRecord list      │
│       │                                                         │
│       v                                                         │
│ OUTPUT: window.trades (list of TradeRecord with entry/exit)   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
    |
    v
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 3: RESULTS REVIEW (Steps 6-7)                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ STEP 6: Fetch Actual Market Data for Review                     │
│ ├─ Range: window.end_date to window.end_date + 7 days        │
│ ├─ Data: Comprehensive 4h market data                         │
│ └─ This is the REAL market outcome after predictions          │
│       │                                                         │
│       v                                                         │
│ STEP 6 (cont): Create Reviewer Batch Requests                  │
│ ├─ Include original window.analysis_data                       │
│ ├─ Include simulated window.trades                             │
│ ├─ Include actual market data (real outcomes)                  │
│ ├─ Add TA_REVIEW_AGENT_PROMPT template                         │
│ ├─ Specify TAReviewOutput structured schema                    │
│ └─ Create one request per window                              │
│       │                                                         │
│       v                                                         │
│ STEP 7: Submit & Process Reviewer Batch                         │
│ ├─ submit_batch(review_file) → returns batch_id                │
│ ├─ wait_for_batch(batch_id) → polls every 30s                 │
│ ├─ download_batch_results() → saves structured outputs        │
│ └─ process_reviewer_results() → parses TAReviewOutput         │
│       │                                                         │
│       v                                                         │
│ OUTPUT: window.review (accuracy assessment & recommendations)  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
    |
    v
FINAL RESULTS
├─ All windows with complete data:
│  ├─ window.analysis_data (TA predictions)
│  ├─ window.trades (simulated trades)
│  ├─ window.review (accuracy assessment)
│  └─ window.actual_market_data (real outcomes)
└─ Saved to: final_results.json
```

---

## Data Flow by Phase

### Phase 1: Technical Analysis

```
┌────────────────────────────────────┐
│ WINDOW DATA                         │
│ ├─ window_id: 0                    │
│ ├─ start_date: 2025-10-01         │
│ └─ end_date: 2025-10-08           │
└──────────────────┬─────────────────┘
                   │
                   v
┌────────────────────────────────────────────────┐
│ fetch_market_data()                            │
│ Returns:                                        │
│ {                                              │
│   'kline': DataFrame                          │
│     └─ 4h OHLCV for 7 days                   │
│   'funding': List of funding rates            │
│   'open_interest': List of OI data            │
│ }                                              │
└──────────────────┬─────────────────────────────┘
                   │
                   v
┌────────────────────────────────────────────────┐
│ prepare_market_data_text()                     │
│                                                 │
│ Converts to:                                   │
│ "Khung 4h gần nhất:                           │
│  - Giá: 2500 USDT                            │
│  - Volume: 1.5M                               │
│  - OI: 5.2B                                   │
│  - Funding: 0.015% (avg)"                    │
└──────────────────┬─────────────────────────────┘
                   │
                   v
┌────────────────────────────────────────────────┐
│ create_ta_batch_requests()                     │
│                                                 │
│ Creates request:                               │
│ {                                              │
│   "custom_id": "ta_window_0",                │
│   "method": "POST",                           │
│   "url": "/v1/responses",                     │
│   "body": {                                    │
│     "model": "gpt-4-turbo",                   │
│     "input": [                                │
│       {                                        │
│         "role": "system",                     │
│         "content": TA_AGENT_PROMPT            │
│       },                                       │
│       {                                        │
│         "role": "user",                       │
│         "content": "prepared_market_data"    │
│       }                                        │
│     ]                                          │
│   }                                            │
│ }                                              │
└──────────────────┬─────────────────────────────┘
                   │
                   v
            BATCH API
         (1 batch per phase)
          (multiple requests)
                   │
                   v
┌────────────────────────────────────────────────┐
│ TA Agent Response:                             │
│                                                 │
│ "## Phân tích kỹ thuật ETH                    │
│  1. Xu hướng: Uptrend trên 4h                │
│  2. Mức kháng cự: 2550                       │
│  3. Mức hỗ trợ: 2480                         │
│  4. Tín hiệu: Mua tại breakout 2550         │
│  5. Mục tiêu: 2620                           │
│  6. Stop Loss: 2450"                         │
└──────────────────┬─────────────────────────────┘
                   │
                   v
┌────────────────────────────────────────────────┐
│ process_ta_results()                           │
│                                                 │
│ Maps: custom_id → window_id → window          │
│ Updates: window.analysis_data = response      │
└──────────────────┬─────────────────────────────┘
                   │
                   v
┌────────────────────────────────────────────────┐
│ UPDATED WINDOW                                 │
│ ├─ window_id: 0                               │
│ ├─ start_date: 2025-10-01                    │
│ ├─ end_date: 2025-10-08                      │
│ └─ analysis_data: "## Phân tích kỹ thuật..." │
└────────────────────────────────────────────────┘
```

### Phase 2: Simulator (Abbreviated)

```
┌────────────────────────────────────────────────┐
│ WINDOW WITH TA ANALYSIS                        │
│ └─ analysis_data: "TA predictions..."         │
└──────────────────┬─────────────────────────────┘
                   │
                   v
        fetch_simulator_data()
    (1h data: 2025-10-08 to 2025-10-15)
                   │
                   v
        create_simulator_batch_requests()
   (include TA analysis + 1h future data)
                   │
                   v
            BATCH API
                   │
                   v
    Simulator Agent: "Mua tại 2525, bán tại 2580"
                   │
                   v
      process_simulator_results()
    (Parse TradeRecord structured output)
                   │
                   v
┌────────────────────────────────────────────────┐
│ UPDATED WINDOW                                 │
│ ├─ analysis_data: "TA predictions..."        │
│ └─ trades: [                                  │
│     {                                          │
│       "id": 1,                                │
│       "entry_time": "2025-10-08 14:00",      │
│       "exit_time": "2025-10-10 09:00",       │
│       "entry_price": 2525,                   │
│       "exit_price": 2580,                    │
│       "pnl_real": 2.18,                      │
│       "result": "Lãi"                        │
│     }                                          │
│   ]                                            │
└────────────────────────────────────────────────┘
```

### Phase 3: Reviewer (Abbreviated)

```
┌────────────────────────────────────────────────┐
│ WINDOW WITH TRADES                             │
│ ├─ analysis_data: "TA predictions..."        │
│ └─ trades: [simulated trades...]             │
└──────────────────┬─────────────────────────────┘
                   │
                   v
     fetch_market_data() for actual market
   (2025-10-08 to 2025-10-15 real outcomes)
                   │
                   v
    create_reviewer_batch_requests()
  (include TA, trades, actual market data)
                   │
                   v
            BATCH API
                   │
                   v
    Reviewer Agent: Compare predictions vs reality
                   │
                   v
   process_reviewer_results()
  (Parse TAReviewOutput structured output)
                   │
                   v
┌────────────────────────────────────────────────┐
│ FINAL UPDATED WINDOW                           │
│ ├─ analysis_data: "TA predictions..."        │
│ ├─ trades: [simulated trades...]             │
│ └─ review: {                                 │
│     "accuracy_score": 8.5,                   │
│     "strengths": "Correctly identified...",  │
│     "weaknesses": "Missed momentum...",      │
│     "ta_improvements": "Use RSI divergence" │
│   }                                            │
└────────────────────────────────────────────────┘
```

---

## Single Window vs Multiple Windows Comparison

### Single Window (Current Testing)

```
ITERATION 1 (Manual steps 1-7 per window)
│
├─ Generate 1 window: Oct 1-8
│  └─ Create TA request → Submit → Wait → Process
│  └─ Create SIM request → Submit → Wait → Process  
│  └─ Create REVIEW request → Submit → Wait → Process
│
└─ Output: 1 window with complete results
```

### Multiple Windows (Target Production)

```
ITERATION 1 (All windows in parallel batches)
│
├─ Generate 55 windows: Oct 1-8, Oct 4-11, Oct 7-14, ...
│
├─ PHASE 1: TA Analysis
│  ├─ Create 55 TA requests
│  ├─ 1 batch submission with all 55 requests
│  ├─ Wait for completion (one time)
│  └─ Process all 55 results simultaneously
│
├─ PHASE 2: Simulator
│  ├─ Create 55 SIM requests
│  ├─ 1 batch submission with all 55 requests
│  ├─ Wait for completion (one time)
│  └─ Process all 55 results simultaneously
│
├─ PHASE 3: Reviewer
│  ├─ Create 55 REVIEW requests
│  ├─ 1 batch submission with all 55 requests
│  ├─ Wait for completion (one time)
│  └─ Process all 55 results simultaneously
│
└─ Aggregate & Report: 55 windows with complete results
```

---

## Batch API Request Structure

```
batch_ta_requests.jsonl
├─ Request 0: {"custom_id": "ta_window_0", "body": {...}}
├─ Request 1: {"custom_id": "ta_window_1", "body": {...}}
├─ ...
└─ Request 54: {"custom_id": "ta_window_54", "body": {...}}
                    │
                    v
            SINGLE BATCH SUBMISSION
            submit_batch(file)
                    │
                    v
            OpenAI Batch API
        (Processes all in parallel)
                    │
                    v
            batch_ta_results.jsonl
            ├─ Result 0: {custom_id: "ta_window_0", body: {response: "..."}}
            ├─ Result 1: {custom_id: "ta_window_1", body: {response: "..."}}
            ├─ ...
            └─ Result 54: {custom_id: "ta_window_54", body: {response: "..."}}
                    │
                    v
            process_ta_results()
            (Maps back to windows using custom_id)
```

---

## Data Structure Evolution Through Workflow

### Initial State (After Window Generation)

```python
windows = [
    BacktestWindow(
        window_id=0,
        start_date=datetime(2025, 10, 1),
        end_date=datetime(2025, 10, 8),
        analysis_data=None,
        trades=None,
        review=None,
        actual_market_data=None
    ),
    # ... 54 more windows
]
```

### After Phase 1 (TA Analysis)

```python
windows = [
    BacktestWindow(
        window_id=0,
        start_date=datetime(2025, 10, 1),
        end_date=datetime(2025, 10, 8),
        analysis_data="## Phân tích kỹ thuật ETH\n1. Xu hướng: Uptrend...",
        trades=None,
        review=None,
        actual_market_data=None
    ),
    # ... 54 more with analysis_data populated
]
```

### After Phase 2 (Simulator)

```python
windows = [
    BacktestWindow(
        window_id=0,
        start_date=datetime(2025, 10, 1),
        end_date=datetime(2025, 10, 8),
        analysis_data="## Phân tích kỹ thuật ETH...",
        trades=[
            TradeRecord(
                id=1,
                entry_time=datetime(2025, 10, 5, 14),
                exit_time=datetime(2025, 10, 7, 9),
                order_type="Long",
                entry_price=2525.5,
                exit_price=2580.0,
                pnl_real=2.18,
                result="Lãi"
            ),
            # ... more trades
        ],
        review=None,
        actual_market_data=None
    ),
    # ... 54 more with trades populated
]
```

### After Phase 3 (Reviewer) - FINAL

```python
windows = [
    BacktestWindow(
        window_id=0,
        start_date=datetime(2025, 10, 1),
        end_date=datetime(2025, 10, 8),
        analysis_data="## Phân tích kỹ thuật ETH...",
        trades=[
            TradeRecord(...),
            # ... list of trades
        ],
        review={
            "accuracy_score": 8.5,
            "prediction_alignment": "Good",
            "price_direction_correct": True,
            "strengths": "Correctly identified support/resistance levels...",
            "weaknesses": "Missed volume divergence signal...",
            "ta_improvements": "Incorporate RSI divergence analysis...",
            "overall_assessment": "TA analysis was mostly accurate..."
        },
        actual_market_data="Khung 4h: Giá đi lên từ 2480 lên 2590..."
    ),
    # ... 54 more with complete data
]
```

---

## Function Call Sequence

### For Single Window (Manual Testing)

```
1. generate_sliding_windows() → [1 window]
2. create_ta_batch_requests([window]) → [1 request]
3. submit_batch(requests) → batch_id_1
4. wait_for_batch(batch_id_1) → batch_info
5. process_ta_results(results, windows) → windows updated
6. create_simulator_batch_requests(windows) → [1 request]
7. submit_batch(requests) → batch_id_2
8. wait_for_batch(batch_id_2) → batch_info
9. process_simulator_results(results, windows) → windows updated
10. create_reviewer_batch_requests(windows) → [1 request]
11. submit_batch(requests) → batch_id_3
12. wait_for_batch(batch_id_3) → batch_info
13. process_reviewer_results(results, windows) → windows updated
14. Return windows with complete data
```

### For Multiple Windows (Target)

```
1. generate_sliding_windows() → [55 windows]
2. create_ta_batch_requests(windows) → [55 requests]
3. submit_batch(requests) → batch_id_1
4. wait_for_batch(batch_id_1) → batch_info
5. process_ta_results(results, windows) → all 55 windows updated
6. create_simulator_batch_requests(windows) → [55 requests]
7. submit_batch(requests) → batch_id_2
8. wait_for_batch(batch_id_2) → batch_info
9. process_simulator_results(results, windows) → all 55 windows updated
10. create_reviewer_batch_requests(windows) → [55 requests]
11. submit_batch(requests) → batch_id_3
12. wait_for_batch(batch_id_3) → batch_info
13. process_reviewer_results(results, windows) → all 55 windows updated
14. Calculate statistics across 55 windows
15. Save comprehensive results (55 complete windows)
16. Return windows with complete data
```

---

## Time Flow Illustration

```
ANALYSIS WINDOW          SIMULATOR WINDOW         REVIEW WINDOW
(Historical Data)        (Future Prediction)      (Actual Outcome)

Oct 1 ---- Oct 8         Oct 8 ---- Oct 15        Oct 8 ---- Oct 15
  │         │              │         │              │         │
  └─TA Analysis            └─Predict Trades       └─Verify Results
    (4h candles)           (1h candles)           (4h candles)
    (Signals & Targets)    (Entry/Exit)           (Actual Price Movement)
      │
      └─→ "Buy at 2550"
              │
              └─→ Simulator: Entry @ 2525, Exit @ 2580
                  │
                  └─→ Reviewer: "Exit was too early, could have held for 2650"
```

