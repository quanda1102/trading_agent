# Back Testing Notebook - Comprehensive Analysis

## 1. OVERALL STRUCTURE AND WORKFLOW

### Notebook Overview
- **Total Cells**: 32 code cells + 1 markdown cell
- **Purpose**: Run backtesting on cryptocurrency trading agent predictions using OpenAI's Batch API
- **Key Approach**: Sliding window technique with overlapping time periods

### High-Level Workflow
The notebook implements a **three-agent backtesting system**:
1. **Technical Analysis Agent** - Analyzes historical price data
2. **Reviewer Agent** - Evaluates the accuracy of the technical analysis
3. **Trading Agent** - Makes trading predictions (for reference)

### Data Flow
```
Historical Market Data
    ↓
[7-day analysis window] → Technical Analysis Agent (gpt-5-mini)
    ↓
[7-day review window] → Reviewer Agent evaluates predictions against actual outcomes
    ↓
Generate Final Backtest Report with Performance Metrics & Costs
```

---

## 2. AGENT USAGE

### Agent Configuration
All three agents use the **same model** and execution framework:

```python
Agent(
    name="technical-analysis-agent",
    model="gpt-5-mini",
    instructions=tech_prompt,
)
```

**Agents Implemented**:
1. **Technical Analysis Agent**
   - Analyzes kline data (4H candlesticks)
   - Identifies support/resistance levels
   - Makes price predictions
   - Provides entry/exit signals

2. **Reviewer Agent**
   - Evaluates agent's predictions in hindsight
   - Compares predictions vs actual outcomes
   - Scores accuracy of technical analysis
   - Uses actual post-event data (funding rates, price movements)

3. **Trading Agent**
   - Makes trading recommendations
   - Analyzes market sentiment
   - Suggests position sizing

### Agent Execution
- **Framework**: Uses `Agent` and `Runner` classes from custom `agents` module
- **Async Execution**: All agents run asynchronously via `await Runner.run(agent, prompt)`
- **Parallel Processing**: Multiple windows can execute in parallel for efficiency

---

## 3. BATCH REQUEST HANDLING

### Two-Phase Batch Process

#### Phase 1: Technical Analysis Batch
```
Generate batch JSONL file with:
- One request per backtesting window
- Each request: Technical analysis prompt for specific date range
- Model: gpt-5-mini
- File: batch_tech_requests.jsonl
↓
Submit to OpenAI Batch API
↓
Download results when ready
↓
Save to: tech_analysis_results.json
```

**Key Function**: `generate_batch_requests_file()`
- Takes: Start/end dates, analysis_days=7, review_days=7, stride=3
- Creates sliding windows across date range
- For each window, creates a batch request with:
  - `custom_id`: Unique identifier for tracking
  - `system_prompt`: System instructions
  - `user_prompt`: Technical analysis request with data

#### Phase 2: Review Batch
```
Load tech_analysis_results.json
↓
For each technical analysis result:
- Create reviewer prompt that includes:
  - Agent's technical analysis
  - Actual outcome data from review period
  - Evaluation criteria
↓
Generate batch_review_requests.jsonl
↓
Submit to OpenAI Batch API
↓
Download results → batch_review_results.jsonl
↓
Process and combine with tech results
↓
Output: backtest_report.json (final combined report)
```

**Key Functions**:
- `generate_review_batch_from_tech_results()` - Creates review batch from tech results
- `process_review_results()` - Combines review + tech results into final report

### Batch API Implementation Details

**Request Format** (JSONL):
```json
{
  "custom_id": "window_2025-06-01_2025-06-08_2025-06-15",
  "method": "POST",
  "url": "/v1/chat/completions",
  "body": {
    "model": "gpt-5-mini",
    "messages": [
      {"role": "system", "content": "system_instructions..."},
      {"role": "user", "content": "user_prompt..."}
    ]
  }
}
```

**Key Batch Functions**:
1. `preview_batch_requests()` - Preview what will be sent (safety check)
2. `submit_batch_job()` - Upload JSONL and submit to OpenAI
3. `check_batch_status()` - Monitor job progress
4. `download_batch_results()` - Retrieve completed results
5. `process_batch_results()` - Parse and organize results with metadata

---

## 4. CURRENT IMPLEMENTATION

### Window Generation (Sliding Window Strategy)
```python
def generate_backtest_windows(
    start_date="2025-06-01",
    end_date="2025-11-03",
    analysis_days=7,      # Period agent analyzes
    review_days=7,        # Period to check accuracy
    stride=3              # Days to slide forward
)
```

**Example Windows**:
- Window 1: Analyze 2025-06-01→06-08, Review 06-08→06-15
- Window 2: Analyze 2025-06-04→06-11, Review 06-11→06-18 (slides 3 days)
- Window 3: Analyze 2025-06-07→06-14, Review 06-14→06-21 (slides 3 days)

**Stride=3 creates 11-day overlap** between consecutive windows (7 days + 4 days of next window)

### Data Fetching
```python
def fetch_backtest_data(
    analysis_start, analysis_end, review_end, symbol='btc'
):
    # Fetches OHLCV data for:
    # - Analysis period (agent sees this)
    # - Full period including review (for evaluation)
    # - Future data only (for comparison)
    # Returns: dict with 'analysis_data', 'full_data', etc.
```

**Data Source**: MySQL database with kline data
- Queries: `get_latest_price()` function
- Granularity: 4H candlesticks (configurable)
- Fields: open, high, low, close, volume, funding_rate, etc.

### Core Data Structures
```python
class BacktestReport(BaseModel):
    analysis_start: str
    analysis_end: str
    review_start: str
    review_end: str
    analysis: str              # Agent's technical analysis
    review: str                # Reviewer evaluation
    
    # Cost tracking
    analysis_input_tokens: int
    analysis_output_tokens: int
    review_input_tokens: int
    review_output_tokens: int
    analysis_cost_usd: float
    review_cost_usd: float
    total_cost_usd: float
    
    status: str = "completed"  # completed | failed
    error_message: str = None
```

### Cost Estimation
The notebook includes comprehensive token/cost estimation:
- `count_tokens()` - Estimate prompt tokens
- `estimate_input_tokens()` - Calculate input token count for both agents
- `estimate_output_tokens_from_sample()` - Sample output to estimate output tokens
- `estimate_window_cost()` - Cost for single window
- `estimate_full_backtest_cost()` - Total cost for entire backtest
- `calculate_cost()` - GPT-4o pricing: Input $0.005/1K, Output $0.015/1K

---

## 5. KEY FUNCTIONS AND THEIR PURPOSES

### Data & Window Management
| Function | Purpose |
|----------|---------|
| `get_connection()` | MySQL database connection |
| `get_latest_price()` | Fetch OHLCV data from database |
| `fetch_backtest_data()` | Get data for analysis + review periods |
| `generate_backtest_windows()` | Create sliding windows from date range |
| `DateRangeSplitter` | Utility class for date range chunking |

### Agent Execution (Direct)
| Function | Purpose |
|----------|---------|
| `run_trading_agent()` | Single agent execution (example) |
| `run_back_testing()` | Run one complete backtest window (tech + review) |
| `entry_point()` | Execute all windows in parallel |
| `execute_full_backtest()` | Full pipeline with error handling |

### Batch API Operations
| Function | Purpose |
|----------|---------|
| `preview_batch_requests()` | Preview batch without submitting (safety) |
| `create_batch_request()` | Format single request for batch API |
| `generate_batch_requests_file()` | Create JSONL with all tech analysis requests |
| `submit_batch_job()` | Upload JSONL and submit to OpenAI |
| `check_batch_status()` | Monitor job progress |
| `download_batch_results()` | Retrieve completed results |
| `process_batch_results()` | Parse and organize results |
| `generate_review_batch_from_tech_results()` | Create 2nd batch from tech results |
| `process_review_results()` | Combine and finalize reports |

### Cost Analysis
| Function | Purpose |
|----------|---------|
| `count_tokens()` | Token count using tiktoken |
| `estimate_input_tokens()` | Estimate tokens for both agents |
| `estimate_output_tokens_from_sample()` | Sample output to estimate size |
| `calculate_cost()` | GPT-4o pricing calculation |
| `estimate_window_cost()` | Single window cost |
| `estimate_full_backtest_cost()` | Full backtest cost |
| `run_backtest_with_cost_tracking()` | Execute + track costs |

### Utilities
| Function | Purpose |
|----------|---------|
| `visualize_windows()` | Display window structure |
| `save_progress()` | Save intermediate results |
| `load_existing_results()` | Load cached results |
| `extract_partial_results_from_exception()` | Recover from failures |

---

## 6. EXECUTION EXAMPLES FROM NOTEBOOK

### Example 1: Cost Estimation
```python
cost_estimate = estimate_full_backtest_cost(
    start_date="2025-06-01",
    end_date="2025-11-03",
    analysis_days=7,
    review_days=7,
    stride=3
)
```

### Example 2: Batch Preview
```python
preview = preview_batch_requests(
    start_date="2025-05-13",
    end_date="2025-10-31",
    analysis_days=7,
    review_days=3,
    stride=3,
    show_full_prompts=True,
    max_windows_to_show=5
)
```

### Example 3: Full Batch Workflow
```python
# STEP 1: Preview
preview = preview_batch_requests(...)

# STEP 2: Generate tech analysis batch
tech_info = generate_batch_requests_file(
    start_date="2025-06-01",
    end_date="2025-11-03",
    analysis_days=7,
    review_days=3,
    stride=3,
    output_file="batch_tech_requests.jsonl"
)

# STEP 3: Submit
batch1 = submit_batch_job("batch_tech_requests.jsonl", "Tech Analysis")

# STEP 4: Monitor & Download
# ... check_batch_status(), download_batch_results()

# STEP 5: Process tech results
tech_results = process_batch_results("batch_tech_results.jsonl")

# STEP 6: Generate review batch
review_info = generate_review_batch_from_tech_results(
    "tech_analysis_results.json"
)

# STEP 7: Submit reviews
batch2 = submit_batch_job("batch_review_requests.jsonl", "Reviews")

# STEP 8: Process final results
final_reports = process_review_results(
    "batch_review_results.jsonl",
    "tech_analysis_results.json"
)
```

---

## 7. TECHNICAL DETAILS

### Database Connection
- **Type**: MySQL
- **Data**: OHLCV klines (4H by default)
- **Fields**: timestamp, open, high, low, close, volume, funding_rate

### API Integration
- **Service**: OpenAI
- **Batch API**: For bulk processing
- **Models**: gpt-5-mini
- **Authentication**: OPENAI_API_KEY environment variable

### Batch Processing Flow
1. Generate requests → JSONL file
2. Upload file → Get file_id
3. Create batch job → Get batch_id
4. Poll until completed (typically minutes to hours)
5. Download results → JSONL file
6. Parse results → Python objects
7. Combine with metadata → Final report

### Error Handling
- Partial results recovery if batch fails
- Try/catch for missing files
- Status tracking (completed/failed)
- Error messages in report

---

## 8. KEY INSIGHTS

1. **Two-Phase Batch Architecture**: Separates technical analysis (first batch) from reviews (second batch). This allows reviewing multiple analyses in parallel.

2. **Sliding Windows**: Creates overlapping test periods to maximize data usage and increase sample size for statistical significance.

3. **Cost Awareness**: Includes comprehensive cost estimation before running expensive batches, helping prevent surprise API bills.

4. **Async/Parallel**: Supports both sequential and parallel execution of windows for flexibility.

5. **Metadata Tracking**: Maintains custom_id mapping to track which request corresponds to which window for accurate result correlation.

6. **Hindsight Evaluation**: Unique approach of evaluating agent predictions with knowledge of actual outcomes (backtesting advantage).

---

## 9. FILE DEPENDENCIES

**External Modules**:
- `agents.Agent, Runner` - Custom agent framework
- `openai.OpenAI` - OpenAI API client
- `mysql.connector` - Database connection
- `pydantic.BaseModel` - Data validation

**Files Generated**:
- `batch_tech_requests.jsonl` - Technical analysis batch input
- `batch_tech_results.jsonl` - Technical analysis batch output
- `batch_tech_requests_metadata.json` - Tracking metadata
- `batch_review_requests.jsonl` - Review batch input
- `batch_review_results.jsonl` - Review batch output
- `tech_analysis_results.json` - Processed tech results
- `backtest_report.json` - Final combined report
