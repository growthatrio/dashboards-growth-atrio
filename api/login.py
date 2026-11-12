import json, os, sys
from http.server import BaseHTTPRequestHandler
sys.path.insert(0, os.path.dirname(__file__))
import _lib


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            n = int(self.headers.get('Content-Length') or 0)
            body = json.loads(self.rfile.read(min(n, 4096)).decode('utf-8') or '{}')
            email, pw = str(body.get('email', '')), str(body.get('password', ''))
            if _lib.check_login(email, pw):
                tok = _lib.make_session(email)
                return _lib.send(self, 200, {'ok': True}, headers={'Set-Cookie': _lib.cookie_header(tok, _lib.SESSION_SECONDS)})
            return _lib.send(self, 401, {'ok': False, 'error': 'E-mail ou senha incorretos.'})
        except Exception as e:
            return _lib.send(self, 500, {'ok': False, 'error': 'Erro de configuração: %s' % e})
