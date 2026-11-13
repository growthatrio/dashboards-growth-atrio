import os, sys
from urllib.parse import parse_qs, urlparse
from http.server import BaseHTTPRequestHandler
sys.path.insert(0, os.path.dirname(__file__))
import _lib


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if not _lib.read_session(self.headers.get('Cookie')):
                return _lib.send(self, 401, {'error': 'não autenticado'})
            name = (parse_qs(urlparse(self.path).query).get('d') or [''])[0]
            defs = _lib.load_defs(name)
            return _lib.send(self, 200, {'datasets': {k: v['params'] for k, v in defs.items()}, 'statics': list(_lib.load_statics(name))})
        except KeyError:
            return _lib.send(self, 404, {'error': 'dashboard desconhecido'})
        except Exception as e:
            return _lib.send(self, 500, {'error': str(e)})
