# Back Testing Notebook - Quick Reference Guide

## Core Concepts at a Glance

### What This Notebook Does
Backtests an AI agent's cryptocurrency trading predictions by:
1. Having an agent analyze historical price data (7 days)
2. Recording its predictions
3. Comparing predictions to actual outcomes (next 7 days)
4. Scoring accuracy using another AI agent (reviewer)
5. Doing this across ~48 overlapping time windows for statistical significance

### The Three Agents
1. **Technical Analysis Agent** - Predicts price movements
2. **Reviewer Agent** - Evaluates prediction accuracy
3. **Trading Agent** - Makes trading recommendations (reference)

All use GPT-5-mini via OpenAI's Batch API

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Analysis period | 7 days |
| Review period | 7 days |
| Window overlap | 11 days (stride=3 slides forward) |
| Total backtest period | 2025-06-01 to 2025-11-03 (155 days) |
| Approximate windows | 48 |
| Input tokens per window | ~3,000 (tech) + 4,000 (review) |
| Output tokens per window | ~1,500 (tech) + 1,200 (review) |
| Cost per window | ~$0.07 |
| Total backtest cost estimate | ~$3.48 |

---

## File Structure

### Generated Files (Tests Directory)
```
tests/
├── batch_tech_requests.jsonl           # Phase 1 input
├── batch_tech_results.jsonl            # Phase 1 output
├── batch_tech_requests_metadata.json   # Phase 1 tracking
├── batch_review_requests.jsonl         # Phase 2 input
├── batch_review_results.jsonl          # Phase 2 output
├── batch_review_requests_metadata.json # Phase 2 tracking
├── tech_analysis_results.json          # Processed Phase 1
└── backtest_report.json                # Final combined report
```

### Analysis Documents (Project Root)
```
├── NOTEBOOK_ANALYSIS.md                # Comprehensive analysis
├── WORKFLOW_DIAGRAM.md                 # Visual diagrams
└── QUICK_REFERENCE.md                  # This file
```

---

## Function Quick Lookup

### Data Retrieval
```python
# Get market data from database
get_latest_price(symbol, timeframe, start_date, end_date)

# Fetch analysis + review data for a window
fetch_backtest_data(analysis_start, analysis_end, review_end)
```

### Window Generation
```python
# Create sliding windows
generate_backtest_windows(start, end, analysis_days=7, review_days=7, stride=3)
```

### Batch Processing - Phase 1 (Technical Analysis)
```python
# Preview batch (safety check)
preview_batch_requests(start_date, end_date, show_full_prompts=False)

# Generate JSONL file
generate_batch_requests_file(start_date, end_date, output_file="batch_tech_requests.jsonl")

# Submit to OpenAI
submit_batch_job("batch_tech_requests.jsonl", "Tech Analysis")

# Monitor status
check_batch_status(batch_id)

# Download results
download_batch_results(batch_id, output_file="batch_tech_results.jsonl")

# Process results
process_batch_results("batch_tech_results.jsonl")
```

### Batch Processing - Phase 2 (Reviews)
```python
# Generate review batch from Phase 1 results
generate_review_batch_from_tech_results("tech_analysis_results.json")

# Submit reviews (same as Phase 1)
submit_batch_job("batch_review_requests.jsonl", "Reviews")

# Final processing (combines both phases)
process_review_results(
    "batch_review_results.jsonl",
    "tech_analysis_results.json"
)
```

### Cost Estimation
```python
# Estimate full backtest cost
estimate_full_backtest_cost(
    start_date="2025-06-01",
    end_date="2025-11-03",
    stride=3
)

# Single window cost
estimate_window_cost(
    analysis_start="2025-06-01",
    analysis_end="2025-06-08",
    review_end="2025-06-15"
)
```

### Direct Execution (Without Batch API)
```python
# Run single window
result = await run_back_testing(
    analysis_start="2025-06-01",
    analysis_end="2025-06-08",
    review_end="2025-06-15"
)

# Run all windows parallel
results = await entry_point()

# Run all windows sequential
results = await execute_full_backtest(parallel=False)
```

---

## Typical Workflow

### Option 1: Using Batch API (Recommended for Large Scale)
```python
# 1. Preview
preview = preview_batch_requests(
    start_date="2025-06-01",
    end_date="2025-11-03",
    show_full_prompts=False
)

# 2. Generate Phase 1
tech_info = generate_batch_requests_file(
    start_date="2025-06-01",
    end_date="2025-11-03",
    output_file="batch_tech_requests.jsonl"
)

# 3. Submit & wait
batch1 = submit_batch_job("batch_tech_requests.jsonl", "Tech Analysis")
# ... wait for completion (check_batch_status)

# 4. Process Phase 1
download_batch_results(batch1['id'], "batch_tech_results.jsonl")
tech_results = process_batch_results("batch_tech_results.jsonl")

# 5. Generate Phase 2
review_info = generate_review_batch_from_tech_results(
    "tech_analysis_results.json"
)

# 6. Submit & wait
batch2 = submit_batch_job("batch_review_requests.jsonl", "Reviews")
# ... wait for completion

# 7. Process Phase 2
download_batch_results(batch2['id'], "batch_review_results.jsonl")
final_reports = process_review_results(
    "batch_review_results.jsonl",
    "tech_analysis_results.json"
)
```

### Option 2: Direct Execution (For Testing)
```python
# Single window test
result = await run_back_testing(
    analysis_start="2025-06-01",
    analysis_end="2025-06-08",
    review_end="2025-06-15"
)

# Full backtest (parallel)
results = await entry_point()

# Full backtest (sequential)
results = await execute_full_backtest(parallel=False)
```

---

## Data Structures

### BacktestReport (Final Output)
```python
{
    "analysis_start": "2025-06-01",
    "analysis_end": "2025-06-08",
    "review_start": "2025-06-08",
    "review_end": "2025-06-15",
    
    "analysis": "...technical analysis text...",
    "review": "...reviewer evaluation text...",
    
    # Token counts
    "analysis_input_tokens": 3000,
    "analysis_output_tokens": 1500,
    "review_input_tokens": 4000,
    "review_output_tokens": 1200,
    
    # Costs in USD
    "analysis_cost_usd": 0.0345,
    "review_cost_usd": 0.038,
    "total_cost_usd": 0.0725,
    
    # Status
    "status": "completed",  # or "failed"
    "error_message": null
}
```

### Batch Request (JSONL Format)
```json
{
  "custom_id": "window_20250601_20250608_20250615",
  "method": "POST",
  "url": "/v1/chat/completions",
  "body": {
    "model": "gpt-5-mini",
    "messages": [
      {"role": "system", "content": "..."},
      {"role": "user", "content": "..."}
    ]
  }
}
```

---

## Important Parameters

### generate_backtest_windows()
- `start_date`: Overall start (e.g., "2025-06-01")
- `end_date`: Overall end (e.g., "2025-11-03")
- `analysis_days`: How many days for agent to analyze (default: 7)
- `review_days`: How many days to check accuracy (default: 7)
- `stride`: Days to slide forward (default: 3)
  - stride=3 creates overlapping windows
  - stride=14 creates non-overlapping windows

### generate_batch_requests_file()
- `output_file`: Where to save JSONL (default: "batch_requests.jsonl")
- `model`: Which model (default: "gpt-5-mini")

### submit_batch_job()
- `input_file`: Path to JSONL file
- `description`: Batch description (for tracking)

---

## Common Issues & Solutions

### Issue: Content Policy Violation
**Solution**: Use `preview_batch_requests(show_full_prompts=True)` to check prompts before submitting

### Issue: Batch Takes Too Long
**Solution**: 
- Batch API is asynchronous, wait with `check_batch_status()`
- Check OpenAI dashboard for queue status
- Typically completes in 5-30 minutes

### Issue: Missing Metadata File
**Solution**: `process_batch_results()` auto-detects metadata file location using JSONL filename

### Issue: Partial Batch Failure
**Solution**: Use `extract_partial_results_from_exception()` to save completed windows and resubmit failed ones

### Issue: High Costs
**Solution**: 
- Use `estimate_full_backtest_cost()` to check before running
- Reduce stride (fewer windows)
- Reduce analysis/review days
- Use cheaper model if acceptable

---

## Environment Requirements

### Imports Needed
```python
import os
import json
import pandas as pd
import numpy as np
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime, timedelta
from openai import OpenAI
from agents import Agent, Runner
```

### Environment Variables
```bash
OPENAI_API_KEY=sk-...  # OpenAI API key
# MySQL credentials loaded from .env
```

### Database Requirements
- MySQL database with kline data
- Tables: klines or similar
- Columns: timestamp, open, high, low, close, volume, funding_rate
- 4H candlestick data (configurable)

---

## Output Files Explained

### backtest_report.json
Main output file containing all results:
- One object per sliding window
- Includes: predictions, reviews, costs, status
- Ready for analysis and visualization

### tech_analysis_results.json
Processed technical analysis from Phase 1:
- Each window's analysis
- Token counts for Phase 1
- Cost for Phase 1

### batch_*_metadata.json
Tracking metadata for batch requests:
- Maps custom_id → window dates
- Used to correlate results with original requests
- Automatically generated by batch functions

---

## Tips & Best Practices

1. **Always Preview First**: Run `preview_batch_requests()` before submitting to catch issues early

2. **Check Costs**: Use `estimate_full_backtest_cost()` before running large batches

3. **Monitor Progress**: Keep OpenAI dashboard open and use `check_batch_status()` regularly

4. **Save Incrementally**: Each function saves output files for resumability

5. **Parallel is Faster**: Use `parallel=True` for direct execution if API rate limits allow

6. **Two-Phase Approach**: Separating tech analysis and reviews allows better error handling

7. **Metadata is Key**: Keep metadata files together with results for correlation

8. **Test First**: Run single window test before full backtest to validate prompts

---

## Performance Metrics to Track

From backtest_report.json, calculate:
```python
# Success rate
success_rate = (completed_windows / total_windows) * 100

# Average prediction accuracy
avg_accuracy = sum(review_scores) / len(review_scores)

# Total cost
total_cost = sum(window['total_cost_usd'] for window in results)

# Total tokens
total_tokens = sum(window['analysis_input_tokens'] + 
                   window['analysis_output_tokens'] +
                   window['review_input_tokens'] +
                   window['review_output_tokens'])
```

---

## Next Steps After Backtest

1. **Load report**: `json.load(open('backtest_report.json'))`
2. **Analyze results**: Extract accuracy scores from review field
3. **Calculate metrics**: Win rate, Sharpe ratio, max drawdown, etc.
4. **Iterate**: Adjust prompts/parameters and retest
5. **Deploy**: Use insights to improve live trading agents

