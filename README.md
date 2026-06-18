# AI Agent Workflow Builder

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi) ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite) ![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=flat-square&logo=pydantic) ![Workflows](https://img.shields.io/badge/Workflows-2088FF?style=flat-square&logo=github-actions)

Define multi-step AI workflows with connected tools, run them locally, and inspect the logs.

![workflow-builder-demo](screenshots/workflow-builder-demo.png)

## Features
- Define multi-step workflow YAML
- Connect tools: search, parse, summarize, export
- Run workflow locally
- View execution logs and step status
- Save and reuse workflow templates

## Quick Start

```bash
uv sync
uv run uvicorn src.main:app --reload --port 8109
```

Open: http://localhost:8109

## API
- `GET /` - browser demo
- `GET /api/health` - health check
- `GET /docs` - interactive FastAPI docs

## Verify
```bash
uv run pytest -q
```
