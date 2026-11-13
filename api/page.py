import os, sys
from urllib.parse import parse_qs, urlparse
from http.server import BaseHTTPRequestHandler
sys.path.insert(0, os.path.dirname(__file__))
import _lib

MENU = '''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Dashboards Atrio</title>
<link rel="stylesheet" href="/assets/theme.css"><style>.m{max-width:560px;margin:48px auto}.m h1{font-size:22px}.m a.c{display:block;margin:12px 0;padding:16px 18px;border:1px solid var(--color-border-line);border-radius:10px;color:var(--color-fg);text-decoration:none;background:var(--color-panel)}.m a.c:hover{border-color:#DB9B0E}.m small{color:var(--color-fg-muted)}</style></head>
<body><div class="m"><h1>Dashboards Atrio</h1>
<a class="c" href="/atrio"><b>Growth Atrio</b><br><small>Atrio Institucional: mídia paga, site, leads e redes sociais</small></a>
<a class="c" href="/growth"><b>Growth Hotéis</b><br><small>Meta Ads, Google Ads e reservas Web Direto por hotel e marca</small></a>
<a class="c" href="/travel"><b>Growth Travel Week</b><br><small>Campanha de 03/11 a 06/12: etapas, metas e campanhas</small></a>
<p><small>Logado como __EMAIL__ · <a href="/api/logout">Sair</a></small></p></div></body></html>'''


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            email = _lib.read_session(self.headers.get('Cookie'))
        except Exception as e:
            return _lib.send(self, 500, 'Erro de configuração: %s' % e, 'text/plain; charset=utf-8')
        if not email:
            return _lib.send(self, 302, b'', 'text/plain', {'Location': '/'})
        name = (parse_qs(urlparse(self.path).query).get('d') or [''])[0]
        if name == 'menu':
            return _lib.send(self, 200, MENU.replace('__EMAIL__', email), 'text/html; charset=utf-8')
        if name not in _lib.DASHBOARDS:
            return _lib.send(self, 404, 'Não encontrado', 'text/plain; charset=utf-8')
        with open(os.path.join(_lib.ROOT, 'private', name + '.html'), 'rb') as f:
            return _lib.send(self, 200, f.read(), 'text/html; charset=utf-8')
