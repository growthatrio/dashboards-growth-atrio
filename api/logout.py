import os, sys
from http.server import BaseHTTPRequestHandler
sys.path.insert(0, os.path.dirname(__file__))
import _lib


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        _lib.send(self, 302, b'', 'text/plain', {'Location': '/', 'Set-Cookie': _lib.cookie_header('', 0)})
