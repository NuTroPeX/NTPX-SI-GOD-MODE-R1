"""Additional regression checks for the supported Python/web release target."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import app

class WebBaselineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous = (app.DB, app.WORKSPACE)
        app.DB = Path(self.temp.name) / "state.sqlite"
        app.WORKSPACE = Path(self.temp.name) / "workspace"
        app.init()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        app.DB, app.WORKSPACE = self.previous
        self.temp.cleanup()

    def test_dashboard_serves_html(self):
        with urlopen(self.base + "/") as response:
            self.assertEqual(response.status, 200)
            self.assertIn("text/html", response.headers["Content-Type"])
            self.assertIn(b"<html", response.read().lower())

    def test_unknown_route_is_404(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(self.base + "/missing")
        self.assertEqual(error.exception.code, 404)

    def test_post_requires_json(self):
        request = Request(self.base + "/api/tasks", data=b"mission=test",
                          headers={"Content-Type": "text/plain"})
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code, 400)

    def test_oversized_request_is_rejected(self):
        request = Request(self.base + "/api/tasks", data=b"x" * 120001,
                          headers={"Content-Type": "application/json"})
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code, 400)

if __name__ == "__main__":
    unittest.main()
