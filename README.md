# AI Agent Workflow Builder

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite)

Define multi-step AI workflows as YAML, connect tools (search, parse, summarize, export), run them locally, and inspect execution logs. A lightweight alternative to hosted workflow platforms.

## Features

- Define multi-step workflows in YAML with step dependencies
- Built-in tool nodes: web search, text parsing, summarization, file export
- Local execution — no cloud dependencies
- Execution log viewer with per-step status and output
- Save and reuse workflow templates
- Extensible tool interface for adding custom nodes

## Quick Start

```bash
uv sync
uv run uvicorn src.main:app --reload --port 8109
```

Open: http://localhost:8109

## API

| Method | Path          | Description          |
| ------ | ------------- | -------------------- |
| GET    | `/`           | Browser demo UI      |
| GET    | `/api/health` | Health check         |
| GET    | `/docs`       | Interactive API docs |

## Tests

```bash
uv run pytest -q
```