(function () {
  const canvas = document.getElementById('c');
  const ctx = canvas.getContext('2d');
  const TYPE_COLORS = {
    document: '#6ba3c9', concept: '#c98b6b',
    rationale: '#8fb573', paper: '#b07bc9'
  };

  let G = null, nodes = [], edges = [], byId = new Map();
  let view = { x: 0, y: 0, k: 1 };
  let hover = null, selected = null, dragNode = null, panning = false;
  let alpha = 1;

  const state = {
    types: new Set(['document', 'concept', 'rationale', 'paper']),
    extractedOnly: true,
    crossOnly: false,
    mode: 'type',
    comm: -1,
    query: ''
  };

  function commColor(cid) {
    const h = (cid * 47) % 360;
    return `hsl(${h} 55% 60%)`;
  }
  function dayColor(day) {
    const d = parseInt((day || '').slice(3), 10) || 0;
    return `hsl(${(d / 30) * 300} 60% 60%)`;
  }
  function colorOf(n) {
    if (state.mode === 'comm') return commColor(n.comm);
    if (state.mode === 'day') return n.day ? dayColor(n.day) : '#555';
    return TYPE_COLORS[n.type] || '#888';
  }

  function resize() {
    const dpr = window.devicePixelRatio || 1;
    canvas.width = canvas.clientWidth * dpr;
    canvas.height = canvas.clientHeight * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  window.addEventListener('resize', () => { resize(); draw(); });

  function visibleNode(n) {
    if (!state.types.has(n.type)) return false;
    if (state.comm !== -1 && n.comm !== state.comm) return false;
    if (state.query && !n.label.toLowerCase().includes(state.query)) return false;
    return true;
  }
  function visibleEdge(e) {
    if (state.extractedOnly && e.conf !== 'EXTRACTED') return false;
    if (state.crossOnly && !e.cross) return false;
    return e.S.vis && e.T.vis;
  }

  function applyFilters() {
    let nv = 0, ev = 0, xv = 0;
    for (const n of nodes) { n.vis = visibleNode(n); if (n.vis) nv++; }
    for (const e of edges) {
      e.vis = visibleEdge(e);
      if (e.vis) { ev++; if (e.cross) xv++; }
    }
    // Hide nodes that end up with no visible edges when a link filter is on.
    if (state.extractedOnly || state.crossOnly) {
      for (const n of nodes) n.hasEdge = false;
      for (const e of edges) if (e.vis) { e.S.hasEdge = true; e.T.hasEdge = true; }
      nv = 0;
      for (const n of nodes) {
        if (n.vis && !n.hasEdge) n.vis = false;
        if (n.vis) nv++;
      }
    }
    document.getElementById('nN').textContent = nv;
    document.getElementById('nE').textContent = ev;
    document.getElementById('nX').textContent = xv;
    alpha = Math.max(alpha, 0.35);
  }

  function step() {
    const REP = 5200, SPR = 0.0055, LEN = 46, CEN = 0.0016, DAMP = 0.86;
    const act = nodes.filter(n => n.vis);
    const gs = 130;
    const grid = new Map();
    for (const n of act) {
      const key = ((n.x / gs) | 0) + ':' + ((n.y / gs) | 0);
      if (!grid.has(key)) grid.set(key, []);
      grid.get(key).push(n);
    }
    for (const n of act) {
      let fx = 0, fy = 0;
      const gx = (n.x / gs) | 0, gy = (n.y / gs) | 0;
      for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) {
        const cell = grid.get((gx + i) + ':' + (gy + j));
        if (!cell) continue;
        for (const m of cell) {
          if (m === n) continue;
          let dx = n.x - m.x, dy = n.y - m.y;
          let d2 = dx * dx + dy * dy;
          if (d2 < 0.01) { dx = Math.random() - 0.5; dy = Math.random() - 0.5; d2 = 1; }
          if (d2 > 62500) continue;
          const f = REP / d2;
          const d = Math.sqrt(d2);
          fx += (dx / d) * f; fy += (dy / d) * f;
        }
      }
      fx -= n.x * CEN; fy -= n.y * CEN;
      n.vx = (n.vx + fx * 0.016) * DAMP;
      n.vy = (n.vy + fy * 0.016) * DAMP;
    }
    for (const e of edges) {
      if (!e.vis) continue;
      const a = e.S, b = e.T;
      const dx = b.x - a.x, dy = b.y - a.y;
      const d = Math.sqrt(dx * dx + dy * dy) || 1;
      const f = (d - LEN) * SPR;
      const ux = (dx / d) * f, uy = (dy / d) * f;
      a.vx += ux; a.vy += uy; b.vx -= ux; b.vy -= uy;
    }
    for (const n of act) {
      if (n === dragNode) continue;
      n.x += n.vx * alpha * 2.2;
      n.y += n.vy * alpha * 2.2;
    }
    alpha *= 0.994;
    if (alpha < 0.004) alpha = 0.004;
  }

  function radius(n) { return 2.4 + Math.min(Math.sqrt(n.deg) * 1.5, 9); }

  function draw() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    ctx.clearRect(0, 0, w, h);
    ctx.save();
    ctx.translate(w / 2 + view.x, h / 2 + view.y);
    ctx.scale(view.k, view.k);

    const nbrs = selected ? selected.nbrSet : null;

    ctx.lineWidth = 0.7 / view.k;
    for (const e of edges) {
      if (!e.vis) continue;
      const near = selected && (e.S === selected || e.T === selected);
      if (selected && !near) { ctx.strokeStyle = 'rgba(120,110,95,0.10)'; }
      else if (near) { ctx.strokeStyle = 'rgba(201,162,39,0.75)'; }
      else if (e.cross) { ctx.strokeStyle = 'rgba(201,162,39,0.34)'; }
      else { ctx.strokeStyle = e.conf === 'EXTRACTED' ? 'rgba(150,140,125,0.30)' : 'rgba(110,102,90,0.16)'; }
      ctx.beginPath();
      ctx.moveTo(e.S.x, e.S.y);
      ctx.lineTo(e.T.x, e.T.y);
      ctx.stroke();
    }

    for (const n of nodes) {
      if (!n.vis) continue;
      const dim = selected && n !== selected && !(nbrs && nbrs.has(n.id));
      ctx.globalAlpha = dim ? 0.22 : 1;
      ctx.fillStyle = colorOf(n);
      ctx.beginPath();
      ctx.arc(n.x, n.y, radius(n), 0, 6.2832);
      ctx.fill();
      if (n === selected || n === hover) {
        ctx.globalAlpha = 1;
        ctx.strokeStyle = '#c9a227';
        ctx.lineWidth = 2 / view.k;
        ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;

    // Labels for hubs and focus, only when zoomed enough to read.
    const showAll = view.k > 1.5;
    ctx.font = `${11 / view.k}px -apple-system, sans-serif`;
    ctx.textAlign = 'center';
    for (const n of nodes) {
      if (!n.vis) continue;
      const focus = n === selected || n === hover || (nbrs && nbrs.has(n.id));
      if (!focus && !(showAll && n.deg >= 3) && !(n.deg >= 12)) continue;
      ctx.fillStyle = focus ? '#f2ead9' : 'rgba(200,190,172,0.65)';
      const t = n.label.length > 40 ? n.label.slice(0, 38) + '…' : n.label;
      ctx.fillText(t, n.x, n.y - radius(n) - 4 / view.k);
    }
    ctx.restore();
  }

  function tick() { step(); draw(); requestAnimationFrame(tick); }

  function toWorld(px, py) {
    return {
      x: (px - canvas.clientWidth / 2 - view.x) / view.k,
      y: (py - canvas.clientHeight / 2 - view.y) / view.k
    };
  }
  function pick(px, py) {
    const p = toWorld(px, py);
    let best = null, bd = 1e9;
    for (const n of nodes) {
      if (!n.vis) continue;
      const dx = n.x - p.x, dy = n.y - p.y;
      const d = dx * dx + dy * dy;
      const r = radius(n) + 5;
      if (d < r * r && d < bd) { bd = d; best = n; }
    }
    return best;
  }

  canvas.addEventListener('mousedown', ev => {
    const n = pick(ev.offsetX, ev.offsetY);
    if (n) { dragNode = n; alpha = 0.5; }
    else { panning = true; canvas.classList.add('dragging'); }
    canvas._lx = ev.offsetX; canvas._ly = ev.offsetY;
  });
  window.addEventListener('mouseup', () => {
    dragNode = null; panning = false; canvas.classList.remove('dragging');
  });
  canvas.addEventListener('mousemove', ev => {
    const dx = ev.offsetX - canvas._lx, dy = ev.offsetY - canvas._ly;
    canvas._lx = ev.offsetX; canvas._ly = ev.offsetY;
    if (dragNode) {
      const p = toWorld(ev.offsetX, ev.offsetY);
      dragNode.x = p.x; dragNode.y = p.y; dragNode.vx = 0; dragNode.vy = 0;
      alpha = Math.max(alpha, 0.4);
    } else if (panning) {
      view.x += dx; view.y += dy;
    } else {
      const h = pick(ev.offsetX, ev.offsetY);
      if (h !== hover) { hover = h; canvas.style.cursor = h ? 'pointer' : 'grab'; }
    }
  });
  canvas.addEventListener('click', ev => {
    if (Math.abs(ev.offsetX - canvas._dx) > 4) return;
    const n = pick(ev.offsetX, ev.offsetY);
    select(n);
  });
  canvas.addEventListener('mousedown', ev => { canvas._dx = ev.offsetX; });
  canvas.addEventListener('wheel', ev => {
    ev.preventDefault();
    const f = ev.deltaY < 0 ? 1.12 : 1 / 1.12;
    const mx = ev.offsetX - canvas.clientWidth / 2, my = ev.offsetY - canvas.clientHeight / 2;
    view.x = mx - (mx - view.x) * f;
    view.y = my - (my - view.y) * f;
    view.k = Math.max(0.1, Math.min(9, view.k * f));
  }, { passive: false });

  function select(n) {
    selected = n;
    const d = document.getElementById('detail');
    if (!n) { d.className = 'panel'; return; }
    d.className = 'panel on';
    const rows = n.nbrs
      .filter(x => x.node.vis)
      .sort((a, b) => b.node.deg - a.node.deg)
      .map(x => `<div class="nbr" data-id="${x.node.id}">${esc(x.node.label)}
        <div class="rel">${x.rel}${x.conf === 'EXTRACTED' ? '' : ' · ' + x.conf.toLowerCase()}${x.cross ? ' · cross-day' : ''}</div></div>`)
      .join('');
    d.innerHTML = `
      <div class="dlabel">${esc(n.label)}</div>
      <div style="margin-bottom:8px">
        <span class="badge">${n.type}</span>
        ${n.day ? `<span class="badge">${n.day}</span>` : ''}
        <span class="badge">${n.deg} link${n.deg === 1 ? '' : 's'}</span>
      </div>
      ${n.url ? `<a href="${esc(n.url)}" target="_blank" rel="noopener">source page ↗</a>` : ''}
      <h2>Connections</h2>${rows || '<div class="sub">none visible</div>'}`;
    d.querySelectorAll('.nbr').forEach(el =>
      el.addEventListener('click', () => {
        const t = byId.get(el.dataset.id);
        if (t) { select(t); view.x = -t.x * view.k; view.y = -t.y * view.k; }
      }));
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  }

  document.querySelectorAll('[data-t]').forEach(cb =>
    cb.addEventListener('change', () => {
      cb.checked ? state.types.add(cb.dataset.t) : state.types.delete(cb.dataset.t);
      applyFilters();
    }));
  document.getElementById('fExtracted').addEventListener('change', e => {
    state.extractedOnly = e.target.checked; applyFilters();
  });
  document.getElementById('fCross').addEventListener('change', e => {
    state.crossOnly = e.target.checked; applyFilters();
  });
  document.getElementById('mode').addEventListener('change', e => { state.mode = e.target.value; });
  document.getElementById('comm').addEventListener('change', e => {
    state.comm = parseInt(e.target.value, 10); applyFilters();
  });
  let qt;
  document.getElementById('q').addEventListener('input', e => {
    clearTimeout(qt);
    qt = setTimeout(() => { state.query = e.target.value.trim().toLowerCase(); applyFilters(); }, 140);
  });
  document.getElementById('reset').addEventListener('click', () => {
    view = { x: 0, y: 0, k: 1 }; select(null); alpha = 0.9;
  });

  fetch('/api/graph-data')
    .then(r => r.json())
    .then(data => {
      G = data;
      nodes = data.nodes;
      const R = 420;
      nodes.forEach((n, i) => {
        const a = i * 2.399963;
        const r = R * Math.sqrt(i / nodes.length);
        n.x = Math.cos(a) * r; n.y = Math.sin(a) * r;
        n.vx = 0; n.vy = 0; n.vis = true; n.nbrs = [];
        byId.set(n.id, n);
      });
      edges = data.edges.filter(e => byId.has(e.s) && byId.has(e.t));
      for (const e of edges) {
        e.S = byId.get(e.s); e.T = byId.get(e.t);
        e.cross = !!(e.S.day && e.T.day && e.S.day !== e.T.day);
        e.S.nbrs.push({ node: e.T, rel: e.rel, conf: e.conf, cross: e.cross });
        e.T.nbrs.push({ node: e.S, rel: e.rel, conf: e.conf, cross: e.cross });
      }
      for (const n of nodes) n.nbrSet = new Set(n.nbrs.map(x => x.node.id));

      const sel = document.getElementById('comm');
      data.communities.filter(c => c.size >= 4).forEach(c => {
        const o = document.createElement('option');
        o.value = c.id;
        o.textContent = `${c.label.slice(0, 34)}${c.label.length > 34 ? '…' : ''} (${c.size})`;
        sel.appendChild(o);
      });

      resize();
      applyFilters();
      tick();
    })
    .catch(err => {
      document.getElementById('hint').textContent = 'failed to load graph data: ' + err;
    });
})();
