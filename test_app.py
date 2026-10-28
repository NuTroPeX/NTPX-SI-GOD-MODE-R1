import json, os, tempfile, threading, unittest
from http.server import ThreadingHTTPServer
from urllib.request import urlopen, Request

class AppTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();os.environ['NTPX_DB']=cls.tmp.name+'/test.db'
  import app
  cls.app=app;app.DB=__import__('pathlib').Path(os.environ['NTPX_DB']);app.init()
  cls.server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
  cls.url='http://127.0.0.1:'+str(cls.server.server_port)
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
 @classmethod
 def tearDownClass(cls): cls.server.shutdown();cls.server.server_close();cls.tmp.cleanup()
 def req(self,path,payload=None):
  data=None if payload is None else json.dumps(payload).encode()
  req=Request(self.url+path,data=data,headers={'Content-Type':'application/json'} if data else {})
  with urlopen(req) as res:return res.status,json.load(res)
 def test_initial_agents(self):
  _,state=self.req('/api/state');self.assertEqual(len(state['agents']),3)
 def test_memory_persists(self):
  self.req('/api/memories',{'content':'Project memory'});_,state=self.req('/api/state');self.assertEqual(state['memories'][0]['content'],'Project memory')
 def test_approval_gate(self):
  _,result=self.req('/api/tasks',{'mission':'Build app','mode':'auto'});self.assertEqual(result['status'],'pending_approval')
  _,result=self.req('/api/tasks/approve',{'id':result['id']});self.assertEqual(result['status'],'approved_plan_only')
 def test_agent_toggle(self):
  self.req('/api/agents/toggle',{'id':'operator','enabled':False});_,state=self.req('/api/state');self.assertEqual(next(a for a in state['agents'] if a['id']=='operator')['enabled'],0)
 def test_plan_is_not_execution(self):
  _,r=self.req('/api/tasks',{'mission':'Test','mode':'developer'});_,state=self.req('/api/state');task=next(t for t in state['tasks'] if t['id']==r['id']);self.assertEqual(json.loads(task['plan'])['execution'],'not_started')
if __name__=='__main__':unittest.main()