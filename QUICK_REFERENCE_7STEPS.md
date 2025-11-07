# Quick Reference: 7-Step Backtesting Workflow

## The 7 Steps at a Glance

| Step | Name | Input | Function | Output | Data Used |
|------|------|-------|----------|--------|-----------|
| 1 | Generate Windows | Dates | `generate_sliding_windows()` | List[BacktestWindow] | Date range |
| 2 | Create TA Requests | Windows | `create_ta_batch_requests()` | List[Request] | 4h market data |
| 3 | Process TA Batch | Requests | `submit_batch() + wait + process_ta_results()` | Windows.analysis_data | TA Agent response |
| 4 | Create SIM Requests | Windows+TA | `create_simulator_batch_requests()` | List[Request] | 1h future data |
| 5 | Process SIM Batch | Requests | `submit_batch() + wait + process_simulator_results()` | Windows.trades | TradeRecord list |
| 6 | Create Review Requests | Windows+Trades | `create_reviewer_batch_requests()` | List[Request] | Actual market data |
| 7 | Process Review Batch | Requests | `submit_batch() + wait + process_reviewer_results()` | Windows.review | TAReviewOutput |

---

## Data Fetching Cheat Sheet

### Step 2: TA Analysis Data
```python
fetch_market_data(symbol, start_time, end_time)
Returns: {
    'kline': DataFrame(4h OHLCV),
    'funding': List of funding rates,
    'open_interest': List of OI data
}
```

### Step 4: Simulator Data
```python
fetch_simulator_data(symbol, future_start, future_end)
Returns: DataFrame(1h close_time, price)
```

### Step 6: Review Data (Actual Market)
```python
fetch_market_data(symbol, review_start, review_end)
Returns: {
    'kline': DataFrame(4h OHLCV for actual market),
    'funding': List of actual funding rates,
    'open_interest': List of actual OI
}
```

---

## Key Data Models

### BacktestWindow
```python
class BacktestWindow(BaseModel):
    window_id: int                              # Unique ID
    start_date: datetime                        # Analysis start
    end_date: datetime                          # Analysis end
    analysis_data: Optional[str] = None         # From Step 3 TA Agent
    trades: Optional[List[TradeRecord]] = None  # From Step 5 Simulator
    review: Optional[str] = None                # From Step 7 Reviewer
    actual_market_data: Optional[str] = None    # From Step 6 fetch
```

### TradeRecord (for Step 5)
```python
class TradeRecord(BaseModel):
    id: int
    entry_time: datetime
    exit_time: datetime
    order_type: str  # "Long" or "Short"
    entry_price: float
    exit_price: float
    target_price: Optional[float]
    stop_price: Optional[float]
    pnl_expected: Optional[float]  # %
    pnl_real: Optional[float]      # %
    result: Optional[str]          # "Lãi" or "Lỗ"
    # ... more fields
```

### TAReviewOutput (for Step 7)
```python
class TAReviewOutput(BaseModel):
    accuracy_score: float          # 0-10
    prediction_alignment: str      # Excellent/Good/Fair/Poor
    price_direction_correct: bool
    strengths: str                 # What TA got right
    weaknesses: str                # What TA missed
    market_conditions: str         # Actual market context
    ta_improvements: str           # How to improve
    overall_assessment: str        # 2-3 paragraph summary
```

---

## Common Function Signatures

### Data Preparation
```python
prepare_market_data_text(data: Dict) -> str
prepare_simulator_data_text(df: DataFrame) -> str
```

### Batch Request Creation
```python
create_ta_batch_requests(windows: List[BacktestWindow], symbol: str) -> List[Dict]
create_simulator_batch_requests(windows: List[BacktestWindow], symbol: str, future_days: int) -> List[Dict]
create_reviewer_batch_requests(windows: List[BacktestWindow], symbol: str, review_days: int) -> List[Dict]
```

### Batch API Operations
```python
create_batch_jsonl(requests: List[Dict], filepath: str) -> str
submit_batch(file: str, description: str, endpoint: str) -> str  # Returns batch_id
wait_for_batch(batch_id: str, check_interval: int) -> BatchInfo
download_batch_results(batch_info: BatchInfo, filepath: str) -> List[Dict]
```

### Result Processing
```python
process_ta_results(results: List[Dict], windows: List[BacktestWindow]) -> List[BacktestWindow]
process_simulator_results(results: List[Dict], windows: List[BacktestWindow]) -> List[BacktestWindow]
process_reviewer_results(results: List[Dict], windows: List[BacktestWindow]) -> List[BacktestWindow]
```

---

## Typical Execution Timeline

### Single Window (Manual Testing)
```
STEP 1-3 (TA Phase):
  ├─ Create request: <1s
  ├─ Submit batch: 5-10s
  ├─ Wait for completion: 2-5 minutes
  └─ Process results: <1s
  Total: ~3-6 minutes

STEP 4-5 (Simulator Phase):
  ├─ Create request: <1s
  ├─ Submit batch: 5-10s
  ├─ Wait for completion: 2-5 minutes
  └─ Process results: <1s
  Total: ~3-6 minutes

STEP 6-7 (Review Phase):
  ├─ Create request: <1s
  ├─ Submit batch: 5-10s
  ├─ Wait for completion: 2-5 minutes
  └─ Process results: <1s
  Total: ~3-6 minutes

GRAND TOTAL: ~10-20 minutes per single window
```

### Multiple Windows (N=55)
```
PHASE 1: Create 55 TA requests → 1 batch → Wait 2-5 min → Process all
PHASE 2: Create 55 SIM requests → 1 batch → Wait 2-5 min → Process all
PHASE 3: Create 55 REVIEW requests → 1 batch → Wait 2-5 min → Process all

GRAND TOTAL: ~10-20 minutes for ALL 55 WINDOWS (vs 550-1100 min if sequential)
Speedup: 50-100x faster!
```

---

## Critical Custom IDs for Tracking

Batch API matches requests to results using custom_id:

```
Phase 1 (TA):
  Request custom_id: "ta_window_0"
  ├─ Results include custom_id: "ta_window_0"
  └─ process_ta_results() maps back to window 0

Phase 2 (Simulator):
  Request custom_id: "sim_window_0"
  ├─ Results include custom_id: "sim_window_0"
  └─ process_simulator_results() maps back to window 0

Phase 3 (Reviewer):
  Request custom_id: "review_window_0"
  ├─ Results include custom_id: "review_window_0"
  └─ process_reviewer_results() maps back to window 0
```

---

## Error Handling Patterns

### Missing TA Analysis
```python
for window in windows:
    if not window.analysis_data:
        print(f"Window {window.window_id}: No TA analysis")
        # Skip simulator phase for this window
        continue
```

### Failed Trades
```python
for window in windows:
    if not window.trades:
        print(f"Window {window.window_id}: Simulator failed")
        # Or: window.trades = []  # Empty list means no trades
```

### JSON Parsing Error
```python
try:
    trades = json.loads(response_text)
except json.JSONDecodeError as e:
    print(f"Window {window_id}: JSON parse error - {e}")
    # Fallback to empty trades list
    window.trades = []
```

---

## Environment Variables Needed

```bash
OPENAI_API_KEY=sk-...
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=...
MYSQL_DATABASE=crypto_data
```

---

## File Operations

### Input Files Generated
- `batch_ta_requests.jsonl` - TA phase requests
- `batch_sim_requests.jsonl` - Simulator phase requests
- `batch_review_requests.jsonl` - Review phase requests

### Output Files Generated
- `batch_ta_results.jsonl` - TA phase results
- `batch_sim_results.jsonl` - Simulator phase results
- `batch_review_results.jsonl` - Review phase results
- `final_results.json` - Aggregated all windows data

---

## Debugging Tips

### Check Batch Status
```python
# After submit_batch()
batch_id = "batch_123..."
batch_info = client.beta.batch.retrieve(batch_id)
print(batch_info.status)  # queued, in_progress, or completed
print(batch_info.request_counts)  # {processed: X, failed: Y}
```

### Inspect Request Format
```python
# Before submit_batch()
import json
with open('batch_ta_requests.jsonl', 'r') as f:
    first_request = json.loads(f.readline())
    print(json.dumps(first_request, indent=2))
```

### Verify Window Updates
```python
# After process_ta_results()
for window in windows:
    print(f"Window {window.window_id}: {bool(window.analysis_data)}")
```

---

## Common Modifications

### Change Window Parameters
```python
windows = generate_sliding_windows(
    start_date=TEST_START,
    end_date=TEST_END,
    window_size_days=14,      # Change from 7 to 14 days
    slide_days=7              # Change from 3 to 7 days
)
```

### Change Simulation Period
```python
sim_requests = create_simulator_batch_requests(
    test_windows,
    symbol=TEST_SYMBOL,
    future_days=14  # Change from 7 to 14 days of simulation
)
```

### Change Trading Symbol
```python
TEST_SYMBOL = "btc"  # Instead of "eth"
ta_requests = create_ta_batch_requests(test_windows, TEST_SYMBOL)
sim_requests = create_simulator_batch_requests(test_windows, TEST_SYMBOL)
review_requests = create_reviewer_batch_requests(test_windows, TEST_SYMBOL)
```

### Change Batch Check Interval
```python
# Default is 30 seconds
ta_batch_info = wait_for_batch(ta_batch_id, check_interval=60)  # Check every 60s
```

---

## Key Insights

### What Already Works for Multiple Windows
- `create_ta_batch_requests()` processes N windows
- `create_simulator_batch_requests()` processes N windows
- `create_reviewer_batch_requests()` processes N windows
- Batch API submission handles all N requests in one call
- Result processing maps back using custom_id (ta_window_0, ta_window_1, ...)

### What Needs to be Added
1. Call `generate_sliding_windows()` instead of single window
2. Aggregate statistics across all N windows
3. Report comprehensive results

### The Magic of Batch API
- Single submission for N requests
- All N processed in parallel
- Still only ~3-5 min total wait time
- Cost: 50% cheaper than standard API
- Perfect for backtesting workflows

---

## Example: Minimal Working Code

```python
# 1. Generate windows
windows = generate_sliding_windows(
    datetime(2025, 10, 1),
    datetime(2025, 10, 31),
    window_size_days=7,
    slide_days=3
)

# 2. Phase 1: TA Analysis
ta_requests = create_ta_batch_requests(windows, "eth")
ta_file = create_batch_jsonl(ta_requests, "batch_ta.jsonl")
ta_id = submit_batch(ta_file, "TA Batch")
ta_info = wait_for_batch(ta_id)
ta_results = download_batch_results(ta_info, "results_ta.jsonl")
windows = process_ta_results(ta_results, windows)

# 3. Phase 2: Simulator
sim_requests = create_simulator_batch_requests(windows, "eth")
sim_file = create_batch_jsonl(sim_requests, "batch_sim.jsonl")
sim_id = submit_batch(sim_file, "Sim Batch")
sim_info = wait_for_batch(sim_id)
sim_results = download_batch_results(sim_info, "results_sim.jsonl")
windows = process_simulator_results(sim_results, windows)

# 4. Phase 3: Reviewer
review_requests = create_reviewer_batch_requests(windows, "eth")
review_file = create_batch_jsonl(review_requests, "batch_review.jsonl")
review_id = submit_batch(review_file, "Review Batch")
review_info = wait_for_batch(review_id)
review_results = download_batch_results(review_info, "results_review.jsonl")
windows = process_reviewer_results(review_results, windows)

# 5. Done! windows now have complete data
print(f"Processed {len(windows)} windows")
```

