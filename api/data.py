import json, os, sys
from urllib.parse import parse_qs, urlparse
from http.server import BaseHTTPRequestHandler
sys.path.insert(0, os.path.dirname(__file__))
import _lib


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if not _lib.read_session(self.headers.get('Cookie')):
                return _lib.send(self, 401, {'error': 'não autenticado'})
            q = parse_qs(urlparse(self.path).query)
            name, ds = (q.get('d') or [''])[0], (q.get('ds') or [''])[0]
            params = json.loads((q.get('p') or ['{}'])[0] or '{}')
            if not isinstance(params, dict):
                raise ValueError('parâmetros inválidos')
            return _lib.send(self, 200, _lib.dataset(name, ds, params))
        except (KeyError, ValueError) as e:
            return _lib.send(self, 400, {'status': 'failed', 'error': str(e)})
        except Exception as e:
            return _lib.send(self, 200, {'status': 'failed', 'error': str(e)})
