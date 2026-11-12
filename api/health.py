import os, sys
from http.server import BaseHTTPRequestHandler
sys.path.insert(0, os.path.dirname(__file__))
import _lib


class handler(BaseHTTPRequestHandler):
    """Teste rápido: abra /api/health depois de entrar. Mostra se a chave da Nekt funciona."""
    def do_GET(self):
        if not _lib.read_session(self.headers.get('Cookie')):
            return _lib.send(self, 401, {'error': 'não autenticado'})
        try:
            r = _lib.run_nekt('SELECT 1 AS ok')
            return _lib.send(self, 200, {'nekt': 'ok', 'resposta': r})
        except Exception as e:
            return _lib.send(self, 200, {'nekt': 'erro', 'detalhe': str(e)})
