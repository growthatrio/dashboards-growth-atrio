"""Funções compartilhadas: sessão, consulta à Nekt e preparo do SQL. Só biblioteca padrão do Python."""
import base64, csv, hashlib, hmac, io, json, os, re, time, urllib.error, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
NEKT_URL = 'https://api.nekt.ai/api/v1/sql-query/'
SESSION_SECONDS = 12 * 3600
COOKIE = 'sess'
_CACHE = {}          # (dashboard, dataset, params) -> (expira, resposta)
CACHE_SECONDS = 600
DASHBOARDS = {'travel': 'Dashboard Travel Week', 'growth': 'Dashboard Growth Hotéis'}


# ---------- usuários e sessão
def _secret():
    s = os.environ.get('SESSION_SECRET', '')
    if len(s) < 16:
        raise RuntimeError('SESSION_SECRET não configurada (mínimo de 16 caracteres).')
    return s.encode()


def allowed_users():
    """ACCESS_USERS: JSON no formato {"email@atriohoteis.com.br": "senha", ...}."""
    raw = os.environ.get('ACCESS_USERS', '{}')
    try:
        users = json.loads(raw)
    except Exception:
        return {}
    return {str(k).strip().lower(): str(v) for k, v in users.items()}


def check_login(email, password):
    users = allowed_users()
    expected = users.get((email or '').strip().lower())
    ok = expected is not None and hmac.compare_digest(expected.encode(), (password or '').encode())
    if not ok:
        time.sleep(1.0)  # desacelera tentativas
    return ok


def make_session(email):
    exp = int(time.time()) + SESSION_SECONDS
    payload = base64.urlsafe_b64encode(('%s|%d' % (email.lower(), exp)).encode()).decode().rstrip('=')
    sig = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    return payload + '.' + sig


def read_session(cookie_header):
    """Devolve o e-mail da sessão válida ou None. Também confere se o e-mail ainda está na lista."""
    if not cookie_header:
        return None
    for part in cookie_header.split(';'):
        k, _, v = part.strip().partition('=')
        if k == COOKIE and '.' in v:
            payload, sig = v.rsplit('.', 1)
            good = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, good):
                return None
            try:
                email, exp = base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)).decode().split('|')
            except Exception:
                return None
            if int(exp) < time.time() or email not in allowed_users():
                return None
            return email
    return None


def cookie_header(value, max_age):
    return '%s=%s; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=%d' % (COOKIE, value, max_age)


# ---------- consultas
def load_defs(name):
    if name not in DASHBOARDS:
        raise KeyError('dashboard desconhecido')
    with open(os.path.join(ROOT, 'private', 'datasets', name + '.json'), encoding='utf-8') as f:
        return json.load(f)['datasets']


_DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
_ENUMS = {'platform': {'Meta Ads', 'Google Ads'}, 'etapa': {'todo', 'pre', 'esquenta', 'tw', 'ressaca'}}


def _literal(name, value):
    if value is None or value == '':
        return 'NULL'
    v = str(value)
    if name in ('start', 'end'):
        if not _DATE.match(v):
            raise ValueError('data inválida em %s' % name)
        return "'%s'" % v
    if name in _ENUMS and v not in _ENUMS[name]:
        raise ValueError('valor inválido em %s' % name)
    if len(v) > 200:
        raise ValueError('valor muito longo em %s' % name)
    v = v.replace('\\', '\\\\').replace("'", "\\'").replace('\n', ' ').replace('\r', ' ')
    return "'%s'" % v


def render_sql(sql, params):
    allowed = {'start', 'end', 'platform', 'grupo', 'marca', 'hotel', 'agencia', 'campaign', 'etapa'}
    unknown = set(params) - allowed
    if unknown:
        raise ValueError('parâmetro não permitido: %s' % ', '.join(sorted(unknown)))
    return re.sub(r'\{\{(\w+)\}\}', lambda m: _literal(m.group(1), params.get(m.group(1))), sql)


def _http_json(req, timeout):
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace')[:300]
        raise RuntimeError('Nekt respondeu %s: %s' % (e.code, body))


def run_nekt(sql):
    key = os.environ.get('NEKT_API_KEY', '')
    if not key:
        raise RuntimeError('NEKT_API_KEY não configurada.')
    req = urllib.request.Request(NEKT_URL, data=json.dumps({'sql': sql, 'mode': 'csv'}).encode(), method='POST',
                                 headers={'Content-Type': 'application/json', 'x-api-key': key})
    res = _http_json(req, 55)
    if res.get('state') != 'SUCCEEDED' or not res.get('presigned_urls'):
        raise RuntimeError('Consulta falhou: %s' % (res.get('state_change_reason') or res.get('state') or 'sem detalhe'))
    columns, data = None, []
    for url in res['presigned_urls']:
        with urllib.request.urlopen(url, timeout=30) as r:
            rows = list(csv.reader(io.StringIO(r.read().decode('utf-8-sig'))))
        if not rows:
            continue
        if columns is None:
            columns = rows[0]; data.extend(rows[1:])
        else:
            data.extend(rows[1:] if rows[0] == columns else rows)
    return {'status': 'succeeded', 'columns': columns or [], 'data': data, 'data_truncated': False}


def dataset(name, ds, params):
    defs = load_defs(name)
    if ds not in defs:
        raise KeyError('dataset desconhecido')
    used = {k: params.get(k) for k in defs[ds]['params']}
    ck = (name, ds, json.dumps(used, sort_keys=True))
    hit = _CACHE.get(ck)
    if hit and hit[0] > time.time():
        return hit[1]
    out = run_nekt(render_sql(defs[ds]['sql'], used))
    _CACHE[ck] = (time.time() + CACHE_SECONDS, out)
    return out


# ---------- respostas HTTP
def send(h, code, body, ctype='application/json; charset=utf-8', headers=None):
    data = body if isinstance(body, bytes) else (json.dumps(body, ensure_ascii=False) if not isinstance(body, str) else body).encode('utf-8')
    h.send_response(code)
    h.send_header('Content-Type', ctype)
    h.send_header('Content-Length', str(len(data)))
    h.send_header('Cache-Control', 'no-store')
    for k, v in (headers or {}).items():
        h.send_header(k, v)
    h.end_headers()
    h.wfile.write(data)
