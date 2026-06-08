from fastapi.testclient import TestClient
from src.main import app
client = TestClient(app)
def test_health():
    r=client.get('/api/health')
    assert r.status_code == 200
    assert r.json()['ok'] is True

def test_workflow_create_and_run():
    wf={'name':'Test Pipe','steps':[{'name':'Search','tool':'search','params':{'query':'test'}},{'name':'Export','tool':'export','params':{'format':'csv'}}]}
    client.post('/api/workflows', json=wf)
    data=client.get('/api/workflows').json()
    assert len(data['workflows']) >= 1
    run_res=client.post('/api/workflows/Test Pipe/run').json()
    assert run_res['total_steps'] == 2
