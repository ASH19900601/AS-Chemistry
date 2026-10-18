'use strict';
// ===== 介面、輸入、天氣繪製、存檔與主迴圈 =====
const UI = {};
const SAVE_KEY = 'xiaotuan-save-v1';
const WX = { drops: [], streaks: [], leaves: [], bolt: 0, boltPath: null, puddle: 0, snow: 0 };

// ----- 舞台縮放 -----
function layoutStage() {
  const wrap = $('#stageWrap');
  const w = wrap.clientWidth;
  const narrow = w < 620;
  const changed = narrow !== L.narrow;
  L.narrow = narrow;
  L.W = narrow ? 640 : 1000;
  L.H = 600;
  L.scale = w / L.W;
  computePositions();
  const st = $('#stage');
  st.style.width = L.W + 'px';
  st.style.height = L.H + 'px';
  st.style.transform = 'scale(' + L.scale + ')';
  st.classList.toggle('narrow', narrow);
  wrap.style.height = (L.H * L.scale) + 'px';
  const cv = $('#weather');
  cv.width = L.W; cv.height = L.H;
  placeScenery();
  if (changed && !MG) { X.x = clamp(X.x, 0.07, 0.93); }
  renderNest();
  renderPot();
  renderWall();
}

function placeScenery() {
  const sh = $('#shelter');
  sh.style.left = (P.nestL * L.W) + 'px';
  sh.style.width = ((P.nestR - P.nestL) * L.W) + 'px';
  sh.style.top = (P.roofY * L.H) + 'px';
  sh.style.height = ((P.ground - P.roofY) * L.H) + 'px';
  const g = nestGeom();
  const nest = $('#nest');
  nest.style.left = g.cx + 'px';
  nest.style.top = (P.ground * L.H) + 'px';
  nest.style.width = (g.hw * 2.5) + 'px';
  $('#ground').style.top = (P.ground * L.H - 8) + 'px';
  const pot = $('#pot');
  pot.style.left = (P.potX * L.W) + 'px';
  pot.style.top = (P.ground * L.H) + 'px';
  const line = $('#line');
  line.style.left = (P.lineL * L.W) + 'px';
  line.style.width = ((P.lineR - P.lineL) * L.W) + 'px';
  line.style.top = (P.lineY * L.H) + 'px';
}

function toStageXY(cx, cy) {
  const r = $('#stage').getBoundingClientRect();
  return { x: (cx - r.left) / L.scale, y: (cy - r.top) / L.scale };
}
function toStage(e) { return toStageXY(e.clientX, e.clientY); }

// ----- 命中判斷（邏輯座標） -----
function hitTuan(p) {
  const r = tuanRect();
  return p.x > r.left - 30 && p.x < r.left + r.width + 30 && p.y > r.top - 40 && p.y < r.top + r.height + 20;
}
function hitNest(p) {
  return p.x > P.nestL * L.W && p.x < P.nestR * L.W && p.y > P.roofY * L.H && p.y < P.ground * L.H + 30;
}
function hitPot(p) {
  const cx = P.potX * L.W;
  return Math.abs(p.x - cx) < 70 && p.y > P.ground * L.H - 190 && p.y < P.ground * L.H + 20;
}

// ----- 拖曳物品 -----
let ghost = null;
function makeGhost(id, cx, cy) {
  const g = document.createElement('div');
  g.className = 'ghost-item';
  g.innerHTML = itemIconHTML(id);
  document.body.appendChild(g);
  moveGhost(g, cx, cy);
  return g;
}
function moveGhost(g, cx, cy) { g.style.left = cx + 'px'; g.style.top = cy + 'px'; }
function highlightTarget(p) {
  $('#tuan').classList.toggle('drop-hot', hitTuan(p));
  $('#shelter').classList.toggle('drop-hot', !hitTuan(p) && hitNest(p));
  $('#pot').classList.toggle('drop-hot', !hitTuan(p) && hitPot(p));
}
function clearHighlight() {
  ['#tuan', '#shelter', '#pot'].forEach(s => $(s).classList.remove('drop-hot'));
}

function dragItem(e, id, source) {
  e.preventDefault();
  e.stopPropagation();
  Sound.init();
  touch();
  let anticipated = false;
  ghost = makeGhost(id, e.clientX, e.clientY);
  if (source === 'nest' || source === 'pot') { S.loc[id] = 'carry'; renderNest(); renderPot(); }
  const move = ev => {
    moveGhost(ghost, ev.clientX, ev.clientY);
    const p = toStageXY(ev.clientX, ev.clientY);
    highlightTarget(p);
    if (!anticipated) {
      const r = tuanRect();
      if (Math.hypot(p.x - (r.left + r.width / 2), p.y - (r.top + r.height / 2)) < 170) { anticipated = true; anticipate(id); }
    }
  };
  const up = ev => {
    window.removeEventListener('pointermove', move);
    window.removeEventListener('pointerup', up);
    window.removeEventListener('pointercancel', up);
    ghost.remove(); ghost = null;
    clearHighlight();
    dropItem(id, source, ev.clientX, ev.clientY);
  };
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', up);
  window.addEventListener('pointercancel', up);
}

function dropItem(id, source, cx, cy) {
  const p = toStageXY(cx, cy);
  const target = hitTuan(p) ? 'tuan' : hitNest(p) ? 'nest' : hitPot(p) ? 'pot' : null;
  const uniq = ITEMS[id].unique;
  if (uniq && S.loc[id] === 'carry') S.loc[id] = 'tray';
  if (source === target && source !== 'tuan') {
    if (uniq) S.loc[id] = source;
  } else if (target === 'tuan') {
    useItemOnTuan(id);
  } else if (target === 'nest') {
    if (source === 'tuan' && !uniq) { /* 消耗品拿走後放進窩裡就沒了 */ }
    useItemOnNest(id);
  } else if (target === 'pot') {
    if (!useItemOnPot(id) && uniq) S.loc[id] = 'tray';
  }
  if (source === 'nest' && target !== 'nest' && target !== 'tuan') takeFromNest(id);
  if (source === 'pot' && target !== 'pot' && !X.sleeping && target !== 'tuan') {
    if (id === 'umbrella' && S.env.rain > 15) react({ emo: 'afraid', say: '芽芽要淋雨了！', act: '拿走花盆上的傘' });
  }
  renderNest(); renderPot(); renderAttachments();
}

// 從小團身上拿東西：牠會抓住
function dragFromTuan(e, id) {
  e.preventDefault();
  e.stopPropagation();
  Sound.init();
  touch();
  if (MG && MG.lockTuan) return;
  const el = e.currentTarget;
  const p0 = toStage(e);
  const need = 30 + guardLevel(id) * 1.8;
  let detached = false, maxD = 0;
  const move = ev => {
    const p = toStage(ev);
    const d = Math.hypot(p.x - p0.x, p.y - p0.y);
    maxD = Math.max(maxD, d);
    if (!detached) {
      if (d > 10 && need > 70) guardResist(id);
      const k = need > 70 ? 0.3 : 0.6;
      el.style.translate = ((p.x - p0.x) * k) + 'px ' + ((p.y - p0.y) * k) + 'px';
      $('#twrap').style.setProperty('--lean', clamp((p.x - p0.x) * 0.08, -12, 12) + 'deg');
      if (d > need) {
        detached = true;
        el.style.translate = '';
        $('#twrap').style.setProperty('--lean', '0deg');
        detach(id);
        onTaken(id);
        ghost = makeGhost(id, ev.clientX, ev.clientY);
      }
    } else {
      moveGhost(ghost, ev.clientX, ev.clientY);
      highlightTarget(p);
    }
  };
  const up = ev => {
    window.removeEventListener('pointermove', move);
    window.removeEventListener('pointerup', up);
    window.removeEventListener('pointercancel', up);
    el.style.translate = '';
    $('#twrap').style.setProperty('--lean', '0deg');
    if (!detached) {
      if (maxD < 8) {
        if (id === 'bell' && X.held === 'bell') ringBell();
        else actTap('belly');
      }
      return;
    }
    ghost.remove(); ghost = null;
    clearHighlight();
    const p = toStage(ev);
    if (hitTuan(p)) useItemOnTuan(id);
    else if (hitNest(p) && ITEMS[id].unique) useItemOnNest(id);
    else if (hitPot(p)) useItemOnPot(id);
    renderNest(); renderPot(); renderAttachments();
  };
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', up);
  window.addEventListener('pointercancel', up);
}

function ringBell() {
  touch(); note('ring');
  Sound.bell();
  if (X.sleeping) { wakeUp('grumpy'); return; }
  if (recent('ring', 10000) >= 5) { tr('snark', 3); react({ emo: 'speechless', say: '好吵…一直搖。', act: '搖鈴鐺' }); return; }
  react({ emo: 'happy', say: pick(['叮鈴叮鈴～', '鈴鐺在唱歌！']), fx: 'note', anim: 'bounce', disc: 'bell_ring', act: '搖鈴鐺' });
}

// ----- 拖動小團 -----
function onTuanDown(e) {
  if (e.button > 0) return;
  if (MG && MG.lockTuan) { if (MG.type === 'tug') tugCmd('pull'); return; }
  if (X.airborne) return;
  e.preventDefault();
  Sound.init();
  const p = toStage(e);
  const r = tuanRect();
  const region = (p.y - r.top) < r.height * 0.45 ? 'head' : 'belly';
  const st = { x0: p.x, y0: p.y, mode: 'press', samples: [{ x: p.x, y: p.y, t: e.timeStamp }], dir: 0, offX: X.x * L.W - p.x, offY: X.y * L.H - p.y };
  const lp = setTimeout(() => { if (st.mode === 'press') { st.mode = 'hug'; hugBegin(); } }, 450);
  const move = ev => {
    const q = toStage(ev);
    const d = Math.hypot(q.x - st.x0, q.y - st.y0);
    if (st.mode === 'press' && d > 12) { clearTimeout(lp); st.mode = 'carry'; carryBegin(); }
    if (st.mode !== 'carry') return;
    X.x = clamp((q.x + st.offX) / L.W, 0.06, 0.94);
    X.y = clamp((q.y + st.offY) / L.H, 0.22, P.ground);
    st.samples.push({ x: q.x, y: q.y, t: ev.timeStamp });
    while (st.samples.length > 2 && ev.timeStamp - st.samples[0].t > 100) st.samples.shift();
    const n = st.samples.length;
    if (n >= 2) {
      const a = st.samples[n - 2], b = st.samples[n - 1];
      const vx = (b.x - a.x) / Math.max(1, b.t - a.t);
      if (Math.abs(vx) > 0.9) {
        const dir = Math.sign(vx);
        if (st.dir && dir !== st.dir) carryShake(7);
        st.dir = dir;
      }
    }
  };
  const up = ev => {
    window.removeEventListener('pointermove', move);
    window.removeEventListener('pointerup', up);
    window.removeEventListener('pointercancel', up);
    clearTimeout(lp);
    if (st.mode === 'press') actTap(region);
    else if (st.mode === 'hug') hugEnd();
    else if (st.mode === 'carry') {
      const s = st.samples, a = s[0], b = s[s.length - 1];
      const dt = Math.max(1, b.t - a.t);
      const fresh = ev.timeStamp - b.t < 60;
      carryEnd(fresh ? (b.x - a.x) / dt : 0, fresh ? (b.y - a.y) / dt : 0);
    }
  };
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', up);
  window.addEventListener('pointercancel', up);
}

// ----- 小窩裡的擺設 -----
let lastPieceMess = 0, lastNestGuard = 0;
function onPieceDown(e) {
  e.preventDefault();
  e.stopPropagation();
  Sound.init();
  touch();
  const el = e.currentTarget;
  const piece = NEST_PIECES.find(p => p.id === el.dataset.id);
  if (guardingNest()) {
    el.classList.remove('wiggle'); void el.offsetWidth; el.classList.add('wiggle');
    if (now() - lastNestGuard > 3000) {
      lastNestGuard = now();
      react({ emo: 'sulk', say: '我在看著喔。不准碰。', anim: 'struggle', disc: 'nest_guarded', act: '想動窩裡的東西' });
    }
    return;
  }
  const before = nestTidy();
  const o = S.nest.pieces[piece.id];
  const p0 = toStage(e);
  const start = { dx: o.dx, dy: o.dy };
  el.classList.add('drag');
  const move = ev => {
    const p = toStage(ev);
    o.dx = clamp(start.dx + (p.x - p0.x) / L.W, -0.3, 0.6);
    o.dy = clamp(start.dy + (p.y - p0.y) / L.H, -0.5, 0.08);
    renderNest();
  };
  const up = () => {
    window.removeEventListener('pointermove', move);
    window.removeEventListener('pointerup', up);
    window.removeEventListener('pointercancel', up);
    el.classList.remove('drag');
    // 靠近原位就吸回去
    if (Math.hypot(o.dx * L.W, o.dy * L.H) < 14) { o.dx = 0; o.dy = 0; }
    renderNest();
    const after = nestTidy();
    if (after > before + 4 && after >= 90 && before < 80) {
      if (!X.sleeping) { tr('grudge', -3); tr('trust', 3); react({ emo: 'moved', say: '你幫我整理了？謝謝！', fx: 'heart', disc: 'player_tidy', act: '整理小窩' }); }
    } else if (after < before - 4 && now() - lastPieceMess > 2500) {
      lastPieceMess = now();
      Sound.rustle();
      onNestMessed('亂動窩裡的擺設');
    }
  };
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', up);
  window.addEventListener('pointercancel', up);
}

// ----- 滑鼠靠近牠拿著的東西 -----
let lastHoverGuard = 0;
function onStageHover(e) {
  if (e.pointerType !== 'mouse' || e.buttons || !X.held || X.sleeping || ghost) return;
  if (now() - lastHoverGuard < 6000 || guardLevel(X.held) < 35) return;
  const r = $('#att-held').getBoundingClientRect();
  const d = Math.hypot(e.clientX - (r.left + r.width / 2), e.clientY - (r.top + r.height / 2)) / L.scale;
  if (d < 90) {
    lastHoverGuard = now();
    const h = $('#att-held');
    h.classList.add('guard');
    setTimeout(() => h.classList.remove('guard'), 1800);
    react({ emo: 'sulk', say: '這是我的喔。', anim: 'shrink', disc: 'guard_hover', act: '手靠近' + ITEMS[X.held].name });
  }
}

// ----- 托盤 -----
const LOC_TEXT = { tuan: '在小團身上', nest: '在小窩', pot: '在花盆', game: '遊戲中', carry: '拿著' };
UI.renderTray = function () {
  const tray = $('#tray');
  if (!tray.children.length) {
    tray.innerHTML = ITEM_ORDER.map(id => '<button class="tray-item" data-item="' + id + '" title="拖到小團、小窩或花盆上"><span class="ti-icon">' + itemIconHTML(id) + '</span><span class="ti-name">' + ITEMS[id].name + '</span><span class="ti-loc"></span></button>').join('');
    tray.querySelectorAll('.tray-item').forEach(b => b.addEventListener('pointerdown', e => {
      const id = b.dataset.item;
      if (ITEMS[id].unique && S.loc[id] !== 'tray') { toast(ITEMS[id].name + LOC_TEXT[S.loc[id]] + '，要從那裡拿'); return; }
      dragItem(e, id, 'tray');
    }));
  }
  ITEM_ORDER.forEach(id => {
    const b = tray.querySelector('[data-item="' + id + '"]');
    const away = !!ITEMS[id].unique && S.loc[id] !== 'tray';
    b.classList.toggle('away', away);
    b.querySelector('.ti-loc').textContent = away ? LOC_TEXT[S.loc[id]] || '' : '';
  });
};

// ----- 花盆 -----
function plantSVG(sp) {
  if (sp.stage < 0) return '';
  const dead = sp.dead, wilt = !dead && sp.health < 35;
  const g = dead ? '#9b8160' : wilt ? '#9ab06a' : '#5ea66a';
  const leaf = (x, y, r, flip) => '<path d="M' + x + ' ' + y + 'q' + (flip ? -r : r) + ' ' + (-r * 0.9) + ' ' + (flip ? -r * 1.6 : r * 1.6) + ' ' + (-r * 0.2) + 'q' + (flip ? r * 0.7 : -r * 0.7) + ' ' + (r * 0.9) + ' ' + (flip ? r * 1.6 : -r * 1.6) + ' ' + (r * 0.2) + 'z" fill="' + g + '"/>';
  let s = '';
  const st = sp.stage;
  if (st === 0) s = '<ellipse cx="60" cy="146" rx="7" ry="5" fill="#7a5638"/>';
  else {
    const h = [0, 22, 46, 70, 88, 96][st];
    const top = 148 - h;
    s += '<path d="M60 148 Q' + (56 + (wilt ? 10 : 0)) + ' ' + (148 - h / 2) + ' ' + (60 + (wilt || dead ? 16 : 0)) + ' ' + top + '" stroke="' + g + '" stroke-width="4" fill="none" stroke-linecap="round"/>';
    s += leaf(60, top + 6, 11, true) + leaf(62, top + 4, 11, false);
    if (st >= 3) s += leaf(60, top + 34, 13, false) + leaf(59, top + 40, 12, true);
    const fx = 60 + (wilt || dead ? 16 : 0);
    if (st === 4) s += '<ellipse cx="' + fx + '" cy="' + (top - 6) + '" rx="7" ry="10" fill="' + (dead ? '#9b8160' : '#e68aa0') + '"/>';
    if (st === 5) {
      const c = dead ? '#a88a6b' : '#f29bb2';
      for (let k = 0; k < 6; k++) { const a = k / 6 * Math.PI * 2; s += '<circle cx="' + (fx + Math.cos(a) * 11) + '" cy="' + (top - 8 + Math.sin(a) * 11) + '" r="8" fill="' + c + '"/>'; }
      s += '<circle cx="' + fx + '" cy="' + (top - 8) + '" r="6" fill="#f6c453"/>';
    }
  }
  return '<svg viewBox="0 0 120 160" aria-hidden="true">' + s + '</svg>';
}

function renderPot() {
  const sp = S.sprout;
  $('#plant').innerHTML = plantSVG(sp);
  const att = $('#pot-att');
  let h = '';
  if (S.loc.umbrella === 'pot') h += '<span class="pot-umb" data-item="umbrella">☂️</span>';
  if (S.loc.blanket === 'pot') h += '<span class="pot-blanket" data-item="blanket">' + SVG_ICONS.blanket + '</span>';
  if (S.loc.bell === 'pot') h += '<span class="pot-bell" data-item="bell">🔔</span>';
  att.innerHTML = h;
  att.querySelectorAll('[data-item]').forEach(el => el.addEventListener('pointerdown', e => dragItem(e, el.dataset.item, 'pot')));
  $('#pot').classList.toggle('thirsty', sp.stage >= 0 && !sp.dead && sp.water < 20);
}
UI.renderPot = renderPot;

// ----- 曬畫繩上的畫 -----
function renderWall() {
  const w = $('#wall');
  w.innerHTML = S.wall.map((d, i) => '<figure class="hung' + (d.tuan ? ' theirs' : '') + '" style="--r:' + ((i % 2 ? 1 : -1) * (2 + i)) + 'deg"><img alt="掛起來的畫" src="' + d.url + '"></figure>').join('');
}
UI.renderWall = renderWall;

// ----- 天空與天氣 -----
function mixColor(a, b, k) { return [0, 1, 2].map(i => Math.round(lerp(a[i], b[i], k))); }
function rgb(c) { return 'rgb(' + c.join(',') + ')'; }

function renderSky() {
  const env = S.env;
  const t = env.temp / 100;
  const cold = [[170, 196, 230], [228, 236, 246]], mild = [[124, 188, 232], [214, 238, 244]], hot = [[236, 160, 112], [255, 224, 176]];
  let top, bot;
  if (t < 0.5) { top = mixColor(cold[0], mild[0], t * 2); bot = mixColor(cold[1], mild[1], t * 2); }
  else { top = mixColor(mild[0], hot[0], (t - 0.5) * 2); bot = mixColor(mild[1], hot[1], (t - 0.5) * 2); }
  const cloud = clamp(Math.max(env.rain / 100 * 0.9, env.thunder ? 0.85 : 0, env.wind / 200), 0, 1);
  top = mixColor(top, [86, 98, 118], cloud);
  bot = mixColor(bot, [150, 158, 172], cloud * 0.85);
  $('#sky').style.background = 'linear-gradient(' + rgb(top) + ',' + rgb(bot) + ')';
  const sun = $('#sun');
  sun.style.opacity = clamp(1 - cloud * 1.6, 0, 1);
  sun.classList.toggle('hot', env.temp > 70);
  document.querySelectorAll('#sky .cloud').forEach((c, i) => {
    c.style.opacity = clamp(0.35 + cloud * 0.65, 0, 1);
    c.style.filter = 'brightness(' + (1 - cloud * 0.45) + ')';
    c.style.animationDuration = (60 - env.wind * 0.5 + i * 12) + 's';
  });
  const grass = env.temp < 30 ? mixColor([132, 168, 140], [124, 178, 112], env.temp / 30) : env.temp > 70 ? mixColor([124, 178, 112], [190, 180, 104], (env.temp - 70) / 30) : [124, 178, 112];
  $('#ground').style.background = 'linear-gradient(' + rgb(mixColor(grass, [90, 110, 100], cloud * 0.4)) + ',' + rgb(mixColor(mixColor(grass, [80, 100, 70], 0.35), [70, 84, 80], cloud * 0.4)) + ')';
  $('#puddles').style.opacity = WX.puddle;
  $('#snowCover').style.opacity = WX.snow;
}

function newDrop(anyY) {
  return { x: rand(-100, L.W + 100), y: anyY ? rand(-L.H, L.H) : rand(-60, -10), v: rand(0.7, 1.1), len: rand(10, 20), r: rand(1.5, 3.5), ph: rand(0, 6) };
}

function drawWeather(dt) {
  const cv = $('#weather');
  const g = cv.getContext('2d');
  g.clearRect(0, 0, L.W, L.H);
  const env = S.env;
  const snow = snowing();
  const want = Math.round(env.rain * 2.4);
  while (WX.drops.length < want) WX.drops.push(newDrop(true));
  if (WX.drops.length > want) WX.drops.length = want;
  const slant = env.wind * 0.012;
  const groundY = P.ground * L.H;
  const shL = P.nestL * L.W, shR = P.nestR * L.W, shT = P.roofY * L.H;
  g.lineWidth = 1.6;
  g.strokeStyle = 'rgba(214,228,250,.75)';
  g.fillStyle = 'rgba(255,255,255,.92)';
  g.beginPath();
  for (const d of WX.drops) {
    if (snow) {
      d.y += d.v * 0.11 * dt;
      d.x += (slant * 0.5 + Math.sin(d.y / 40 + d.ph) * 0.4) * dt * 0.1;
    } else {
      d.y += d.v * dt;
      d.x += slant * d.v * dt;
    }
    if (d.y > groundY + rand(0, 40) || (d.x > shL && d.x < shR && d.y > shT) || d.x > L.W + 120) Object.assign(d, newDrop(false));
    if (snow) { g.moveTo(d.x + d.r, d.y); g.arc(d.x, d.y, d.r, 0, Math.PI * 2); }
    else { g.moveTo(d.x, d.y); g.lineTo(d.x - slant * d.len, d.y - d.len); }
  }
  if (snow) g.fill(); else g.stroke();
  // 風的線條與落葉
  const ws = env.wind > 20 ? Math.round((env.wind - 20) / 6) : 0;
  while (WX.streaks.length < ws) WX.streaks.push({ x: rand(-300, L.W), y: rand(20, groundY - 20), len: rand(40, 120), v: rand(0.6, 1.2) });
  if (WX.streaks.length > ws) WX.streaks.length = ws;
  g.strokeStyle = 'rgba(255,255,255,.45)';
  g.lineWidth = 2;
  g.beginPath();
  for (const s of WX.streaks) {
    s.x += s.v * env.wind * 0.02 * dt;
    if (s.x > L.W + 50) { s.x = rand(-300, -50); s.y = rand(20, groundY - 20); }
    g.moveTo(s.x, s.y); g.quadraticCurveTo(s.x + s.len / 2, s.y - 6, s.x + s.len, s.y);
  }
  g.stroke();
  const wl = env.wind > 45 ? Math.round((env.wind - 45) / 8) : 0;
  while (WX.leaves.length < wl) WX.leaves.push({ x: rand(-200, 0), y: rand(80, groundY), r: rand(0, 6), v: rand(0.8, 1.4) });
  if (WX.leaves.length > wl) WX.leaves.length = wl;
  g.fillStyle = env.temp > 70 ? '#c9a54a' : '#7bb26a';
  for (const l of WX.leaves) {
    l.x += l.v * env.wind * 0.012 * dt; l.y += Math.sin(l.x / 50) * 0.6; l.r += 0.01 * dt;
    if (l.x > L.W + 30) { l.x = rand(-200, -20); l.y = rand(80, groundY); }
    g.save(); g.translate(l.x, l.y); g.rotate(l.r); g.beginPath(); g.ellipse(0, 0, 9, 4, 0, 0, Math.PI * 2); g.fill(); g.restore();
  }
  // 閃電
  if (WX.bolt > 0 && WX.boltPath) {
    WX.bolt -= dt;
    g.strokeStyle = 'rgba(255,250,210,' + clamp(WX.bolt / 150, 0, 1) + ')';
    g.lineWidth = 4;
    g.beginPath();
    WX.boltPath.forEach((pt, i) => (i ? g.lineTo(pt[0], pt[1]) : g.moveTo(pt[0], pt[1])));
    g.stroke();
  }
  // 積水與積雪
  if (env.rain > 10 && !snow) WX.puddle = clamp(WX.puddle + env.rain * 0.0000025 * dt, 0, 0.8);
  else WX.puddle = clamp(WX.puddle - 0.00002 * dt * (1 + env.temp / 50), 0, 0.8);
  if (snow) WX.snow = clamp(WX.snow + env.rain * 0.000003 * dt, 0, 0.9);
  else if (env.temp > 25) WX.snow = clamp(WX.snow - 0.00003 * dt * (env.temp / 50), 0, 0.9);
}

UI.flash = function () {
  const f = $('#flash');
  f.classList.remove('on'); void f.offsetWidth; f.classList.add('on');
  WX.bolt = 220;
  let x = rand(L.W * 0.35, L.W * 0.95), y = 0;
  const path = [[x, y]];
  while (y < L.H * 0.45) { y += rand(20, 45); x += rand(-30, 30); path.push([x, y]); }
  WX.boltPath = path;
};

// ----- 面板 -----
function setTab(name) {
  document.querySelectorAll('.tabs button').forEach(b => {
    const on = b.dataset.tab === name;
    b.classList.toggle('on', on);
    b.setAttribute('aria-selected', on ? 'true' : 'false');
  });
  document.querySelectorAll('.pane').forEach(p => { p.hidden = p.id !== 'pane-' + name; });
  try { localStorage.setItem('xiaotuan-tab', name); } catch (e) { /* 沒有儲存空間也沒關係 */ }
  if (name === 'notes') renderNotes();
}

const ACTIONS = {
  praise: actPraise, nuzzle: actNuzzle, call: actCall, soothe: actSoothe,
  scare: actScare, tease: actTease, snatch: actSnatchButton, mess: actMessNest,
  fakesad: actFakeSad, teddy: actHugTeddy
};

function tempLabel(v) { return v < 15 ? '嚴寒' : v < 35 ? '涼' : v < 65 ? '舒適' : v < 85 ? '暖' : '炎熱'; }
function windLabel(v) { return v < 10 ? '無風' : v < 40 ? '微風' : v < 70 ? '強風' : '狂風'; }
function rainLabel(v) { const sn = S.env.temp < 22; return v < 8 ? (sn ? '不下雪' : '不下雨') : v < 40 ? (sn ? '小雪' : '小雨') : v < 75 ? (sn ? '大雪' : '大雨') : (sn ? '暴風雪' : '暴雨'); }

function syncWeatherUI() {
  const env = S.env;
  $('#wTemp').value = env.temp; $('#wWind').value = env.wind; $('#wRain').value = env.rain;
  $('#wThunder').checked = env.thunder;
  $('#wTempV').textContent = tempLabel(env.temp);
  $('#wWindV').textContent = windLabel(env.wind);
  $('#wRainV').textContent = rainLabel(env.rain);
  $('#wRainName').textContent = env.temp < 22 ? '雪' : '雨';
}

const PRESETS = {
  clear: { temp: 50, wind: 5, rain: 0, thunder: false },
  coldsnap: { temp: 8, wind: 55, rain: 0, thunder: false },
  heat: { temp: 95, wind: 0, rain: 0, thunder: false },
  storm: { temp: 40, wind: 75, rain: 85, thunder: true },
  snow: { temp: 6, wind: 15, rain: 55, thunder: false }
};

function statusText() {
  const c = ctx(), B = S.B, parts = [];
  if (X.sleeping) parts.push('睡著了');
  if (c.freezing) parts.push('冷得發抖'); else if (c.cold) parts.push('有點冷');
  if (c.scorching) parts.push('熱到發暈'); else if (c.hot) parts.push('有點熱');
  if (c.soaked) parts.push('濕透了'); else if (c.wet) parts.push('濕答答');
  if (!X.sleeping && B.energy < 25) parts.push('想睡');
  if (B.full < 25) parts.push('肚子餓'); else if (B.full > 85) parts.push('吃得好飽');
  if (B.dizzy > 50) parts.push('頭暈');
  if (recentFright()) parts.push('驚魂未定');
  if (now() < X.jealousUntil) parts.push('在吃醋');
  if (S.T.grudge > 50) parts.push('在生你的氣'); else if (S.T.grudge > 25) parts.push('有點記仇');
  if (!parts.length) parts.push('舒舒服服');
  return parts.join('・');
}

function meter(name, v, cls, title) {
  return '<div class="meter ' + (cls || '') + '"' + (title ? ' title="' + title + '"' : '') + '><span>' + name + '</span><div class="bar"><i style="width:' + Math.round(v) + '%"></i></div><b>' + Math.round(v) + '</b></div>';
}

function renderNotesLive() {
  $('#status').textContent = '小團現在：' + statusText();
  const pane = $('#pane-notes');
  if (pane.hidden) return;
  const B = S.B, T = S.T;
  const feel = Math.round(B.feel);
  $('#bodyMeters').innerHTML =
    '<div class="meter feel"><span>體感</span><div class="bar bi"><i style="left:' + (50 + feel / 2) + '%"></i></div><b>' + (feel < -25 ? '冷' : feel > 25 ? '熱' : '剛好') + '</b></div>' +
    meter('濕度', B.wet, B.wet > 60 ? 'warn' : '') + meter('精神', B.energy, B.energy < 25 ? 'warn' : '') +
    meter('飽足', B.full, B.full < 25 ? 'warn' : '') + meter('頭暈', B.dizzy, B.dizzy > 50 ? 'warn' : '');
  $('#heartMeters').innerHTML = Object.keys(TRAIT_NAME).map(k => meter(TRAIT_NAME[k], T[k], k === 'trust' ? 'good' : (T[k] > 50 ? 'warn' : ''))).join('');
  $('#setNow').innerHTML = '<span class="mini-face">' + faceOf(X.curSet, 'calm') + '</span><div><b>' + FACESETS[X.curSet].name + '</b><small>' + SET_REASON[X.curSet] + '</small></div>';
}
UI.onSetChange = renderNotesLive;

function renderNotes() {
  renderNotesLive();
  const total = Object.keys(DISC).length;
  const found = Object.keys(S.disc).filter(k => DISC[k]);
  $('#discCount').textContent = found.length + ' / ' + total;
  let faceTotal = 0;
  for (const k in FACESETS) faceTotal += FACESETS[k].faces.length;
  $('#faceCount').textContent = Object.keys(S.faces).length + ' / ' + faceTotal;
  const sets = Object.keys(FACESETS).map(k => {
    const seen = Object.keys(S.faces).some(f => f.split(':')[0] === k);
    return '<span class="chip' + (seen ? '' : ' unseen') + '" title="' + (seen ? SET_REASON[k] : '還沒見過') + '">' + (seen ? FACESETS[k].name : '？？？') + '</span>';
  }).join('');
  $('#setChips').innerHTML = sets;
  const unfound = Object.keys(DISC).filter(k => !S.disc[k]);
  const hints = [];
  const pool = unfound.slice();
  for (let i = 0; i < 3 && pool.length; i++) hints.push(pool.splice(Math.floor(Math.random() * pool.length), 1)[0]);
  $('#hints').innerHTML = hints.length ? hints.map(k => '<li>試試看：' + DISC[k][1] + '</li>').join('') : '<li>全部都發現了！</li>';
  found.sort((a, b) => S.disc[b] - S.disc[a]);
  $('#discList').innerHTML = found.map(k => '<li><b>' + DISC[k][0] + '</b><small>' + DISC[k][1] + '</small></li>').join('') || '<li class="empty">還沒有發現。去製造一點情境吧。</li>';
  renderLog();
}

function renderLog() {
  $('#logList').innerHTML = X.log.slice(0, 40).map(logItem).join('') || '<li class="empty">還沒有紀錄。</li>';
}
function logItem(e) {
  return '<li><time>' + e.time + '</time><b>' + e.act + '</b>' + (e.face ? '<span class="lf">' + e.face + '</span>' : '') + '<span class="lt">' + e.text + '</span>' + (e.delta ? '<em>' + e.delta + '</em>' : '') + '</li>';
}
UI.onLog = function (e) {
  $('#ticker').innerHTML = logItem(e);
  if (!$('#pane-notes').hidden) renderLog();
};
UI.onDiscover = function () { if (!$('#pane-notes').hidden) renderNotes(); };
UI.onFacesChange = function () {};

// ----- 存檔 -----
function saveObj() {
  return { v: 1, env: S.env, T: S.T, B: S.B, c: S.c, aff: S.aff, loc: S.loc, nest: S.nest, sprout: S.sprout, wall: S.wall, disc: S.disc, faces: S.faces, hide: S.hide, played: S.played, set: X.curSet };
}
function save() {
  try { localStorage.setItem(SAVE_KEY, JSON.stringify(saveObj())); } catch (e) { /* 存不了就算了 */ }
}
function mergeState(d) {
  if (!d || d.v !== 1) return;
  ['env', 'T', 'B', 'c', 'aff', 'loc', 'nest', 'sprout'].forEach(k => { if (d[k]) Object.assign(S[k], d[k]); });
  ['wall', 'hide'].forEach(k => { if (Array.isArray(d[k])) S[k] = d[k]; });
  if (d.disc) S.disc = d.disc;
  if (d.faces) S.faces = d.faces;
  if (d.played) S.played = d.played;
  if (d.set && FACESETS[d.set] && !FACESETS[d.set].temp) X.curSet = d.set;
  // 上次離開時正在遊戲中的物品，回到小團身上
  for (const id in S.loc) {
    if (S.loc[id] === 'game' || S.loc[id] === 'carry' || S.loc[id] === 'tuan') S.loc[id] = (id === 'bell' || id === 'teddy') ? 'nest' : 'tray';
  }
}
function load() {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (raw) mergeState(JSON.parse(raw));
  } catch (e) { /* 讀不到就從頭開始 */ }
}

let resetArmed = 0;
function resetGame() {
  if (now() - resetArmed > 4000) {
    resetArmed = now();
    $('#resetBtn').textContent = '再按一次確認：忘掉一切重新認識';
    setTimeout(() => { $('#resetBtn').textContent = '重新認識小團'; }, 4000);
    return;
  }
  try { localStorage.removeItem(SAVE_KEY); } catch (e) { /* 忽略 */ }
  window.removeEventListener('beforeunload', save);
  location.reload();
}

// ----- 綁定 -----
function bindUI() {
  $('#nest-blanket').innerHTML = SVG_ICONS.blanket;
  $('#att-blanket').innerHTML = SVG_ICONS.blanket.replace('<svg ', '<svg preserveAspectRatio="none" ');
  document.querySelectorAll('.tabs button').forEach(b => b.addEventListener('click', () => setTab(b.dataset.tab)));
  document.querySelectorAll('[data-act]').forEach(b => b.addEventListener('click', () => { Sound.init(); ACTIONS[b.dataset.act](); }));
  $('#tbody').addEventListener('pointerdown', onTuanDown);
  ['held', 'umbrella', 'ice', 'blanket'].forEach(k => {
    $('#att-' + k).addEventListener('pointerdown', e => {
      const id = k === 'held' ? X.held : k;
      if (!id) return;
      dragFromTuan(e, id);
    });
  });
  ['blanket', 'teddy', 'bell'].forEach(id => $('#nest-' + id).addEventListener('pointerdown', e => dragItem(e, id, 'nest')));
  const pieces = $('#pieces');
  pieces.innerHTML = NEST_PIECES.map(p => '<span class="piece ' + (p.cls || '') + '" data-id="' + p.id + '">' + p.icon + '</span>').join('');
  pieces.querySelectorAll('.piece').forEach(el => el.addEventListener('pointerdown', onPieceDown));
  $('#stage').addEventListener('pointermove', onStageHover);
  $('#stage').addEventListener('contextmenu', e => e.preventDefault());
  $('#gamePanel').addEventListener('click', e => {
    const b = e.target.closest('[data-g]');
    if (b) Games.click(b.dataset.g);
  });
  const wInput = (id, key) => $(id).addEventListener('input', e => { Sound.init(); S.env[key] = +e.target.value; syncWeatherUI(); });
  wInput('#wTemp', 'temp'); wInput('#wWind', 'wind'); wInput('#wRain', 'rain');
  $('#wThunder').addEventListener('change', e => { Sound.init(); S.env.thunder = e.target.checked; UI.nextThunder = now() + 1500; });
  $('#wStrike').addEventListener('click', () => { Sound.init(); thunderStrike(); });
  document.querySelectorAll('[data-preset]').forEach(b => b.addEventListener('click', () => {
    Sound.init();
    Object.assign(S.env, PRESETS[b.dataset.preset]);
    UI.nextThunder = now() + 1500;
    syncWeatherUI();
  }));
  $('#soundBtn').addEventListener('click', () => {
    Sound.init();
    Sound.setOn(!Sound.on);
    $('#soundBtn').textContent = Sound.on ? '聲音：開' : '聲音：關';
    $('#soundBtn').setAttribute('aria-pressed', Sound.on ? 'true' : 'false');
  });
  $('#resetBtn').addEventListener('click', resetGame);
  window.addEventListener('keydown', e => {
    if (e.code === 'Space' && MG && MG.type === 'tug' && !e.target.closest('input,textarea')) { e.preventDefault(); tugCmd('pull'); Games.renderPanel(); }
  });
  window.addEventListener('resize', layoutStage);
  window.addEventListener('beforeunload', save);
  document.addEventListener('visibilitychange', () => { if (document.hidden) save(); });
}

// ----- 主迴圈 -----
let lastT = 0, tickAcc = 0, slowAcc = 0, saveAcc = 0;
function frame() {
  const t = now();
  const dt = Math.min(50, t - lastT);
  lastT = t;
  stepPhysics(dt);
  Games.tick(dt);
  tickAcc += dt;
  while (tickAcc >= 250) { tickAcc -= 250; bodyTick(); envTick(); }
  slowAcc += dt;
  if (slowAcc >= 1000) {
    slowAcc = 0;
    sproutTick();
    aiTick();
    refreshSet();
    renderSky();
    renderNotesLive();
    renderAttachments();
    renderNest();
    Sound.ambient(S.env.rain, S.env.wind);
  }
  saveAcc += dt;
  if (saveAcc > 5000) { saveAcc = 0; save(); }
  updateFace();
  renderTuan();
  drawWeather(dt);
  requestAnimationFrame(frame);
}

function start(hot) {
  load();
  if (hot && hot.S) mergeState(hot.S);
  initNestPieces(false);
  bindUI();
  layoutStage();
  syncWeatherUI();
  X.x = P.homeX; X.y = P.ground;
  X.lastInteract = now();
  UI.renderTray();
  renderAttachments();
  renderNest();
  renderPot();
  renderWall();
  renderSky();
  Games.renderPanel();
  let tab = 'act';
  try { tab = localStorage.getItem('xiaotuan-tab') || 'act'; } catch (e) { /* 預設分頁 */ }
  setTab(['act', 'weather', 'games', 'notes'].includes(tab) ? tab : 'act');
  updateFace(true);
  const returning = Object.keys(S.disc).length > 0;
  setTimeout(() => {
    if (S.T.grudge > 40) react({ emo: 'sulk', say: '…你回來了。哼。', act: '見面' });
    else if (returning) react({ emo: 'happy', say: '你回來了！', fx: 'heart', act: '見面' });
    else react({ emo: 'shy', say: '你好…我是小團。', fx: 'note', act: '見面' });
  }, 600);
  lastT = now();
  requestAnimationFrame(frame);
}

(function boot() {
  const hot = window.claude && window.claude.hot;
  try { if (hot && hot.snapshot) hot.snapshot(() => ({ S: saveObj() })); } catch (e) { /* 沒有也沒關係 */ }
  if (hot && hot.ready) hot.ready(start);
  else start((hot && hot.data) || {});
})();
