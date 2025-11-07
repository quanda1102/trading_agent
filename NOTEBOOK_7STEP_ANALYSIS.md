# 7-Step Single Window Backtesting Analysis
## Notebook: tests/new_back_testing.ipynb

---

## 1. OVERVIEW: THE 7-STEP WORKFLOW

The notebook implements a **3-Agent Backtesting System** that follows a 7-step sequential workflow for analyzing single backtesting windows:

```
Window Generation
    ↓
STEP 1: Create TA Batch Requests
    ↓
STEP 2: Submit TA Batch to OpenAI
    ↓
STEP 3: Process TA Results (wait for completion)
    ↓
STEP 4: Create Simulator Batch Requests
    ↓
STEP 5: Submit Simulator Batch to OpenAI
    ↓
STEP 6: Create Reviewer Batch Requests
    ↓
STEP 7: Submit & Process Reviewer Batch
```

---

## 2. THE 7 STEPS DETAILED

### STEP 1: Generate Sliding Windows
**Function:** `generate_sliding_windows()`
- **Input:** Start date, end date, window size (7 days default), slide size (3 days default)
- **Output:** List of BacktestWindow objects with window_id, start_date, end_date
- **Purpose:** Creates overlapping time windows for sequential backtesting
- **Example:** From Oct 1-8, Oct 4-11, Oct 7-14, etc.

```python
class BacktestWindow(BaseModel):
    window_id: int
    start_date: datetime
    end_date: datetime
    analysis_data: Optional[str] = None        # TA predictions (filled in Step 3)
    trades: Optional[List[TradeRecord]] = None # Simulator result (filled in Step 5)
    review: Optional[str] = None               # TA Review result (filled in Step 7)
    actual_market_data: Optional[str] = None   # Actual market outcomes
```

### STEP 2: Create Technical Analysis (TA) Batch Requests
**Function:** `create_ta_batch_requests(windows, symbol="BTCUSDT")`
- **Input:** List of BacktestWindow objects, trading symbol
- **Data Fetched:**
  - 4-hour kline data (OHLCV - Open, High, Low, Close, Volume)
  - Funding rates (compressed with min/max/avg statistics)
  - Open interest (4-hour aggregated)
- **Output:** List of batch request objects in OpenAI Responses API format
- **Processing:** 
  - Converts market data to formatted text using `prepare_market_data_text()`
  - Each request includes TA_AGENT_PROMPT template + market data
  - Custom_id: "ta_window_{window_id}"

**Key Data Sources:**
```python
market_data = fetch_market_data(
    symbol=symbol,
    start_time=window.start_date,
    end_time=window.end_date
)
# Returns: {
#   'kline': DataFrame with 4h OHLCV data,
#   'funding': List of funding rates,
#   'open_interest': List of OI data
# }
```

### STEP 3: Submit and Process TA Batch
**Functions:** `submit_batch()`, `wait_for_batch()`, `download_batch_results()`, `process_ta_results()`
- **Submit:** Sends TA requests to OpenAI Batch API with /v1/responses endpoint
- **Wait:** Polls for completion (checks every 30 seconds)
- **Download:** Retrieves results and saves to JSONL
- **Process:** `process_ta_results(results, windows)` maps results back to windows
  - Extracts TA analysis from each response
  - Updates window.analysis_data with TA predictions
  - Handles errors and missing responses

### STEP 4: Create Simulator Batch Requests
**Function:** `create_simulator_batch_requests(windows, symbol="BTCUSDT", future_days=7)`
- **Input:** Windows with analysis_data populated (from Step 3)
- **Data Fetched:**
  - 1-hour kline data from window.end_date to window.end_date + future_days
  - Used to simulate actual trading after TA prediction window
- **Output:** Batch requests with structured output format
- **Prompt Template:** SIMULATOR_AGENT_PROMPT includes:
  - Window's TA analysis (from Step 3)
  - Future 1-hour price data
  - Instructions to generate TradeRecord objects
- **Structured Output:** Uses TradeSimulationOutput model
  ```python
  class TradeRecord(BaseModel):
      id, entry_time, exit_time, order_type
      entry_price, exit_price, target_price, stop_price
      pnl_expected, pnl_real, deviation
      holding_time_hours, technical_reason, ta_reference
      result, ta_assessment, market_result
      deviation_reason, improvement_note
  ```

### STEP 5: Submit and Process Simulator Batch
**Functions:** `submit_batch()`, `wait_for_batch()`, `download_batch_results()`, `process_simulator_results()`
- **Submit:** Sends Simulator requests to OpenAI Batch API
- **Wait:** Polls for completion
- **Download:** Retrieves results with structured outputs
- **Process:** `process_simulator_results(results, windows)`
  - Parses structured TradeRecord outputs
  - Updates window.trades with list of TradeRecord objects
  - Handles JSON parsing and validation errors

### STEP 6: Create TA Reviewer Batch Requests
**Function:** `create_reviewer_batch_requests(windows, symbol="BTCUSDT", review_days=7)`
- **Input:** Windows with trades populated (from Step 5)
- **Data Fetched:**
  - Actual market data from window.end_date to window.end_date + review_days
  - This is the REAL market outcome after predictions
- **Output:** Batch requests for review phase
- **Prompt Template:** TA_REVIEW_AGENT_PROMPT includes:
  - Original TA analysis
  - Simulated trades (what TA said to do)
  - Actual market outcomes (what really happened)
  - Requests evaluation of TA prediction accuracy
- **Structured Output:** Uses TAReviewOutput model with:
  - Accuracy scores, price direction correctness
  - Volume/OI/Funding analysis evaluation
  - Strengths, weaknesses, market conditions
  - Improvement recommendations

### STEP 7: Submit and Process Reviewer Batch
**Functions:** `submit_batch()`, `wait_for_batch()`, `download_batch_results()`, `process_reviewer_results()`
- **Submit:** Sends Review requests to OpenAI Batch API
- **Wait:** Polls for completion
- **Download:** Retrieves results
- **Process:** `process_reviewer_results(results, windows)`
  - Parses TAReviewOutput structured outputs
  - Updates window.review with TA assessment
  - Evaluates accuracy of TA predictions vs actual market

---

## 3. KEY FUNCTIONS AND THEIR PURPOSES

### Data Fetching Functions

**`fetch_market_data(symbol, start_time, end_time)`**
- Retrieves comprehensive market data from MySQL database
- Returns kline (4h), funding rates, and open interest data
- Used in: TA phase (Step 2) and Review phase (Step 6)

**`fetch_simulator_data(symbol, start_time, end_time)`**
- Retrieves simplified 1-hour kline data (close_time, price only)
- Used in: Simulator phase (Step 4)
- Optimized for simulator performance

### Batch Request Creation Functions

**`create_ta_batch_requests(windows, symbol)`**
- Creates OpenAI Batch API requests for Technical Analysis phase
- Fetches 4h market data for each window
- Formats data with `prepare_market_data_text()`
- Returns list of batch request objects

**`create_simulator_batch_requests(windows, symbol, future_days)`**
- Creates batch requests for Simulator phase
- Uses TA analysis from previous step
- Fetches 1h future data for trading simulation
- Includes structured output schema (TradeSimulationOutput)

**`create_reviewer_batch_requests(windows, symbol, review_days)`**
- Creates batch requests for Review phase
- Includes actual market data (real outcomes)
- Compares predictions vs reality
- Uses TAReviewOutput structured schema

### Batch API Functions

**`create_batch_jsonl(requests, filepath)`**
- Converts request list to JSONL format
- Saves to file for batch submission

**`submit_batch(file, description, endpoint="/v1/responses")`**
- Submits JSONL file to OpenAI Batch API
- Returns batch_id for tracking

**`wait_for_batch(batch_id, check_interval=30)`**
- Polls batch status until completion
- Checks every 30 seconds (configurable)
- Returns batch info when done

**`download_batch_results(batch_info, filepath)`**
- Downloads completed batch results
- Saves to JSONL file
- Returns parsed results list

### Result Processing Functions

**`process_ta_results(results, windows)`**
- Maps TA analysis results back to windows
- Updates window.analysis_data
- Returns updated windows list

**`process_simulator_results(results, windows)`**
- Parses structured TradeRecord outputs
- Updates window.trades with trade list
- Handles validation and error cases
- Returns updated windows list

**`process_reviewer_results(results, windows)`**
- Parses TAReviewOutput structured outputs
- Updates window.review with assessment
- Returns updated windows list

### Data Preparation Functions

**`prepare_market_data_text(data: Dict)`**
- Converts market data dict to formatted text
- Handles klines, funding rates, OI
- Output consumed by TA agent
- Includes summaries and statistics

**`prepare_simulator_data_text(df_future: DataFrame)`**
- Converts 1h kline DataFrame to text format
- Output consumed by Simulator agent

---

## 4. DATA FLOW AND MARKET DATA SOURCES

### Market Data Fetching Strategy

**Database:** MySQL with crypto_data database
**Tables:** Assumed to have kline, funding_rate, and open_interest data

**For TA Analysis (4h timeframe):**
```
Window: 2025-10-01 → 2025-10-08
  ↓
fetch_market_data("eth", 2025-10-01, 2025-10-08)
  ├→ 4h klines (OHLCV) for 7 days
  ├→ Funding rates (compressed: min, max, avg)
  └→ Open interest (4h aggregated)
  ↓
prepare_market_data_text() → formatted string
  ↓
TA Agent receives structured market context
```

**For Simulator (1h timeframe):**
```
Window: 2025-10-01 → 2025-10-08
TA gives signals like: Buy at 2025-10-05 14:00
  ↓
Simulator needs future data: 2025-10-08 → 2025-10-15
  ↓
fetch_simulator_data("eth", 2025-10-08, 2025-10-15)
  ├→ 1h klines (price data only)
  ├→ Efficient for price action simulation
  └→ Used to determine entry/exit prices
  ↓
Simulator Agent simulates trades on this data
```

**For Reviewer (actual market verification):**
```
Actual market data: 2025-10-08 → 2025-10-15
  ↓
fetch_market_data("eth", 2025-10-08, 2025-10-15)
  ├→ Same comprehensive data as TA phase
  ├→ This is the REAL market outcome
  └→ Compare against simulated trades
  ↓
Reviewer Agent evaluates prediction accuracy
```

---

## 5. WORKFLOW STRUCTURE

### Sequential Phases

The 7 steps are organized into 3 sequential phases:

**PHASE 1: Technical Analysis (Steps 1-3)**
- Generate windows with market context
- TA Agent analyzes 4h data, produces signals
- Output: window.analysis_data

**PHASE 2: Trading Simulation (Steps 4-5)**
- Simulator uses TA predictions on future 1h data
- Simulates actual trades with entry/exit prices
- Output: window.trades (list of TradeRecord)

**PHASE 3: Results Review (Steps 6-7)**
- Reviewer compares predicted trades vs actual market
- Evaluates TA prediction accuracy
- Output: window.review (assessment and recommendations)

### Key Design Features

1. **Sliding Windows:** Overlapping 7-day analysis windows
   - Window size: 7 days (default)
   - Slide: 3 days (default)
   - Generates 55 windows for typical test periods

2. **Structured Outputs:** Uses Pydantic models for AI response validation
   - TradeRecord: Individual trade details
   - TradeSimulationOutput: List of trades
   - TAReviewOutput: Accuracy assessment

3. **Batch API Usage:** OpenAI Responses API for efficient processing
   - All requests processed in parallel
   - One batch per phase (TA, Simulator, Reviewer)
   - Significant cost and time savings vs sequential API calls

4. **Error Handling:** Robust result processing
   - Handles missing/failed responses
   - JSON parsing with fallbacks
   - Window tracking throughout workflow

---

## 6. WHAT NEEDS TO BE CONVERTED TO MULTIPLE WINDOWS

### Current Single-Window Implementation (Steps 1-7)

The notebook includes a **manual testing section** (Cells 22-31) that demonstrates the 7-step workflow on a single window:

```python
# STEP 1: Generate Single Window
test_windows = [BacktestWindow(
    window_id=0,
    start_date=datetime(2025, 10, 1, tzinfo=pytz.UTC),
    end_date=datetime(2025, 10, 8, tzinfo=pytz.UTC)
)]

# STEP 2-7: Process single window through all phases
```

### Conversion Requirements for Multiple Windows

#### 1. **Window Generation Loop**
**Current:**
```python
test_windows = [BacktestWindow(...)]  # Single window only
```

**Should become:**
```python
test_windows = generate_sliding_windows(
    start_date=TEST_START,
    end_date=TEST_END,
    window_size_days=7,
    slide_days=3
)  # Multiple overlapping windows
```

#### 2. **Batch Request Creation**
**Already supports multiple windows:**
- `create_ta_batch_requests(test_windows)` → processes all windows
- `create_simulator_batch_requests(test_windows)` → processes all windows
- `create_reviewer_batch_requests(test_windows)` → processes all windows
- No changes needed - already designed for N windows

#### 3. **Batch Submission**
**Already handles multiple requests in single batch:**
```python
ta_requests = create_ta_batch_requests(test_windows)
# If 55 windows: creates 55 requests in single batch
ta_batch_id = submit_batch(ta_file)
# OpenAI processes all 55 in parallel
```
- No changes needed - batch API naturally parallelizes

#### 4. **Result Processing**
**Already maps results back to windows:**
```python
test_windows = process_ta_results(ta_results, test_windows)
# Updates each window's analysis_data from corresponding result
```
- No changes needed - uses custom_id mapping (ta_window_{window_id})

#### 5. **Data Storage and Aggregation**
**What needs to be added:**
```python
# After all 3 phases complete:
all_results = []
for window in test_windows:
    all_results.append({
        'window_id': window.window_id,
        'period': f"{window.start_date} to {window.end_date}",
        'ta_analysis': window.analysis_data,
        'trades': window.trades,
        'review': window.review,
        'actual_market_data': window.actual_market_data
    })

# Save comprehensive results
save_backtest_results(all_results, output_dir)
```

#### 6. **Results Analysis and Reporting**
**What needs to be added:**
```python
# Aggregate statistics across windows
def calculate_backtest_statistics(windows: List[BacktestWindow]):
    total_trades = sum(len(w.trades) for w in windows if w.trades)
    total_wins = sum(
        1 for w in windows if w.trades
        for t in w.trades
        if _get(t, 'result') == 'Lãi'
    )
    win_rate = total_wins / total_trades if total_trades > 0 else 0
    
    avg_accuracy = sum(
        w.review.accuracy_score for w in windows if w.review
    ) / len([w for w in windows if w.review])
    
    return {
        'total_windows': len(windows),
        'total_trades': total_trades,
        'win_rate': win_rate,
        'avg_accuracy': avg_accuracy,
        'trades_per_window': total_trades / len(windows)
    }
```

#### 7. **Progress Tracking**
**What needs to be added:**
```python
# Track progress across phases
print(f"Phase 1: Processing {len(test_windows)} windows")
print(f"  ✓ TA batch completed - {sum(1 for w in test_windows if w.analysis_data)} windows with analysis")

print(f"Phase 2: Processing {len(test_windows)} windows")
print(f"  ✓ Simulator batch completed - {sum(1 for w in test_windows if w.trades)} windows with trades")
print(f"  ✓ Total trades generated: {sum(len(w.trades) for w in test_windows if w.trades)}")

print(f"Phase 3: Processing {len(test_windows)} windows")
print(f"  ✓ Reviewer batch completed - {sum(1 for w in test_windows if w.review)} windows reviewed")
```

#### 8. **Main Execution Function**
**Already exists but needs to be used:**
```python
def run_3_agent_backtest(
    start_date: datetime,
    end_date: datetime,
    symbol: str = "eth",
    window_size_days: int = 7,
    slide_days: int = 3,
    output_dir: str = "./backtest_results"
) -> List["BacktestWindow"]:
    """
    Run complete 3-agent backtesting workflow using Batch API
    - Automatically generates sliding windows
    - Processes all windows through all 3 phases
    - Returns all windows with results
    """
    # This function orchestrates the entire multi-window workflow
```

### Summary of Conversion

**What's already multi-window ready:**
- Window generation logic
- Batch request creation (processes N windows)
- Batch submission (handles all N requests in parallel)
- Result mapping (uses custom_id to track back to windows)
- Data structures (BacktestWindow holds all results)

**What needs to be added:**
- Call `generate_sliding_windows()` instead of hardcoding single window
- Loop through phases with all windows at once
- Aggregate and report statistics across all windows
- Save comprehensive multi-window results
- Add progress tracking and logging

**Current approach (single window in manual testing):**
```
For each step (1-7):
  ▪ Create request
  ▪ Submit batch
  ▪ Wait for completion
  ▪ Process results
  ▪ Display output
```

**Target approach (multiple windows):**
```
Generate N windows
Loop through 3 phases:
  ▪ Phase 1: Create all TA requests → 1 batch → process all results
  ▪ Phase 2: Create all SIM requests → 1 batch → process all results
  ▪ Phase 3: Create all REVIEW requests → 1 batch → process all results
Aggregate statistics across all N windows
Generate comprehensive report
```

---

## 7. KEY TECHNICAL DETAILS

### Agent Prompts Used

1. **TA_AGENT_PROMPT:** 
   - Vietnamese instructions for technical analysis
   - Expects 4h kline analysis
   - Output: Text analysis with signals and price targets

2. **SIMULATOR_AGENT_PROMPT:**
   - Takes TA analysis as input
   - Receives future 1h price data
   - Output: Structured TradeRecord list

3. **TA_REVIEW_AGENT_PROMPT:**
   - Takes both predictions and actual market data
   - Compares what TA said vs what actually happened
   - Output: Structured TAReviewOutput with accuracy metrics

### Database Connection
```python
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "crypto_data"),
        connection_timeout=5
    )
```

### Time Zone Handling
- All analysis uses **Vietnam Time (UTC+7)**
- Market data stored in UTC but displayed in UTC+7
- 4h candles align to: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 (UTC+7)

### Performance Considerations
- Uses Batch API for cost efficiency (50% cheaper than standard API)
- Parallel processing of all windows in each phase
- Single batch per phase can contain hundreds of requests
- Check interval: 30 seconds (configurable)

---

## 8. FILE STRUCTURE IN OUTPUT DIRECTORY

For each backtest run:
```
./test_single_window/
├── batch_ta_requests.jsonl        # TA phase requests
├── batch_ta_results.jsonl         # TA phase results
├── batch_sim_requests.jsonl       # Simulator phase requests
├── batch_sim_results.jsonl        # Simulator phase results
├── batch_review_requests.jsonl    # Review phase requests
├── batch_review_results.jsonl     # Review phase results
└── final_results.json             # Aggregated results with all window data
```

---

## CONCLUSION

The notebook implements a sophisticated 7-step backtesting workflow that:

1. **Analyzes market data** with AI technical analysis agent
2. **Simulates trades** based on analysis with structured outputs
3. **Reviews accuracy** by comparing predictions to actual market outcomes

The system is **already designed for multiple windows** - the infrastructure handles N windows in parallel through the Batch API. The main conversion from single-window testing to multi-window production is simply:

```python
# Change from:
test_windows = [BacktestWindow(...)]

# To:
test_windows = generate_sliding_windows(TEST_START, TEST_END)

# Everything else (Steps 2-7) already works for multiple windows!
```

