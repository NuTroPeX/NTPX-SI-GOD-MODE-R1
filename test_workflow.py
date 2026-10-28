"""HTTP-level regression tests for the approval-gated workspace flow."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer
import app

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db, self.old_ws = app.DB, app.WORKSPACE
        app.DB = Path(self.tmp.name) / 'test.db'
        app.WORKSPACE = Path(self.tmp.name) / 'workspace'
        app.init()
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        app.DB, app.WORKSPACE = self.old_db, self.old_ws
        self.tmp.cleanup()

    def call(self, route, payload):
        req = Request(self.base + '/api/' + route,
                      data=json.dumps(payload).encode(),
                      headers={'Content-Type': 'application/json'})
        try:
            with urlopen(req) as r:
                return r.status, json.load(r)
        except HTTPError as e:
            return e.code, json.load(e)

    def test_approved_write_and_read(self):
        _, task = self.call('tasks', {'mission':'Create a file','mode':'developer'})
        task_id = task['id']
        status, _ = self.call('actions', {'task_id':task_id,'tool':'write_file',
                                          'args':{'path':'note.txt','content':'approved'}})
        self.assertEqual(status, 400)
        self.call('tasks/approve', {'id':task_id})
        status, action = self.call('actions', {'task_id':task_id,'tool':'write_file',
                                               'args':{'path':'note.txt','content':'approved'}})
        self.assertEqual(status, 201)
        self.assertFalse((app.WORKSPACE / 'note.txt').exists())
        status, result = self.call('actions/approve', {'id':action['id']})
        self.assertEqual((status,result['status']), (200,'completed'))
        self.assertEqual((app.WORKSPACE / 'note.txt').read_text(), 'approved')
        status, _ = self.call('actions/approve', {'id':action['id']})
        self.assertEqual(status, 404)

    def test_rejects_cross_origin(self):
        req = Request(self.base+'/api/memories',data=b'{"content":"bad"}',
                      headers={'Content-Type':'application/json','Origin':'https://attacker.example'})
        with self.assertRaises(HTTPError) as cm:
            urlopen(req)
        self.assertEqual(cm.exception.code, 403)

if __name__ == '__main__':
    unittest.main()
