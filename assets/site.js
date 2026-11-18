/* Chess portfolio behaviour. No dependencies. Everything degrades gracefully without it. */
(function () {
  'use strict';
  var doc = document;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s, r) { return (r || doc).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || doc).querySelectorAll(s)); };

  /* ---------- theme ---------- */
  var themeBtn = $('[data-theme-toggle]');
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var el = doc.documentElement;
      var current = el.dataset.theme || (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
      var next = current === 'light' ? 'dark' : 'light';
      el.dataset.theme = next;
      try { localStorage.setItem('theme', next); } catch (e) { /* private mode */ }
    });
  }

  /* ---------- mobile nav ---------- */
  var toggle = $('.nav-toggle'), nav = $('#nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    });
    $$('a', nav).forEach(function (a) {
      a.addEventListener('click', function () { nav.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); });
    });
  }

  /* ---------- reveal on scroll + active nav link ---------- */
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { threshold: 0.12 });
    $$('.reveal').forEach(function (el) { io.observe(el); });

    var links = {};
    $$('.nav a').forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting && links[e.target.id]) {
          Object.keys(links).forEach(function (k) { links[k].classList.remove('on'); });
          links[e.target.id].classList.add('on');
        }
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    $$('main section[id]').forEach(function (s) { spy.observe(s); });
  } else {
    $$('.reveal').forEach(function (el) { el.classList.add('in'); });
  }

  /* ---------- project filters ---------- */
  var filters = $$('.f');
  if (filters.length) {
    filters.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var f = btn.dataset.filter;
        filters.forEach(function (b) { var on = b === btn; b.classList.toggle('on', on); b.setAttribute('aria-pressed', String(on)); });
        $$('.card').forEach(function (c) { c.hidden = !(f === 'all' || c.dataset.cat === f); });
      });
    });
  }

  /* ---------- copy email ---------- */
  $$('[data-copy]').forEach(function (btn) {
    var label = btn.textContent;
    btn.addEventListener('click', function () {
      var done = function () { btn.textContent = 'Copied'; setTimeout(function () { btn.textContent = label; }, 1600); };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(btn.dataset.copy).then(done, function () { btn.textContent = 'Press Ctrl+C'; });
      } else { btn.textContent = btn.dataset.copy; }
    });
  });

  /* ---------- skill graph: highlight a piece's connections ---------- */
  var graph = $('.graph'), caption = $('[data-caption]');
  if (graph) {
    var edges = $$('.edge', graph);
    var clear = function () {
      graph.classList.remove('has-hl');
      edges.forEach(function (e) { e.classList.remove('hl'); });
      if (caption) caption.textContent = 'Hover or focus a piece.';
    };
    $$('.node', graph).forEach(function (n) {
      var show = function () {
        var id = n.dataset.id;
        graph.classList.add('has-hl');
        edges.forEach(function (e) { e.classList.toggle('hl', e.dataset.a === id || e.dataset.b === id); });
        if (caption) caption.textContent = n.dataset.name + ': ' + n.dataset.state;
      };
      n.addEventListener('mouseenter', show); n.addEventListener('focus', show);
      n.addEventListener('mouseleave', clear); n.addEventListener('blur', clear);
    });
  }

  /* ---------- the board: click your piece, then a marked square ---------- */
  var root = $('[data-board]');
  if (!root || !window.PIECES) return;
  var board = $('.board', root), statusEl = $('[data-status]', root);
  var P = window.PIECES;
  var pieceName = root.dataset.piece in P ? root.dataset.piece : 'knight';
  var original = pieceName;

  function svg(name) {
    var cells = {}, ring = {};
    P[name].forEach(function (row, r) { for (var c = 0; c < row.length; c++) if (row[c] === '#') cells[c + ',' + r] = 1; });
    Object.keys(cells).forEach(function (k) {
      var p = k.split(','), c = +p[0], r = +p[1];
      for (var dx = -1; dx <= 1; dx++) for (var dy = -1; dy <= 1; dy++) {
        var kk = (c + dx) + ',' + (r + dy); if (!cells[kk]) ring[kk] = 1;
      }
    });
    var d = function (set) { return Object.keys(set).map(function (k) { var p = k.split(','); return 'M' + p[0] + ' ' + p[1] + 'h1v1h-1z'; }).join(''); };
    return '<svg class="pc" viewBox="-1 -1 11 11" aria-hidden="true" focusable="false" shape-rendering="crispEdges"><path class="po" d="' + d(ring) + '"/><path class="pf" d="' + d(cells) + '"/></svg>';
  }
  var inb = function (c, r) { return c >= 0 && c < 8 && r >= 0 && r < 8; };
  function legal(name, c, r) {
    var out = [];
    var add = function (x, y) { if (inb(x, y)) out.push([x, y]); };
    var slide = function (dx, dy) { var x = c + dx, y = r + dy; while (inb(x, y)) { out.push([x, y]); x += dx; y += dy; } };
    var orth = [[1, 0], [-1, 0], [0, 1], [0, -1]], diag = [[1, 1], [1, -1], [-1, 1], [-1, -1]];
    if (name === 'knight') [[1, 2], [2, 1], [-1, 2], [-2, 1], [1, -2], [2, -1], [-1, -2], [-2, -1]].forEach(function (m) { add(c + m[0], r + m[1]); });
    else if (name === 'king') orth.concat(diag).forEach(function (m) { add(c + m[0], r + m[1]); });
    else if (name === 'rook') orth.forEach(function (m) { slide(m[0], m[1]); });
    else if (name === 'bishop') diag.forEach(function (m) { slide(m[0], m[1]); });
    else if (name === 'queen') orth.concat(diag).forEach(function (m) { slide(m[0], m[1]); });
    else if (name === 'pawn') { add(c, r - 1); if (r === 6) add(c, r - 2); }
    return out;
  }
  var sqName = function (c, r) { return 'abcdefgh'[c] + (8 - r); };
  var cap = function (s) { return s.charAt(0).toUpperCase() + s.slice(1); };

  var pos, from, moves, selected, touched, timer;
  var pieceEl = doc.createElement('button');
  pieceEl.type = 'button'; pieceEl.className = 'piece';
  var lastFrom = doc.createElement('span'), lastTo = doc.createElement('span');
  lastFrom.className = lastTo.className = 'sq last';
  var targets = [];

  function place(el, c, r) { el.style.setProperty('--c', c); el.style.setProperty('--r', r); }
  function say(msg) { if (statusEl) statusEl.textContent = msg; }
  function label() {
    pieceEl.setAttribute('aria-label', 'Your ' + pieceName + ' on ' + sqName(pos[0], pos[1]) + '. Press to ' + (selected ? 'hide' : 'show') + ' legal moves.');
    pieceEl.setAttribute('aria-expanded', String(selected));
  }
  function clearTargets() { targets.forEach(function (t) { t.remove(); }); targets = []; }
  function showTargets() {
    clearTargets();
    if (!selected) return;
    legal(pieceName, pos[0], pos[1]).forEach(function (m) {
      var t = doc.createElement('button');
      t.type = 'button'; t.className = 'target'; place(t, m[0], m[1]);
      t.setAttribute('aria-label', 'Move to ' + sqName(m[0], m[1]));
      t.addEventListener('click', function () { touched = true; stopAuto(); move(m[0], m[1]); });
      board.appendChild(t); targets.push(t);
    });
  }
  function move(c, r) {
    from = pos.slice(); pos = [c, r]; moves++;
    selected = false;
    place(lastFrom, from[0], from[1]); place(lastTo, c, r); lastFrom.hidden = lastTo.hidden = false;
    place(pieceEl, c, r);
    if (!reduce) { pieceEl.classList.remove('hop'); void pieceEl.offsetWidth; pieceEl.classList.add('hop'); }
    var msg = cap(pieceName) + ' to ' + sqName(c, r) + '. ' + moves + (moves === 1 ? ' move' : ' moves') + ' played.';
    if (pieceName === 'pawn' && r === 0) {
      pieceName = 'queen'; pieceEl.innerHTML = svg('queen'); msg = 'Promoted! The pawn is now a queen. ' + moves + ' moves played.';
    }
    say(msg); label(); showTargets();
  }
  function reset() {
    pieceName = original; pos = original === 'pawn' ? [4, 6] : [3, 4]; from = null; moves = 0; selected = false;
    pieceEl.innerHTML = svg(pieceName); place(pieceEl, pos[0], pos[1]);
    lastFrom.hidden = lastTo.hidden = true; clearTargets(); label();
    say('Try me: click the ' + pieceName + ', then a marked square.');
  }
  function auto() {
    var opts = legal(pieceName, pos[0], pos[1]);
    if (!opts.length || (pieceName === 'queen' && original === 'pawn')) { reset(); return; }
    var m = opts[Math.floor(Math.random() * opts.length)];
    move(m[0], m[1]);
    if (pieceName === 'queen' && original === 'pawn') { stopAuto(); timer = setTimeout(function () { reset(); startAuto(); }, 2400); }
  }
  function startAuto() { if (reduce || touched) return; stopAuto(); timer = setInterval(auto, 2600); }
  function stopAuto() { clearInterval(timer); clearTimeout(timer); }

  board.innerHTML = '';
  board.appendChild(lastFrom); board.appendChild(lastTo); board.appendChild(pieceEl);
  reset();
  pieceEl.addEventListener('click', function () { touched = true; stopAuto(); selected = !selected; label(); showTargets(); });
  board.addEventListener('keydown', function (e) { if (e.key === 'Escape' && selected) { selected = false; label(); showTargets(); pieceEl.focus(); } });
  var resetBtn = doc.createElement('button');
  resetBtn.type = 'button'; resetBtn.className = 'f'; resetBtn.textContent = 'Reset board'; resetBtn.style.cssText = 'grid-column:2;justify-self:start';
  resetBtn.addEventListener('click', function () { touched = true; stopAuto(); reset(); });
  root.appendChild(resetBtn);
  doc.addEventListener('visibilitychange', function () { if (doc.hidden) stopAuto(); else startAuto(); });
  startAuto();
})();
