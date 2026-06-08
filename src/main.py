from __future__ import annotations
import csv, io, re, sqlite3
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field
APP_NAME='AI Agent Workflow Builder'
DB_FILE=Path(__file__).resolve().parent.parent/'data'/'app.sqlite'
DB_FILE.parent.mkdir(exist_ok=True)
app=FastAPI(title=APP_NAME, version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
def json_dumps(obj: Any) -> str:
    import json; return json.dumps(obj, ensure_ascii=False)
def json_loads(text: str) -> Any:
    import json; return json.loads(text)
def db() -> sqlite3.Connection:
    conn=sqlite3.connect(DB_FILE); conn.row_factory=sqlite3.Row; conn.execute('pragma journal_mode=wal'); return conn
def init_db() -> None:
    with db() as conn: conn.execute('create table if not exists records (id integer primary key autoincrement, kind text not null, title text not null, payload text not null, created_at text not null)')
init_db()
def save_record(kind: str, title: str, payload: str) -> int:
    with db() as conn:
        cur=conn.execute('insert into records(kind,title,payload,created_at) values (?,?,?,?)',(kind,title,payload,datetime.utcnow().isoformat())); return int(cur.lastrowid)
def rows(kind: str | None = None) -> list[dict[str, Any]]:
    with db() as conn:
        data=conn.execute('select * from records where kind=? order by id desc',(kind,)).fetchall() if kind else conn.execute('select * from records order by id desc').fetchall()
    return [dict(r) for r in data]
@app.get('/api/health')
def health(): return {'ok': True, 'app': APP_NAME, 'records': len(rows())}
@app.get('/', response_class=HTMLResponse)
def home(): return INDEX_HTML

from pathlib import Path as PPath
WORKFLOWS_DIR = PPath(__file__).resolve().parent.parent / 'data' / 'workflows'
WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
class WorkflowStep(BaseModel):
    name: str
    tool: str = Field(..., pattern=r'^(search|parse|summarize|export)$')
    params: dict = {}
class Workflow(BaseModel):
    name: str
    steps: list[WorkflowStep]
BUILTIN_TOOLS = {"search": lambda p: f"Searched: {p.get('query','n/a')} -> returned results", "parse": lambda p: f"Parsed content of length {p.get('length',0)}", "summarize": lambda p: f"Summarized text with target length {p.get('target_length','brief')}", "export": lambda p: f"Exported to {p.get('format','csv')}"}
@app.post('/api/workflows')
def create_workflow(wf: Workflow):
    path = WORKFLOWS_DIR / f"{wf.name.replace(' ','_').lower()}.json"
    payload = wf.model_dump()
    path.write_text(json_dumps(payload))
    save_record('workflow', wf.name, json_dumps(payload))
    return {"name": wf.name, "steps": len(wf.steps), "saved_to": str(path.name)}
@app.get('/api/workflows')
def list_workflows():
    return {"workflows": [json_loads(r['payload']) | {'id':r['id'],'created_at':r['created_at']} for r in rows('workflow')]}
@app.post('/api/workflows/{name}/run')
def run_workflow(name: str):
    items = [r for r in rows('workflow') if json_loads(r['payload']).get('name') == name]
    if not items: return {"error": f"Workflow '{name}' not found"}, 404
    wf = json_loads(items[0]['payload'])
    logs = []
    for step in wf['steps']:
        tool_fn = BUILTIN_TOOLS.get(step['tool'])
        if tool_fn: logs.append({"step": step['name'], "tool": step['tool'], "result": tool_fn(step['params']), "status": "ok"})
        else: logs.append({"step": step['name'], "tool": step['tool'], "result": "Unknown tool", "status": "error"})
    record = {"name": name, "logs": logs, "total_steps": len(logs)}
    save_record('run', name, json_dumps(record))
    return record
@app.get('/api/runs')
def list_runs():
    return {"runs": [json_loads(r['payload']) | {'id':r['id'],'created_at':r['created_at']} for r in rows('run')]}

INDEX_HTML='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI Agent Workflow Builder</title><style>body{font-family:Inter,Arial,sans-serif;background:#0f172a;color:#e5e7eb;margin:0}main{max-width:980px;margin:auto;padding:32px}.card{background:#111827;border:1px solid #334155;border-radius:18px;padding:24px;margin:18px 0}h1{font-size:42px}textarea,input{width:100%;box-sizing:border-box;border-radius:12px;border:1px solid #475569;background:#020617;color:#e5e7eb;padding:14px;margin:8px 0}button{background:#22c55e;color:#04130a;border:0;border-radius:12px;padding:12px 18px;font-weight:700}pre{white-space:pre-wrap;background:#020617;border-radius:12px;padding:16px}.pill{background:#1e293b;border:1px solid #475569;border-radius:999px;padding:6px 10px}</style></head><body><main><div class="card"><span class="pill">agentic automation</span><h1>AI Agent Workflow Builder</h1><p>Define multi-step AI workflows with connected tools, run them locally, and inspect the logs.</p><ul><li>Define multi-step workflow YAML</li><li>Connect tools: search, parse, summarize, export</li><li>Run workflow locally</li><li>View execution logs and step status</li><li>Save and reuse workflow templates</li></ul></div><div class="card"><h2>Live Demo</h2><textarea id="input" rows="6">{"name":"Research Pipeline","steps":[{"name":"Search Web","tool":"search","params":{"query":"latest AI news"}},{"name":"Summarize","tool":"summarize","params":{"target_length":"brief"}},{"name":"Export","tool":"export","params":{"format":"markdown"}}]}</textarea><button onclick="runWorkflow()">Run Saved</button><input id="input3" placeholder="workflow name" value="Research Pipeline" /><button onclick="runDemo()">Run</button><pre id="out">Click Run to call the API.</pre></div><div class="card"><h2>API</h2><p>Health: /api/health &middot; Docs: /docs</p></div><script>async function runDemo(){const res=await (fetch(\'/api/workflows\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify(JSON.parse(document.getElementById(\'input\').value))}));document.getElementById(\'out\').textContent=JSON.stringify(await res.json(),null,2);}async function runWorkflow(){const name=document.getElementById(\'input3\').value||\'Research Pipeline\';const res=await fetch(\'/api/workflows/\'+encodeURIComponent(name)+\'/run\');document.getElementById(\'out\').textContent=JSON.stringify(await res.json(),null,2);}</script></main></body></html>'
