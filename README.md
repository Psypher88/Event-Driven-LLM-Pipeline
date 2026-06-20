# Quan_Proj — Quantitative Trading Signal System

An event-driven quantitative trading prototype that fetches financial news and market data, scores it with AI agents running on a local LLM, and outputs BUY/PASS trading signals. The system is designed so that adding a new data source or a new agent requires only creating one new file — no existing files ever change.

---

## Architecture

```
sources/                        data/                  agents/
  source_rss.py    ──writes──▶  source_rss.json  ──▶
  source_akshare.py ──writes──▶ source_akshare.json ─▶  core/orchestrator.py
  (add more freely)                                       (discovers all files)
                                                               │
                                                     runs each agent on each item
                                                               │
                                                    agents/agent_buyer.py
                                                    agents/agent_seller.py
                                                    (add more freely)
                                                               │
                                                               ▼
                                                    core/signal_engine.py
                                                    (weighted score + filter)
                                                               │
                                              ┌────────────────┴────────────────┐
                                              ▼                                 ▼
                                    logs/signal_log.txt               server.exe (C)
                                    (decision record)          (circuit breaker, port 9000)
```

Every data source writes the same JSON format. Every agent reads the same input and returns the same output. The orchestrator and signal engine never need to know what sources or agents exist — they discover them automatically.

---

## How to Extend the System

**To add a new data source:**
1. Create `sources/source_xyz.py`
2. Write a `fetch()` function that writes to `data/source_xyz.json`
3. Follow the source contract (see below)
4. No other files need to be changed

**To add a new agent:**
1. Create `agents/agent_xyz.py`
2. Write a `run(news_text)` function that returns an agent result dict
3. Follow the agent contract (see below)
4. No other files need to be changed

**Source contract** — every `data/*.json` file must contain:
```json
{
  "source_name": "xyz",
  "fetched_at": "2024-01-15T09:30:00",
  "items": [
    { "text": "the news or data as a plain English sentence", "meta": {} }
  ]
}
```

**Agent contract** — every `agents/agent_xyz.py` must return:
```python
{ "agent_name": "xyz", "score": 3, "reason": "one sentence", "weight": 0.5 }
```
`score` is an integer from -5 (very bearish) to +5 (very bullish). `weight` is 0.0 to 1.0.

---

## Prerequisites

| Requirement | Version / Notes |
|---|---|
| Python | 3.10 or 3.11 |
| Ollama | Running locally at `http://localhost:11434` |
| LLM model | `qwen2.5:14b` (pull with `ollama pull qwen2.5:14b`) |
| GCC | Required to compile `server.c` (e.g. MinGW on Windows) |
| feedparser | `pip install feedparser` |
| requests | `pip install requests` |

---

## Quick Start

1. **Pull the LLM model** (one-time setup):
   ```
   ollama pull qwen2.5:14b
   ```

2. **Start Ollama** (keep running in background):
   ```
   ollama serve
   ```

3. **Compile and start the C pipeline server** (keep running in a separate terminal):
   ```
   make
   .\server.exe
   ```

4. **Fetch fresh data** (run before each analysis):
   ```
   python sources/source_rss.py
   python sources/source_akshare.py
   ```

5. **Run the full pipeline**:
   ```
   python core/signal_engine.py
   ```

6. **Check the output log**:
   ```
   logs/signal_log.txt
   ```

---

## File Descriptions

| File | Purpose |
|---|---|
| `contracts/source_schema.py` | Validates that a source output has all required fields before it is written or used |
| `contracts/agent_schema.py` | Validates that an agent result has all required fields and valid score/weight ranges |
| `sources/source_rss.py` | Fetches the latest 5 news headlines from CNBC RSS and writes to `data/source_rss.json` |
| `sources/source_akshare.py` | Fetches today's close price and turnover rate for an A-share stock, writes to `data/source_akshare.json` |
| `agents/agent_buyer.py` | Scores news from a buy-side perspective using the local LLM; weight 0.6 |
| `agents/agent_seller.py` | Scores news from a sell-side perspective using the local LLM; weight 0.4 |
| `core/ollama_client.py` | The only file that talks to the Ollama HTTP API; all agents call this module |
| `core/orchestrator.py` | Discovers all source JSON files and all agents, runs every agent on every item, returns results |
| `core/signal_engine.py` | Computes the weighted score, applies BUY/PASS filter rules, writes to the signal log |
| `server.c` | Async TCP server (select-based) with a circuit breaker that rejects scores at or below -4 |
| `Makefile` | Compiles `server.c` with `gcc -lws2_32` |
