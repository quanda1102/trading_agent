# OpenAI Code Interpreter File Proxy Guide

## Overview

The File Proxy system enables your trading agents to generate downloadable files (PDFs, charts, CSV exports, etc.) using OpenAI's Code Interpreter tool and serve them to frontend clients through your own backend.

## Problem Statement

When OpenAI agents use the `CodeInterpreterTool` to generate files, they return sandbox URLs like:

```
[Download report.pdf](sandbox:/mnt/data/report.pdf)
```

These sandbox URLs are not accessible to your frontend users. The File Proxy system solves this by:

1. Extracting file references from agent responses
2. Replacing sandbox URLs with working backend proxy URLs
3. Serving files through your FastAPI backend

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────────┐
│   Frontend  │────────>│  Your API    │────────>│  OpenAI Agent   │
│             │         │  (FastAPI)   │         │  + CodeInterp   │
└─────────────┘         └──────────────┘         └─────────────────┘
                               │                          │
                               │                          │
                               │    ┌─────────────────────┘
                               │    │ sandbox:// links
                               │    │
                               │    ▼
                        ┌──────────────────┐
                        │  File Proxy      │
                        │  - Collect refs  │
                        │  - Replace links │
                        │  - Serve files   │
                        └──────────────────┘
                               │
                               ▼
                        working HTTP URLs
```

## Components

### 1. Utility Module (`trading_agent_tp/utils/file_proxy.py`)

Provides helper functions for processing agent responses:

- `collect_file_refs(response)` - Extract file citations from agent output
- `replace_sandbox_links(text, refs, backend_base)` - Replace sandbox:// URLs
- `extract_text_from_response(response)` - Get text content from response
- `process_agent_response(response, backend_base)` - Complete processing pipeline

### 2. API Endpoints (`trading_agent_tp/api/file_proxy_endpoints.py`)

FastAPI router with endpoints:

- `GET /api/files/download/{container_id}/{file_id}/{filename}` - Download file
- `GET /api/files/health` - Health check

### 3. Example Usage (`examples/file_proxy_example.py`)

Complete examples demonstrating the file proxy system.

## Setup

### 1. Environment Configuration

Add to your `.env` file:

```bash
# Required
OPENAI_API_KEY=sk-proj-...

# Optional - customize the backend URL
FILE_PROXY_BASE_URL=http://localhost:8888/api/files/download
```

### 2. Install Dependencies

The `requests` package is required and already added to `pyproject.toml`:

```bash
# Using uv
uv pip install requests

# Or using pip
pip install requests
```

### 3. Start the Server

```bash
python main.py
```

The file proxy endpoints will be available at:
- Download: `http://localhost:8888/api/files/download/{container_id}/{file_id}/{filename}`
- Health: `http://localhost:8888/api/files/health`

## Usage

### Basic Usage

```python
import asyncio
from agents import Runner, Agent, CodeInterpreterTool
from trading_agent_tp.utils.file_proxy import process_agent_response

# Create agent with Code Interpreter
agent = Agent(
    name="DataAnalyst",
    tools=[CodeInterpreterTool(
        tool_config={"type": "code_interpreter", "container": {"type": "auto"}}
    )],
    instructions="Generate charts and export them as PNG files.",
    model="gpt-4.1-mini",
)

# Run agent
runner = Runner()
result = await runner.run(agent, "Create a trading volume chart as PNG")
response = result.raw_responses[0]

# Process response with file proxy
processed = process_agent_response(response)

# Now processed["text"] contains working download links!
print(processed["text"])
# Output: "Here's your chart: [volume_chart.png](http://localhost:8888/api/files/download/cntr_xyz/cfile_abc/volume_chart.png)"

# Access file references
print(processed["file_refs"])
# Output: [{"file_id": "cfile_abc", "filename": "volume_chart.png", "container_id": "cntr_xyz"}]
```

### Integration with Existing Agents

### ✅ Simple Agent (Fully Implemented)

The simple agent endpoint at `/api/simple/chat` automatically processes file proxies:

```python
# In simple_agent_endpoints.py
agent_result = await runner.run(simple_agent, request.question)

# Extract file references from raw responses
if hasattr(agent_result, 'raw_responses') and agent_result.raw_responses:
    raw_response = agent_result.raw_responses[0]
    file_refs = collect_file_refs(raw_response)

# Replace sandbox links
if file_refs:
    answer = replace_sandbox_links(answer, file_refs)
```

### ⚠️ Multi-Agent Orchestrator (Partial Implementation)

The multi-agent orchestrator at `/api/v1/chat` has basic support but requires enhancement:

**Current Status:**
- Basic regex-based replacement is in place
- Does not yet extract file_refs from individual agent responses

**To fully implement:**
1. Modify `multi_agent_orchestrator.py` to store raw_responses in `agent_results`
2. Extract file_refs from all agent responses (analysis, research, report)
3. Pass refs to `replace_sandbox_links()`

**Example enhancement needed:**

```python
# In multi_agent_orchestrator.py, when storing agent results:
agent_results[agent_type].append({
    "task_id": task_id,
    "result": exec_result["result"],
    "raw_response": agent_response  # ADD THIS
})

# Then in multi_agent_endpoints.py:
all_file_refs = []
for agent_type, results in result.get("agent_results", {}).items():
    if results:
        for agent_result in results:
            if "raw_response" in agent_result:
                refs = collect_file_refs(agent_result["raw_response"])
                all_file_refs.extend(refs)

# Use all_file_refs for replacement
result["final_answer"] = replace_sandbox_links(
    result["final_answer"],
    all_file_refs
)
```

### Manual Processing

For more control, use individual functions:

```python
from trading_agent_tp.utils.file_proxy import (
    collect_file_refs,
    replace_sandbox_links,
    extract_text_from_response
)

# Step 1: Extract text
text = extract_text_from_response(response)

# Step 2: Collect file references
file_refs = collect_file_refs(response)

# Step 3: Replace sandbox links
backend_url = "http://localhost:8888/api/files/download"
final_text = replace_sandbox_links(text, file_refs, backend_url)
```

## Use Cases

### 1. Technical Analysis Charts

```python
agent = Agent(
    name="ChartGenerator",
    tools=[CodeInterpreterTool(...)],
    instructions="Create candlestick charts with indicators (RSI, MACD, etc.)"
)

# Agent generates PNG/PDF charts
# Files are automatically accessible via proxy
```

### 2. Trading Reports

```python
agent = Agent(
    name="ReportGenerator",
    tools=[CodeInterpreterTool(...)],
    instructions="Generate comprehensive PDF trading reports with analysis"
)

# Agent creates PDF reports
# Users can download them directly
```

### 3. Data Exports

```python
agent = Agent(
    name="DataExporter",
    tools=[CodeInterpreterTool(...)],
    instructions="Export trading data to CSV/Excel formats"
)

# Agent exports data files
# Files available for download
```

## API Reference

### Download Endpoint

**GET** `/api/files/download/{container_id}/{file_id}/{filename}`

**Parameters:**
- `container_id` (path) - OpenAI container identifier
- `file_id` (path) - File identifier within container
- `filename` (path) - Desired filename for download

**Response:**
- Status 200: File content with download headers
- Status 404: File not found
- Status 500: API key not configured
- Status 502: Error fetching from OpenAI

**Example:**
```bash
curl http://localhost:8888/api/files/download/cntr_abc123/cfile_xyz789/report.pdf \
  -o report.pdf
```

### Health Check Endpoint

**GET** `/api/files/health`

**Response:**
```json
{
  "service": "file-proxy",
  "status": "healthy",
  "api_key_configured": true,
  "endpoints": {
    "download": "/api/files/download/{container_id}/{file_id}/{filename}",
    "health": "/api/files/health"
  }
}
```

## Troubleshooting

### Issue: API Key Not Configured

**Error:** `OPENAI_API_KEY not configured`

**Solution:**
1. Check `.env` file contains `OPENAI_API_KEY=sk-proj-...`
2. Restart the FastAPI server
3. Verify with health check: `curl http://localhost:8888/api/files/health`

### Issue: File Not Found (404)

**Error:** `Failed to fetch file from OpenAI`

**Possible causes:**
1. Container or file ID is invalid
2. File has expired (OpenAI containers have limited lifetime)
3. API key doesn't have access to the container

**Solution:**
- Check the logs for detailed error messages
- Verify container_id and file_id are correct
- Ensure you're using fresh file references from recent agent runs

### Issue: CORS Errors

**Error:** Browser blocks request due to CORS

**Solution:**
The main app already has CORS configured. If you need custom CORS for specific origins:

```python
# In main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Security Considerations

### 1. API Key Protection

The OpenAI API key is stored securely in environment variables and never exposed to clients.

### 2. File Access Control

Currently, any client can download files if they know the container_id and file_id. For production:

```python
# Add authentication to download endpoint
@router.get("/download/{container_id}/{file_id}/{filename}")
async def download_file(
    container_id: str,
    file_id: str,
    filename: str,
    user: User = Depends(get_current_user)  # Add auth
):
    # Verify user has access to this file
    # ...
```

### 3. Rate Limiting

Consider adding rate limiting for the download endpoint:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/download/...")
@limiter.limit("10/minute")
async def download_file(...):
    # ...
```

## Testing

Run the example file to test the system:

```bash
# Make sure server is running
python main.py

# In another terminal
python examples/file_proxy_example.py
```

## Production Deployment

### 1. Use HTTPS

Always use HTTPS in production:

```bash
FILE_PROXY_BASE_URL=https://api.yourdomain.com/api/files/download
```

### 2. Configure Logging

Adjust logging level for production:

```python
# In file_proxy_endpoints.py
logger.setLevel(logging.WARNING)  # Reduce noise
```

### 3. Add Monitoring

Monitor file download metrics:
- Download count
- File size statistics
- Error rates
- Response times

## Examples

See `examples/file_proxy_example.py` for complete working examples:

1. **Basic Usage** - Simple file generation and proxy
2. **Manual Processing** - Step-by-step processing
3. **Trading Analysis** - Real-world trading scenario with charts

Run examples:

```bash
cd /home/quan-ubuntu/Desktop/projects/trading-agent-tp
python examples/file_proxy_example.py
```

## FAQ

**Q: Can I use this with other file types besides PDF and PNG?**

A: Yes! The system supports any file type. The `_get_content_type()` function handles common types, and falls back to `application/octet-stream` for unknown types.

**Q: How long do files remain accessible?**

A: Files are stored in OpenAI's containers, which have a limited lifetime (typically hours to days). For long-term storage, download and save files to your own storage.

**Q: Can I customize the backend URL?**

A: Yes! Set `FILE_PROXY_BASE_URL` in your `.env` file:
```bash
FILE_PROXY_BASE_URL=https://your-custom-domain.com/files/download
```

**Q: Does this work with streaming responses?**

A: The current implementation works with complete responses. For streaming, you'd need to collect file references after the stream completes.

**Q: Can I integrate this with my existing agents?**

A: Absolutely! Just add `CodeInterpreterTool` to your agent's tools and use the `process_agent_response()` function to handle file outputs.

## Support

For issues or questions:
1. Check the logs in your FastAPI server
2. Verify environment configuration
3. Test with the health check endpoint
4. Run the example file to ensure basic functionality

## References

- [OpenAI Agents API Documentation](https://platform.openai.com/docs/agents)
- [Code Interpreter Tool](https://platform.openai.com/docs/agents/tools/code-interpreter)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)