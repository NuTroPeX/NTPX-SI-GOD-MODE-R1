import json, os, sqlite3, threading, uuid, urllib.request, urllib.error
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parent
DB=Path(os.environ.get('NTPX_DB',str(ROOT/'data'/'godmode.db')))
WORKSPACE=Path(os.environ.get('NTPX_WORKSPACE',str(ROOT/'workspace'))).resolve()
LOCK=threading.RLock()

def connect():
    DB.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(DB,timeout=10);db.row_factory=sqlite3.Row;return db

def now():return datetime.now(timezone.utc).isoformat()
def init():
    WORKSPACE.mkdir(parents=True,exist_ok=True)
    with LOCK,connect() as db:
        db.executescript('''CREATE TABLE IF NOT EXISTS agents(id TEXT PRIMARY KEY,name TEXT NOT NULL,role TEXT NOT NULL,enabled INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS memories(id TEXT PRIMARY KEY,content TEXT NOT NULL,created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY,mission TEXT NOT NULL,mode TEXT NOT NULL,status TEXT NOT NULL,plan TEXT NOT NULL,created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY,task_id TEXT NOT NULL,tool TEXT NOT NULL,args TEXT NOT NULL,status TEXT NOT NULL,result TEXT NOT NULL DEFAULT '',created TEXT NOT NULL,FOREIGN KEY(task_id) REFERENCES tasks(id));''')
        for x in [('generator','Generator','Creates plans and artifacts'),('operator','Operator','Proposes controlled actions'),('developer','Developer','Builds and validates code')]:
            db.execute('INSERT OR IGNORE INTO agents VALUES(?,?,?,1)',x)

def rows(table):
    if table not in ('agents','memories','tasks','actions'):raise ValueError('Invalid table')
    with LOCK,connect() as db:return [dict(r) for r in db.execute(f'SELECT * FROM {table} ORDER BY rowid DESC LIMIT 200')]

def plan(mission,mode):
    return {'engine':'offline-rule-planner','steps':[{'agent':'generator','action':'Define requirements for: '+mission[:180]},{'agent':'developer','action':'Draft implementation and test plan'},{'agent':'operator','action':'Request explicit approval before write actions'}],'requires_approval':True,'execution':'not_started'}

def model_chat(prompt):
    # Ollama's native HTTP API. Loopback only: no arbitrary remote endpoints.
    url='http://127.0.0.1:'+str(int(os.environ.get('NTPX_OLLAMA_PORT','11434')))+'/api/generate'
    payload=json.dumps({'model':os.environ.get('NTPX_MODEL','qwen2.5-coder:1.5b'),'prompt':prompt,'stream':False,'options':{'num_predict':512}}).encode()
    req=urllib.request.Request(url,data=payload,headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=45) as r:return json.load(r).get('response','')
    except (urllib.error.URLError,TimeoutError,OSError) as e:raise ValueError('Local Ollama unavailable or model missing; install/start Ollama and pull the configured model') from e

def safe_path(relative):
    if not isinstance(relative,str) or not relative or len(relative)>200 or '\\' in relative:raise ValueError('Invalid path')
    p=Path(relative)
    if p.is_absolute() or '..' in p.parts or p.parts[0].startswith('.'):raise ValueError('Path denied')
    target=(WORKSPACE/p).resolve()
    if not target.is_relative_to(WORKSPACE):raise ValueError('Path escapes workspace')
    return target

def run_tool(tool,args):
    if tool=='list_files':
        return {'files':[str(p.relative_to(WORKSPACE)) for p in WORKSPACE.rglob('*') if p.is_file() and not p.is_symlink()][:200]}
    if tool=='read_file':
        p=safe_path(args.get('path'));return {'content':p.read_text(encoding='utf-8')[:20000]}
    if tool=='write_file':
        p=safe_path(args.get('path'));content=args.get('content')
        if not isinstance(content,str) or len(content.encode())>100000:raise ValueError('Content exceeds limit')
        p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content,encoding='utf-8');return {'written':str(p.relative_to(WORKSPACE))}
    raise ValueError('Unknown tool')

class Handler(BaseHTTPRequestHandler):
    def send(self,code,data):
        body=json.dumps(data).encode();self.send_response(code)
        for k,v in [('Content-Type','application/json'),('Content-Length',str(len(body))),('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),('Content-Security-Policy',"default-src 'none'")]:self.send_header(k,v)
        self.end_headers();self.wfile.write(body)
    def read(self):
        n=int(self.headers.get('Content-Length','0'))
        if n<0 or n>120000:raise ValueError('Request too large')
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError('JSON required')
        return json.loads(self.rfile.read(n) or b'{}')
    def origin_ok(self):
        origin=self.headers.get('Origin')
        if not origin:return True
        u=urlparse(origin);host=self.headers.get('Host','')
        return u.scheme=='http' and u.netloc==host and u.hostname in ('localhost','127.0.0.1')
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/api/state':return self.send(200,{'agents':rows('agents'),'memories':rows('memories'),'tasks':rows('tasks'),'actions':rows('actions'),'runtime':'local Ollama optional; offline planner available','approval_required':True})
        if path in ('/','/index.html'):
            body=(ROOT/'index.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body);return
        self.send(404,{'error':'Not found'})
    def do_POST(self):
        try:
            if not self.origin_ok():return self.send(403,{'error':'Origin denied'})
            data=self.read();path=urlparse(self.path).path
            if not isinstance(data,dict):raise ValueError('JSON object required')
            if path=='/api/chat':
                prompt=data.get('prompt','')
                if not isinstance(prompt,str) or not 1<=len(prompt.strip())<=4000:raise ValueError('Invalid prompt')
                return self.send(200,{'engine':'ollama','response':model_chat(prompt)})
            if path=='/api/tasks':
                mission=data.get('mission','');mode=data.get('mode','auto')
                if not isinstance(mission,str) or not 1<=len(mission.strip())<=2000 or mode not in ('auto','generator','operator','developer'):raise ValueError('Invalid mission or mode')
                item=(str(uuid.uuid4()),mission.strip(),mode,'pending_approval',json.dumps(plan(mission,mode)),now())
                with LOCK,connect() as db:db.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?)',item)
                return self.send(201,{'id':item[0],'status':item[3]})
            if path=='/api/memories':
                content=data.get('content','')
                if not isinstance(content,str) or not 1<=len(content.strip())<=4000:raise ValueError('Invalid memory')
                with LOCK,connect() as db:db.execute('INSERT INTO memories VALUES(?,?,?)',(str(uuid.uuid4()),content.strip(),now()))
                return self.send(201,{'ok':True})
            if path=='/api/agents/toggle':
                agent=data.get('id');enabled=data.get('enabled')
                if agent not in ('generator','operator','developer') or type(enabled) is not bool:raise ValueError('Invalid agent')
                with LOCK,connect() as db:db.execute('UPDATE agents SET enabled=? WHERE id=?',(int(enabled),agent))
                return self.send(200,{'ok':True})
            if path=='/api/tasks/approve':
                task_id=data.get('id')
                if not isinstance(task_id,str):raise ValueError('Invalid task ID')
                with LOCK,connect() as db:
                    cur=db.execute("UPDATE tasks SET status='approved_plan_only' WHERE id=? AND status='pending_approval'",(task_id,))
                    if not cur.rowcount:return self.send(404,{'error':'Pending task not found'})
                return self.send(200,{'status':'approved_plan_only','note':'No tool executed'})
            if path=='/api/actions':
                task_id=data.get('task_id');tool=data.get('tool');args=data.get('args',{})
                if tool not in ('list_files','read_file','write_file') or not isinstance(args,dict):raise ValueError('Invalid tool')
                if not isinstance(task_id,str):raise ValueError('Invalid task')
                if tool in ('read_file','write_file'):safe_path(args.get('path'))
                with LOCK,connect() as db:
                    if not db.execute("SELECT 1 FROM tasks WHERE id=? AND status='approved_plan_only'",(task_id,)).fetchone():raise ValueError('Approve task plan first')
                    action_id=str(uuid.uuid4());db.execute('INSERT INTO actions(id,task_id,tool,args,status,result,created) VALUES(?,?,?,?,?,?,?)',(action_id,task_id,tool,json.dumps(args),'pending_approval','',now()))
                return self.send(201,{'id':action_id,'status':'pending_approval'})
            if path=='/api/actions/approve':
                action_id=data.get('id')
                if not isinstance(action_id,str):raise ValueError('Invalid action ID')
                with LOCK,connect() as db:
                    action=db.execute('SELECT * FROM actions WHERE id=?',(action_id,)).fetchone()
                    if not action or action['status']!='pending_approval':return self.send(404,{'error':'Pending action not found'})
                    # Serialize approval + execution to prevent duplicate actions.
                    try:result=run_tool(action['tool'],json.loads(action['args']));status='completed'
                    except (ValueError,OSError,UnicodeError) as e:result={'error':str(e)};status='failed'
                    db.execute('UPDATE actions SET status=?,result=? WHERE id=?',(status,json.dumps(result),action_id))
                return self.send(200,{'status':status,'result':result})
            return self.send(404,{'error':'Not found'})
        except (ValueError,TypeError,KeyError,json.JSONDecodeError) as e:return self.send(400,{'error':str(e)})
    def log_message(self,*args):pass

def serve(host='127.0.0.1',port=8765):
    if host not in ('127.0.0.1','localhost'):raise ValueError('R2 binds loopback only')
    init();server=ThreadingHTTPServer((host,port),Handler);print(f'NTPX G.O.D. Mode http://{host}:{port}',flush=True);server.serve_forever()
if __name__=='__main__':serve(os.environ.get('NTPX_HOST','127.0.0.1'),int(os.environ.get('NTPX_PORT','8765')))