/* Mini runtime "dash": reproduz o que os dashboards usam no Claude (loader, calc, data, onData, params).
   Os dados vêm de /api/data (o servidor consulta a Nekt). Nenhuma chave fica no navegador. */
(function () {
  var DASH = document.documentElement.getAttribute('data-dash');
  var loaders = {}, calcs = {}, state = {}, subs = [], params = {}, manifest = {}, started = false, scheduled = false;
  var queue = [], running = 0, MAX = 4;

  function notify() {
    if (scheduled) return; scheduled = true;
    setTimeout(function () { scheduled = false; subs.forEach(function (f) { try { f(); } catch (e) { console.error(e); } }); showErrors(); }, 0);
  }
  function showErrors() {
    var el = document.getElementById('dash-err'); if (!el) return;
    var errs = Object.keys(state).filter(function (k) { return state[k].status === 'error'; }).map(function (k) { return k + ': ' + state[k].error; });
    if (!errs.length) { el.style.display = 'none'; return; }
    el.innerHTML = '<b>Erro ao consultar a Nekt.</b> ' + errs.slice(0, 2).join(' | ').replace(/</g, '&lt;') + (errs.length > 2 ? ' (+' + (errs.length - 2) + ')' : '');
    el.style.display = 'block';
  }
  function keyFor(id) {
    var names = manifest[id] || [], o = {};
    names.forEach(function (n) { if (params[n] != null && params[n] !== '') o[n] = params[n]; });
    return JSON.stringify(o);
  }
  function pump() {
    while (running < MAX && queue.length) { var job = queue.shift(); running++; job().then(function () { running--; pump(); }); }
  }
  function enqueue(id) {
    var key = keyFor(id), st = state[id] || (state[id] = { v: 0 });
    if (st.key === key && (st.status === 'ok' || st.status === 'loading')) return;
    st.key = key; st.status = 'loading'; st.data = undefined; st.error = undefined; notify();
    queue.push(function () {
      return fetch('/api/data?d=' + encodeURIComponent(DASH) + '&ds=' + encodeURIComponent(id) + '&p=' + encodeURIComponent(key), { credentials: 'same-origin' })
        .then(function (r) {
          if (r.status === 401) { location.href = '/'; throw new Error('Sessão expirada'); }
          return r.json();
        })
        .then(function (answer) {
          if (st.key !== key) return;
          var out = loaders[id].fn({ answer: answer });
          st.data = out.rows; st.columns = out.columns; st.cut = out.cut; st.status = 'ok'; st.v++;
        })
        .catch(function (e) { if (st.key !== key) return; st.status = 'error'; st.error = String((e && e.message) || e); })
        .then(function () { if (st.key === key) notify(); });
    });
    pump();
  }
  function get(id) {
    if (calcs[id]) {
      var c = calcs[id], ins = c.inputs.map(get), bad = ins.filter(function (i) { return i.status !== 'ok'; });
      if (bad.length) return { status: bad.some(function (i) { return i.status === 'error'; }) ? 'error' : 'loading' };
      var sig = ins.map(function (i) { return i.v; }).join('|');
      if (c.sig !== sig) { try { c.out = c.fn.apply(null, ins.map(function (i) { return i.data; })); c.err = null; } catch (e) { c.err = String(e && e.message || e); } c.sig = sig; c.v = (c.v || 0) + 1; }
      return c.err ? { status: 'error', error: c.err } : { status: 'ok', data: c.out, v: c.v };
    }
    var st = state[id];
    if (!st) return { status: 'loading' };
    return { status: st.status, data: st.data, columns: st.columns, cut: st.cut, error: st.error, v: st.v };
  }
  function refetch(changed) {
    if (!started) return;
    Object.keys(loaders).forEach(function (id) {
      var names = manifest[id] || [];
      if (!changed || names.some(function (n) { return changed.indexOf(n) >= 0; })) enqueue(id);
    });
  }
  window.dash = {
    loader: function (id, o) { loaders[id] = o; },
    calc: function (id, o) { calcs[id] = { inputs: o.inputs, fn: o.fn }; },
    data: get,
    onData: function (f) { subs.push(f); },
    params: function () { var o = {}; Object.keys(params).forEach(function (k) { o[k] = params[k]; }); return o; },
    setParams: function (p) {
      var changed = [];
      Object.keys(p).forEach(function (k) { var v = p[k] === '' ? null : p[k]; if ((params[k] == null ? null : params[k]) !== (v == null ? null : v)) { changed.push(k); if (v == null) delete params[k]; else params[k] = v; } });
      if (changed.length) { refetch(changed); notify(); }
    },
    setLink: function (name) { try { history.replaceState(null, '', '#' + (name || '')); } catch (e) {} },
    resetParams: function () { var changed = Object.keys(params); params = {}; if (changed.length) { refetch(changed); notify(); } }
  };

  function start() {
    var bar = document.createElement('div'); bar.id = 'dash-topbar';
    bar.innerHTML = '<a href="/menu">Dashboards</a><a href="/api/logout">Sair</a>';
    document.body.appendChild(bar);
    var err = document.createElement('div'); err.id = 'dash-err'; document.body.appendChild(err);
    fetch('/api/manifest?d=' + encodeURIComponent(DASH), { credentials: 'same-origin' })
      .then(function (r) { if (r.status === 401) { location.href = '/'; throw new Error('401'); } return r.json(); })
      .then(function (m) {
        manifest = m.datasets || {};
        (m.statics || []).forEach(function (id) { manifest[id] = []; loaders[id] = { fn: function (x) { return { rows: x.answer.rows || [], columns: [], cut: false }; } }; });
        started = true; refetch(null); notify();
      })
      .catch(function (e) { err.style.display = 'block'; err.innerHTML = '<b>Não foi possível iniciar.</b> ' + String(e && e.message || e); });
  }
  if (document.readyState === 'complete') setTimeout(start, 0); else window.addEventListener('load', start);
})();
