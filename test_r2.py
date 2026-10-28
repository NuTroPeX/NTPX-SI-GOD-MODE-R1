import unittest, tempfile, pathlib, json
import app
class R2Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.old_db,self.old_ws=app.DB,app.WORKSPACE
  app.DB=pathlib.Path(self.tmp.name)/'db.sqlite';app.WORKSPACE=pathlib.Path(self.tmp.name)/'workspace';app.init()
 def tearDown(self):app.DB,self.old_db=self.old_db,app.DB;app.WORKSPACE=self.old_ws;self.tmp.cleanup()
 def test_safe_path_rejects_escape(self):
  for path in ['../escape','/etc/passwd','link/../../oops']:
   with self.assertRaises(ValueError):app.safe_path(path)
 def test_workspace_write_read(self):
  self.assertEqual(app.run_tool('write_file',{'path':'demo/test.txt','content':'hello'})['written'],'demo/test.txt')
  self.assertEqual(app.run_tool('read_file',{'path':'demo/test.txt'})['content'],'hello')
 def test_no_shell_tool(self):
  with self.assertRaises(ValueError):app.run_tool('shell',{'command':'echo hi'})
 def test_symlink_escape(self):
  (app.WORKSPACE/'link').symlink_to(pathlib.Path(self.tmp.name),target_is_directory=True)
  with self.assertRaises(ValueError):app.safe_path('link/escape')
 def test_plan_not_execution(self):self.assertEqual(app.plan('hello','auto')['execution'],'not_started')
if __name__=='__main__':unittest.main()