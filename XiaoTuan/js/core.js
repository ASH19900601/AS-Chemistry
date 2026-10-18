'use strict';
// ===== 基本工具 =====
const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
const rand = (a, b) => a + Math.random() * (b - a);
const pick = arr => arr[Math.floor(Math.random() * arr.length)];
const chance = p => Math.random() < p;
const now = () => performance.now();
const $ = (s, r) => (r || document).querySelector(s);
const lerp = (a, b, k) => a + (b - a) * k;

// ===== 舞台尺寸：舞台以固定的邏輯像素繪製，再整體縮放 =====
const L = { W: 1000, H: 600, scale: 1, narrow: false };
const P = {};

function computePositions() {
  if (L.narrow) {
    Object.assign(P, { ground: 0.84, nestX: 0.18, nestL: 0.02, nestR: 0.34, roofY: 0.44,
      potX: 0.88, homeX: 0.62, lineL: 0.40, lineR: 0.97, lineY: 0.09 });
  } else {
    Object.assign(P, { ground: 0.82, nestX: 0.155, nestL: 0.03, nestR: 0.28, roofY: 0.38,
      potX: 0.9, homeX: 0.56, lineL: 0.36, lineR: 0.78, lineY: 0.1 });
  }
}

// ===== 狀態：S 會存檔，X 只存在這一次遊玩 =====
const S = {
  env: { temp: 50, wind: 0, rain: 0, thunder: false },
  T: { trust: 50, grudge: 0, fear: 22, sorrow: 0, smug: 10, glutton: 10, snark: 0 },
  B: { feel: 0, wet: 0, energy: 80, full: 60, dizzy: 0, warmFx: 0 },
  c: { scare: 0, mess: 0, snatch: {}, woken: 0, doodle: 0, thunderAlone: 0, thunderHug: 0,
    tugLetGo: 0, tugStreakYou: 0, cheatBell: 0, spills: 0, tornDrawings: 0, fakeTrick: 0,
    soothe: 0, offenses: 0, snatchReturn: 0, bellSwapCaught: 0 },
  aff: { ice: 0, blanket: 0, tea: 0, cookie: 0, water: 0, fan: 0, umbrella: 0, bell: 6, teddy: 3, crayon: 0 },
  loc: { blanket: 'tray', umbrella: 'tray', bell: 'nest', teddy: 'tray' },
  nest: { pieces: {}, wet: 0, crumbs: false },
  sprout: { stage: -1, growth: 0, water: 50, health: 100, dead: false },
  wall: [],
  disc: {},
  faces: {},
  hide: [0, 0, 0],
  played: 0
};
const TRAIT_NAME = { trust: '信任', grudge: '記仇', fear: '膽怯', sorrow: '委屈', smug: '得意', glutton: '嘴饞', snark: '無語' };

const X = {
  x: 0.56, y: 0.82, vx: 0, vy: 0, airborne: false, target: null, walking: false,
  sleeping: false, carried: false, hugging: false, hugStart: 0, hugMarks: {},
  held: null, wear: { blanket: false, umbrella: false, ice: 0, doodle: false },
  fanUntil: 0, eatUntil: 0,
  emo: 'calm', emoUntil: 0, setOverride: 0, setOverrideUntil: 0, curSet: 1, setCand: 1, setCandSince: 0,
  lastInteract: 0, lastReact: -1e9, nextAI: 0, busyUntil: 0, hist: [],
  lastThunder: -1e9, lastScare: -1e9, lastCry: -1e9, lastGood: -1e9, lastLostTug: -1e9, lastFall: -1e9,
  snatched: null, snatchedAt: 0, fakeSadAt: -1e9, jealousUntil: 0, playfulUntil: 0, tidying: false,
  sleepFlags: { mess: false, doodle: false, snatched: null },
  rainPlay: false, umbrellaFlipAt: 0, lastFace: '', tdelta: {}, log: []
};

// ===== 特質與歷史 =====
function tr(k, d) {
  const before = S.T[k];
  S.T[k] = clamp(before + d, 0, 100);
  X.tdelta[k] = (X.tdelta[k] || 0) + (S.T[k] - before);
}
function body(k, d, lo, hi) {
  S.B[k] = clamp(S.B[k] + d, lo === undefined ? 0 : lo, hi === undefined ? 100 : hi);
}
function note(type) {
  const t = now();
  X.hist.push({ type, t });
  if (X.hist.length > 200) X.hist.splice(0, X.hist.length - 200);
}
function recent(type, ms) {
  const t = now();
  let n = 0;
  for (let i = X.hist.length - 1; i >= 0; i--) {
    if (t - X.hist[i].t > ms) break;
    if (X.hist[i].type === type) n++;
  }
  return n;
}
function touch() { X.lastInteract = now(); }
function offense(weight) { S.c.offenses += weight || 1; }
function recentFright() { const t = now(); return t - X.lastThunder < 7000 || t - X.lastScare < 6000; }
const later = (ms, fn) => setTimeout(fn, ms);

// ===== 體感 =====
function ctx() {
  const B = S.B;
  return {
    cold: B.feel < -25, freezing: B.feel < -55, hot: B.feel > 25, scorching: B.feel > 55,
    wet: B.wet > 40, soaked: B.wet > 70, sleepy: B.energy < 25, hungry: B.full < 30, full: B.full > 85
  };
}
function inNest() {
  return !X.carried && !X.airborne && X.x > P.nestL + 0.01 && X.x < P.nestR - 0.01;
}
function sheltered() { return inNest() || X.wear.umbrella; }
function snowing() { return S.env.rain > 8 && S.env.temp < 22; }

// ===== 臉型與表情 =====
function computeSet() {
  const T = S.T, B = S.B, t = now();
  if (X.setOverride && t < X.setOverrideUntil) return X.setOverride;
  if (B.dizzy > 60) return 16;
  if (T.grudge > 75) return 9;
  if (T.grudge > 52) return 17;
  if (T.grudge > 28) return T.trust > 55 ? 3 : 10;
  if (T.fear > 62) return 8;
  if (T.sorrow > 55) return 14;
  if (T.sorrow > 32) return T.trust > 45 ? 12 : 13;
  if (T.snark > 55) return 7;
  if (T.smug > 60) return 11;
  if (T.glutton > 60) return 5;
  if (T.trust > 80 && T.grudge < 10 && Math.abs(B.feel) < 30) return 15;
  return 1;
}

function refreshSet(force) {
  const t = now();
  const cand = computeSet();
  if (cand === X.curSet) { X.setCand = cand; return; }
  const isOverride = X.setOverride && t < X.setOverrideUntil && cand === X.setOverride;
  if (cand !== X.setCand) { X.setCand = cand; X.setCandSince = t; }
  if (force || isOverride || cand === 16 || t - X.setCandSince > 2500) {
    const old = X.curSet;
    X.curSet = cand;
    if (old !== cand) {
      logLine('底色', '小團的臉型變成「' + FACESETS[cand].name + '」：' + SET_REASON[cand]);
      UI.onSetChange && UI.onSetChange();
    }
    updateFace(true);
  }
}

function idleEmo() {
  const B = S.B, T = S.T, t = now();
  if (X.sleeping) return 'sleep';
  if (B.dizzy > 50) return 'dizzy';
  if (recentFright()) return 'afraid';
  if (X.hugging) {
    if (B.feel > 35) return 'speechless';
    if (T.grudge > 45) return 'sulk';
    return T.trust > 60 ? 'love' : 'shy';
  }
  if (X.carried) return T.fear > 55 || T.trust < 35 ? 'afraid' : 'happy';
  if (B.feel < -55) return 'cry';
  if (B.feel < -25) return 'sad';
  if (B.feel > 55) return 'dizzy';
  if (B.feel > 28) return 'speechless';
  if (B.wet > 65) return 'sad';
  if (B.full < 15) return 'sad';
  if (t < X.jealousUntil) return 'sulk';
  if (T.grudge > 60) return 'angry';
  if (T.grudge > 38) return 'sulk';
  if (T.sorrow > 45) return 'sad';
  if (B.energy < 22) return 'speechless';
  if (X.held === 'cookie' && t < X.eatUntil) return 'happy';
  if (t < X.playfulUntil) return 'happy';
  if (T.trust > 72 && T.grudge < 15) return 'happy';
  return 'calm';
}

function currentEmo() { return now() < X.emoUntil ? X.emo : idleEmo(); }
function faceOf(set, emo) { return FACESETS[set].faces[EMOS.indexOf(emo)]; }

function updateFace(force) {
  const emo = currentEmo();
  const f = faceOf(X.curSet, emo);
  if (f === X.lastFace && !force) return;
  const el = $('#tface');
  if (f !== X.lastFace) {
    el.textContent = f;
    el.classList.remove('pop');
    void el.offsetWidth;
    el.classList.add('pop');
  }
  X.lastFace = f;
  const key = X.curSet + ':' + emo;
  if (!S.faces[key]) {
    S.faces[key] = 1;
    UI.onFacesChange && UI.onFacesChange();
  }
}

function voice(text, emo) {
  const tone = EMO_TONE[emo] || 0;
  const s = X.curSet;
  if (s === 3 && tone > 0 && chance(0.45)) return text + line('voice_tsun_pos');
  if (s === 7 && chance(0.45)) return tone > 0 ? line('voice_snark_pos') + text : text + line('voice_snark_neg');
  if (s === 8 && tone < 0 && chance(0.5)) return line('voice_timid_neg') + text;
  if (s === 9 && tone < 0) return text + line('voice_rage_neg');
  if (s === 10 && tone < 0 && chance(0.5)) return text + line('voice_pout_neg');
  if (s === 11 && tone > 0 && chance(0.5)) return text + line('voice_smug_pos');
  if (s === 5 && chance(0.2)) return text + line('voice_glutton');
  if ((s === 13 || s === 14) && chance(0.5)) return line('voice_gloomy_pre') + text;
  if (s === 15 && tone >= 0 && chance(0.35)) return text + line('voice_calm_suf');
  if (s === 2 && chance(0.4)) return text + line('voice_caring_suf');
  return text;
}

// ===== 對話泡泡、日誌、發現、特效 =====
let bubbleTimer = 0;
function say(text, ms) {
  const b = $('#bubble');
  b.textContent = text;
  b.hidden = false;
  b.classList.remove('show');
  void b.offsetWidth;
  b.classList.add('show');
  clearTimeout(bubbleTimer);
  bubbleTimer = setTimeout(() => { b.hidden = true; }, ms || 3000);
  Sound.chirp();
}

function deltaText() {
  const parts = [];
  for (const k in X.tdelta) {
    const d = X.tdelta[k];
    if (Math.abs(d) >= 1) parts.push(TRAIT_NAME[k] + (d > 0 ? '↑' : '↓'));
  }
  X.tdelta = {};
  return parts.join(' ');
}

function logLine(act, text, face) {
  const d = new Date();
  const entry = {
    time: String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0'),
    act, text, face: face || '', delta: face === undefined ? '' : deltaText()
  };
  X.log.unshift(entry);
  if (X.log.length > 60) X.log.pop();
  UI.onLog && UI.onLog(entry);
}

function discover(id) {
  if (!DISC[id]) { console.warn('unknown discovery', id); return; }
  if (S.disc[id]) return;
  S.disc[id] = Date.now();
  toast('新發現：' + DISC[id][0]);
  UI.onDiscover && UI.onDiscover();
}

let toastTimer = 0;
function toast(text) {
  const el = $('#toast');
  el.textContent = text;
  el.classList.remove('show');
  void el.offsetWidth;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2600);
}

const FX_CHAR = { heart: '♡', anger: '💢', tear: '💧', sparkle: '✧', zzz: 'z', sweat: '💦', excl: '!', ques: '?', note: '♪', star: '★', shiver: '〰', steam: '♨', crumb: '·' };
function burst(type, n, at) {
  const layer = $('#fx');
  const r = tuanRect();
  const cx = at ? at.x : r.left + r.width / 2;
  const cy = at ? at.y : r.top + 10;
  for (let i = 0; i < (n || 3); i++) {
    const s = document.createElement('span');
    s.className = 'fx fx-' + type;
    s.textContent = FX_CHAR[type] || type;
    s.style.left = (cx + rand(-r.width * 0.45, r.width * 0.45)) + 'px';
    s.style.top = (cy + rand(-20, 20)) + 'px';
    s.style.animationDelay = (i * 0.12) + 's';
    s.style.setProperty('--dx', rand(-40, 40) + 'px');
    layer.appendChild(s);
    setTimeout(() => s.remove(), 2200 + i * 120);
  }
}

function playAnim(name) {
  const w = $('#twrap');
  w.classList.remove('a-bounce', 'a-shake', 'a-jump', 'a-struggle', 'a-shrink', 'a-nod', 'a-spin', 'a-dodge', 'a-squish', 'a-tumble');
  void w.offsetWidth;
  w.classList.add('a-' + name);
}

// 一個反應：表情、台詞、動畫、特效、日誌
function react(o) {
  const t = now();
  if (o.over) {
    X.setOverride = o.over;
    X.setOverrideUntil = t + (o.overDur || 12000);
    if (o.over === 18) discover('shock_face');
  }
  refreshSet(!!o.over);
  if (o.emo) {
    X.emo = o.emo;
    X.emoUntil = t + (o.dur || 2800);
    if (o.emo === 'cry') X.lastCry = t;
  }
  updateFace(true);
  let text = '';
  if (o.say) {
    text = o.raw ? o.say : voice(o.say, o.emo || currentEmo());
    say(text, (o.dur || 2800) + 700);
  }
  if (o.anim) playAnim(o.anim);
  if (o.fx) burst(o.fx, o.n || 3);
  if (o.snd && Sound[o.snd]) Sound[o.snd]();
  if (o.disc) discover(o.disc);
  if (o.act) logLine(o.act, text || '（' + EMO_NAME[o.emo || currentEmo()] + '）', X.lastFace);
  X.lastReact = t;
  X.nextAI = Math.max(X.nextAI, t + 3500);
}

// ===== 移動與物理 =====
function walkTo(fx, cb) {
  if (X.sleeping) return;
  X.target = { x: clamp(fx, 0.07, 0.93), cb };
}
function stopWalk() { X.target = null; X.walking = false; }

function stepPhysics(dt) {
  if (X.carried) return;
  if (X.airborne) {
    X.vy += 0.0000032 * dt;
    X.x += X.vx * dt;
    X.y += X.vy * dt;
    if (X.x < 0.07) { X.x = 0.07; X.vx = -X.vx * 0.5; }
    if (X.x > 0.93) { X.x = 0.93; X.vx = -X.vx * 0.5; }
    if (X.y >= P.ground) {
      X.y = P.ground;
      if (Math.abs(X.vy) > 0.0012) {
        X.vy = -X.vy * 0.35;
        X.vx *= 0.6;
        Sound.pop();
      } else {
        X.airborne = false; X.vx = 0; X.vy = 0;
        if (X.onLand) { const f = X.onLand; X.onLand = null; f(); }
      }
    }
    return;
  }
  if (X.y < P.ground - 0.002) { X.airborne = true; X.vx = 0; X.vy = 0; return; }
  X.y = P.ground;
  // 強風會把不在小窩裡的小團往旁邊推
  if (S.env.wind > 70 && !inNest() && !X.sleeping && !X.target) {
    X.x = clamp(X.x + (S.env.wind - 70) * 0.0000012 * dt, 0.07, 0.93);
  }
  if (X.target && !X.sleeping) {
    const dx = X.target.x - X.x;
    const speed = 0.00016 * (S.B.energy < 20 ? 0.6 : 1) * (S.B.dizzy > 50 ? 0.5 : 1);
    const step = speed * dt;
    X.walking = true;
    if (Math.abs(dx) <= step) {
      X.x = X.target.x;
      const cb = X.target.cb;
      X.target = null; X.walking = false;
      if (cb) cb();
    } else {
      X.x += Math.sign(dx) * step;
    }
  } else {
    X.walking = false;
  }
}

// ===== 繪製 =====
let tuanSize = { w: 200, h: 90 };
function tuanRect() {
  return { left: X.x * L.W - tuanSize.w / 2, top: X.y * L.H - tuanSize.h, width: tuanSize.w, height: tuanSize.h };
}

function renderTuan() {
  const el = $('#tuan');
  const bodyEl = $('#tbody');
  tuanSize = { w: bodyEl.offsetWidth, h: bodyEl.offsetHeight };
  el.style.left = (X.x * L.W) + 'px';
  el.style.top = (X.y * L.H) + 'px';
  const c = ctx();
  const cls = el.classList;
  cls.toggle('s-sleep', X.sleeping);
  cls.toggle('s-cold', c.cold && !X.sleeping);
  cls.toggle('s-hot', c.hot);
  cls.toggle('s-wet', S.B.wet > 35);
  cls.toggle('s-dizzy', S.B.dizzy > 50);
  cls.toggle('s-carried', X.carried);
  cls.toggle('s-hug', X.hugging);
  cls.toggle('s-walk', X.walking);
  cls.toggle('s-air', X.airborne);
  el.style.setProperty('--tint', tintColor());
  // 影子
  const sh = $('#tshadow');
  const lift = clamp((P.ground - X.y) * L.H, 0, 400);
  sh.style.transform = 'translate(-50%, ' + lift + 'px) scale(' + clamp(1 - lift / 400, 0.3, 1) + ')';
  sh.style.opacity = clamp(0.5 - lift / 800, 0.1, 0.5);
  // 對話泡泡
  const b = $('#bubble');
  if (!b.hidden) {
    const bw = b.offsetWidth;
    const bx = clamp(X.x * L.W, bw / 2 + 8, L.W - bw / 2 - 8);
    b.style.left = bx + 'px';
    b.style.top = Math.max(8, X.y * L.H - tuanSize.h - 26 - b.offsetHeight - (X.wear.umbrella ? 52 : 0) - (iceOn() ? 26 : 0)) + 'px';
    b.style.setProperty('--tail', clamp(X.x * L.W - bx + bw / 2, 18, bw - 18) + 'px');
  }
}

function tintColor() {
  const f = S.B.feel;
  if (f < -20) return 'rgba(140, 180, 235, ' + clamp((-f - 20) / 80, 0, 0.55) + ')';
  if (f > 20) return 'rgba(250, 140, 110, ' + clamp((f - 20) / 80, 0, 0.5) + ')';
  return 'rgba(0,0,0,0)';
}

function iceOn() { return X.wear.ice > now(); }

function itemIconHTML(id) {
  const it = ITEMS[id];
  return it.svg ? SVG_ICONS[it.svg] : it.icon;
}

function renderAttachments() {
  const held = $('#att-held');
  held.hidden = !X.held;
  if (X.held && held.dataset.item !== X.held) { held.innerHTML = itemIconHTML(X.held); held.dataset.item = X.held; }
  $('#att-umbrella').hidden = !X.wear.umbrella;
  const ice = $('#att-ice');
  ice.hidden = !iceOn();
  if (iceOn()) ice.style.transform = 'translateX(-50%) scale(' + clamp((X.wear.ice - now()) / 25000, 0.35, 1) + ')';
  $('#att-blanket').hidden = !X.wear.blanket;
  $('#tdoodle').hidden = !X.wear.doodle;
  UI.renderTray && UI.renderTray();
}

// ===== 小窩 =====
function nestGeom() {
  const cx = P.nestX * L.W;
  const cy = P.ground * L.H - 26;
  const hw = (P.nestR - P.nestL) * L.W * 0.34;
  return { cx, cy, hw, hh: 46 };
}
function pieceHome(p) {
  const g = nestGeom();
  return { x: g.cx + p.hx * g.hw, y: g.cy + p.hy * g.hh };
}
function initNestPieces(reset) {
  NEST_PIECES.forEach(p => {
    if (reset || !S.nest.pieces[p.id]) S.nest.pieces[p.id] = { dx: 0, dy: 0 };
  });
}
function piecePos(p) {
  const h = pieceHome(p);
  const o = S.nest.pieces[p.id];
  return { x: h.x + o.dx * L.W, y: h.y + o.dy * L.H };
}
function nestTidy() {
  let pen = 0;
  NEST_PIECES.forEach(p => {
    const o = S.nest.pieces[p.id];
    const d = Math.hypot(o.dx * L.W, o.dy * L.H);
    pen += Math.min(25, d / 5);
  });
  if (S.nest.crumbs) pen += 15;
  return clamp(100 - pen, 0, 100);
}
function renderNest() {
  NEST_PIECES.forEach(p => {
    const el = document.querySelector('.piece[data-id="' + p.id + '"]');
    if (!el) return;
    const pos = piecePos(p);
    el.style.left = pos.x + 'px';
    el.style.top = pos.y + 'px';
  });
  const nest = $('#nest');
  nest.classList.toggle('wet', S.nest.wet > 25);
  nest.classList.toggle('crumbs', S.nest.crumbs);
  ['blanket', 'teddy', 'bell'].forEach(id => {
    const el = $('#nest-' + id);
    if (el) el.hidden = S.loc[id] !== 'nest';
  });
}

// ===== 小團的行為反應 =====
function wakeUp(kind) {
  if (!X.sleeping) return;
  X.sleeping = false;
  note('woken');
  if (kind === 'grumpy') {
    S.c.woken++;
    const n = recent('woken', 90000);
    tr('grudge', 2 + n * 2);
    offense();
    if (n >= 2) react({ emo: 'cry', say: line('woken_repeat'), anim: 'shake', fx: 'anger', disc: 'woken_repeat', act: '吵醒牠' });
    else react({ emo: 'angry', say: line('woken_grumpy'), anim: 'shake', fx: 'anger', disc: 'woken_grumpy', act: '吵醒牠' });
  }
  later(3200, checkAfterWake);
}

function checkAfterWake() {
  const f = X.sleepFlags;
  if (f.doodle && X.wear.doodle) {
    f.doodle = false;
    tr('grudge', 3);
    react({ emo: 'startle', say: line('wake_doodle'), anim: 'jump', fx: 'excl', disc: 'doodle_sleep', act: '醒來發現' });
    return;
  }
  if (f.snatched) {
    const id = f.snatched;
    f.snatched = null;
    if (S.loc[id] !== 'tuan') {
      tr('sorrow', 6); tr('grudge', 3);
      react({ emo: 'sad', say: line('wake_item_gone', { item: ITEMS[id].sname }), fx: 'tear', disc: 'snatch_sleep_discover', act: '醒來發現' });
      return;
    }
  }
  if (f.mess && nestTidy() < 75) {
    f.mess = false;
    tr('grudge', 4);
    react({ emo: 'angry', say: line('wake_nest_messed'), anim: 'shake', disc: 'mess_discovered_later', act: '醒來發現' });
  }
}

function fallAsleep(text) {
  X.sleeping = true;
  stopWalk();
  X.tidying = false;
  X.emoUntil = 0;
  say(text || line('fall_asleep'), 2200);
  burst('zzz', 3);
  logLine('睡覺', '小團睡著了。', X.lastFace);
}

// ----- 點擊 -----
function actTap(region) {
  touch();
  note('tap');
  const n = recent('tap', 4000);
  const T = S.T, B = S.B;
  Sound.pop();
  if (X.sleeping) {
    if (region === 'head' && T.trust > 60 && n <= 1) {
      tr('trust', 1);
      react({ emo: 'sleep', say: line('tap_sleep_pat'), fx: 'heart', n: 2, disc: 'tap_sleep_pat', act: '摸睡著的頭' });
    } else wakeUp('grumpy');
    return;
  }
  if (n >= 5) {
    tr('grudge', 3); tr('snark', 3); offense(0.5);
    if (T.fear > 55) react({ emo: 'afraid', say: line('tap_spam_fear'), anim: 'shrink', disc: 'tap_spam_fear', act: '一直戳' });
    else if (T.snark > 45) react({ emo: 'speechless', say: line('tap_spam_snark'), disc: 'tap_spam_snark', act: '一直戳' });
    else react({ emo: 'angry', say: line('tap_spam'), anim: 'shake', fx: 'anger', disc: 'tap_spam', act: '一直戳' });
    return;
  }
  if (region === 'head') {
    if (B.wet > 50) { tr('trust', 0.5); react({ emo: 'sulk', say: line('pat_wet'), fx: 'tear', n: 1, disc: 'pat_wet', act: '摸頭' }); }
    else if (T.grudge > 45) { tr('grudge', -1); react({ emo: 'angry', say: line('pat_dodge'), anim: 'dodge', disc: 'pat_dodge', act: '摸頭' }); }
    else if (T.grudge > 20) { tr('grudge', -1.5); react({ emo: 'sulk', say: line('pat_sulk'), disc: 'pat_sulk', act: '摸頭' }); }
    else if (T.trust > 65) { tr('trust', 1); tr('sorrow', -1); react({ emo: 'happy', say: line('pat_happy'), fx: 'heart', n: 2, anim: 'nod', disc: 'pat_happy', act: '摸頭' }); }
    else { tr('trust', 1.5); react({ emo: 'shy', say: line('pat_shy'), anim: 'nod', act: '摸頭' }); }
  } else {
    if (B.full > 85) react({ emo: 'speechless', say: line('poke_full'), disc: 'poke_full', act: '戳肚子' });
    else if (B.full < 20) react({ emo: 'sad', say: line('poke_hungry'), disc: 'poke_hungry', act: '戳肚子' });
    else if (T.trust > 50 && T.grudge < 25) react({ emo: 'happy', say: line('poke_tickle'), anim: 'bounce', fx: 'note', disc: 'poke_tickle', act: '戳肚子' });
    else react({ emo: 'speechless', say: line('poke_meh'), act: '戳肚子' });
  }
}

// ----- 長按：抱抱 -----
function hugBegin() {
  touch();
  note('hug');
  X.hugging = true;
  X.hugStart = now();
  X.hugMarks = {};
  stopWalk();
  const T = S.T, c = ctx(), t = now();
  if (X.sleeping) {
    if (T.trust > 55) { X.hugMarks.sleep = true; react({ emo: 'sleep', say: line('hug_sleep'), fx: 'heart', n: 2, disc: 'hug_sleep', act: '抱睡著的牠' }); }
    else {
      X.sleeping = false; tr('fear', 3);
      react({ emo: 'startle', say: line('hug_sleep_startle'), anim: 'jump', fx: 'excl', disc: 'hug_sleep_startle', act: '抱睡著的牠' });
    }
    return;
  }
  if (recentFright()) {
    tr('fear', -4); tr('trust', 3);
    const thunder = t - X.lastThunder < 7000;
    if (thunder) S.c.thunderHug++;
    react({ emo: 'moved', say: line('hug_scared'), fx: 'tear', n: 2, disc: thunder ? 'hug_thunder' : 'hug_scared', act: '抱抱' });
    return;
  }
  if (t < X.jealousUntil) {
    X.jealousUntil = 0; tr('trust', 2);
    react({ emo: 'moved', say: line('jealous_hug'), fx: 'heart', disc: 'jealous_hug', act: '抱抱' });
    return;
  }
  if (T.grudge > 55) { react({ emo: 'angry', say: line('hug_angry'), anim: 'struggle', fx: 'anger', disc: 'hug_angry_struggle', act: '抱抱' }); return; }
  if (T.grudge > 25) { react({ emo: 'sulk', say: line('hug_sulk'), act: '抱抱' }); return; }
  if (recent('hug', 30000) >= 4) { react({ emo: 'shy', say: line('hug_many'), fx: 'heart', disc: 'hug_many', act: '抱抱' }); return; }
  if (c.cold) { react({ emo: 'happy', say: line('hug_cold'), fx: 'heart', disc: 'hug_cold', act: '抱抱' }); return; }
  if (c.hot) { react({ emo: 'speechless', say: line('hug_hot'), fx: 'sweat', n: 2, disc: 'hug_hot', act: '抱抱' }); return; }
  if (c.wet) { tr('trust', 2); react({ emo: 'moved', say: line('hug_wet'), fx: 'heart', disc: 'hug_wet', act: '抱抱' }); return; }
  react({ emo: T.trust > 60 ? 'love' : 'shy', say: line('hug_basic'), fx: 'heart', act: '抱抱' });
}

function hugTick() {
  const d = now() - X.hugStart;
  const m = X.hugMarks, c = ctx(), T = S.T;
  if (X.sleeping) {
    if (d > 2500 && !m.sleepTrust) { m.sleepTrust = true; tr('trust', 2); }
    return;
  }
  if (c.hot && d > (c.scorching ? 1500 : 3000) && !m.hot) {
    m.hot = true; tr('grudge', 2);
    react({ emo: 'angry', say: line('hug_too_hot'), anim: 'struggle', fx: 'sweat', disc: 'hug_too_hot', act: '抱太久' });
    return;
  }
  if (T.grudge > 25 && d > 3000 && !m.melt) {
    m.melt = true; tr('grudge', -8); tr('trust', 1);
    react({ emo: 'shy', say: line('hug_melt'), disc: 'hug_melt_grudge', act: '一直抱著' });
    return;
  }
  if (d > 5000 && !m.drowsy && S.B.energy < 45 && !c.hot) {
    m.drowsy = true;
    fallAsleep(line('hug_fall_asleep'));
    discover('hug_fall_asleep');
    return;
  }
  if (d > 9000 && !m.long) {
    m.long = true;
    if (T.trust > 80 || c.cold) react({ emo: 'love', say: line('hug_long_love'), fx: 'heart', act: '抱很久' });
    else { tr('snark', 3); react({ emo: 'speechless', say: line('hug_too_long'), disc: 'hug_too_long', act: '抱很久' }); }
  }
}

function hugEnd() {
  const d = now() - X.hugStart;
  X.hugging = false;
  touch();
  const c = ctx(), T = S.T;
  if (X.sleeping) { if (d > 1000) tr('trust', 1); return; }
  if (d < 900 && T.trust > 60 && T.grudge < 20) {
    react({ emo: 'sulk', say: line('hug_short'), disc: 'hug_short', act: '放開' });
    return;
  }
  if (!X.hugMarks.hot && !(T.grudge > 55)) {
    tr('trust', Math.min(4, d / 1200));
    tr('grudge', -Math.min(5, d / 1500));
    tr('sorrow', -Math.min(5, d / 1500));
    tr('fear', -Math.min(3, d / 2500));
  }
  if (now() - X.lastThunder < 9000 && S.env.thunder) react({ emo: 'afraid', say: line('hug_release_thunder'), anim: 'shrink', act: '放開' });
}

// ----- 拖動：拎起來、甩、丟 -----
function carryBegin() {
  touch();
  note('carry');
  X.carried = true;
  X.airborne = false;
  stopWalk();
  X.tidying = false;
  X.carryFrom = inNestAt(X.x);
  const T = S.T;
  if (X.sleeping) {
    if (T.trust > 65) { react({ emo: 'sleep', say: line('carry_sleep'), disc: 'carry_sleep', act: '搬動睡著的牠' }); return; }
    X.sleeping = false; tr('fear', 3);
    react({ emo: 'startle', say: line('carry_wake'), anim: 'jump', fx: 'excl', act: '搬動睡著的牠' });
    return;
  }
  if (T.fear > 60 || T.trust < 30) react({ emo: 'afraid', say: line('carry_fear'), disc: 'carry_fear', act: '拎起來' });
  else if (T.grudge > 45) react({ emo: 'angry', say: line('carry_angry'), anim: 'struggle', act: '拎起來' });
  else if (S.B.energy > 55 && T.trust > 55) react({ emo: 'happy', say: line('carry_fly'), fx: 'note', disc: 'carry_fly', act: '拎起來' });
  else react({ emo: 'startle', say: line('carry_startle'), act: '拎起來' });
}

function inNestAt(fx) { return fx > P.nestL + 0.01 && fx < P.nestR - 0.01; }

function carryShake(amount) {
  const before = S.B.dizzy;
  body('dizzy', amount);
  if (X.sleeping && S.B.dizzy > 30) { X.sleeping = false; }
  if (before < 50 && S.B.dizzy >= 50) {
    tr('grudge', 1);
    react({ emo: 'dizzy', say: line('shake_dizzy'), fx: 'star', disc: 'shake_dizzy', act: '甩來甩去' });
  } else if (before < 88 && S.B.dizzy >= 88) {
    tr('grudge', 3); offense();
    react({ emo: 'dizzy', say: line('shake_sick'), fx: 'sweat', disc: 'shake_sick', act: '甩來甩去' });
  }
}

function carryHigh() {
  if (X.sleeping || X.highSaid) return;
  X.highSaid = true;
  if (S.T.fear > 50) { tr('fear', 2); react({ emo: 'cry', say: line('carry_high_fear'), fx: 'tear', disc: 'carry_high_fear', act: '舉高' }); }
  else react({ emo: 'sparkle', say: line('carry_high'), fx: 'sparkle', disc: 'carry_high', act: '舉高高' });
}

function carryEnd(vx, vy) {
  X.carried = false;
  X.highSaid = false;
  touch();
  const speed = Math.hypot(vx, vy);
  const T = S.T;
  if (speed > 1.1 && !X.sleeping) {
    // 丟出去：速度是邏輯像素/毫秒，換成比例
    X.airborne = true;
    X.vx = clamp(vx / L.W, -0.0025, 0.0025);
    X.vy = clamp(vy / L.H, -0.004, 0.003);
    note('throw');
    X.onLand = () => {
      body('dizzy', 15);
      X.lastFall = now();
      if (T.trust > 65 && T.grudge < 20 && T.fear < 40) {
        X.playfulUntil = now() + 20000;
        react({ emo: 'happy', say: line('throw_fun'), fx: 'star', anim: 'bounce', over: 4, overDur: 20000, disc: 'throw_fun', act: '丟出去' });
        discover('playful_mode');
      } else if (T.fear > 50) {
        tr('fear', 5); tr('grudge', 3); offense();
        react({ emo: 'cry', say: line('throw_cry'), fx: 'tear', anim: 'shrink', disc: 'throw_cry', act: '丟出去' });
      } else {
        tr('grudge', 5); offense();
        react({ emo: 'angry', say: line('throw_angry'), fx: 'anger', anim: 'shake', disc: 'throw_angry', act: '丟出去' });
      }
    };
    return;
  }
  if (X.y < P.ground - 0.01) { X.airborne = true; X.vx = 0; X.vy = 0; }
  const land = () => afterSetDown();
  if (X.airborne) X.onLand = land; else land();
}

function afterSetDown() {
  if (X.sleeping) return;
  const env = S.env;
  const nowIn = inNest();
  if (nowIn && !X.carryFrom) {
    if (S.nest.wet > 30) { tr('grudge', 1); react({ emo: 'angry', say: line('nest_drop_wet'), act: '放進小窩' }); return; }
    if (nestTidy() < 60) { react({ emo: 'sad', say: line('nest_drop_messy'), disc: 'nest_messy_drop', act: '放進小窩' }); return; }
    if (env.rain > 15 || env.thunder || S.B.feel < -25 || env.wind > 60) {
      tr('trust', 2);
      react({ emo: 'happy', say: line('nest_drop_safe'), fx: 'heart', disc: 'carry_to_nest', act: '放進小窩' });
      return;
    }
    react({ emo: 'calm', say: line('nest_drop'), act: '放進小窩' });
    return;
  }
  if (!nowIn && X.carryFrom && env.rain > 15 && !X.wear.umbrella) {
    tr('grudge', 4); offense();
    react({ emo: 'angry', say: line('carry_into_rain'), anim: 'shake', disc: 'carry_into_rain', act: '抱出小窩' });
    later(2500, () => { if (!X.carried && !inNest() && S.env.rain > 15) walkTo(P.nestX); });
    return;
  }
  if (S.B.dizzy > 50) { discover('dizzy_walk'); react({ emo: 'dizzy', say: line('set_down_dizzy'), anim: 'spin', act: '放下' }); return; }
  if (Math.abs(X.x - P.potX) < 0.08 && S.sprout.stage >= 0 && !S.sprout.dead) {
    react({ emo: 'happy', say: line('visit_sprout'), act: '帶去看芽' });
  }
}

// ----- 動作按鈕 -----
function actPraise() {
  touch(); note('praise');
  const n = recent('praise', 20000), T = S.T, t = now();
  if (X.sleeping) { tr('trust', 1); react({ emo: 'sleep', say: line('praise_sleep'), fx: 'heart', disc: 'praise_sleep', act: '誇獎' }); return; }
  if (X.wear.doodle && chance(0.6)) { tr('snark', 2); react({ emo: 'speechless', say: line('praise_doodled'), disc: 'praise_doodled', act: '誇獎' }); return; }
  if (t - X.lastGood < 15000) { tr('smug', 5); tr('trust', 2); X.lastGood = 0; react({ emo: 'smug', say: line('praise_achievement'), fx: 'sparkle', anim: 'bounce', disc: 'praise_achievement', act: '誇獎' }); return; }
  if (t - X.lastCry < 8000 || T.sorrow > 50) { tr('sorrow', -6); tr('trust', 2); react({ emo: 'moved', say: line('praise_crying'), fx: 'tear', disc: 'praise_crying', act: '誇獎' }); return; }
  if (T.grudge > 50) { tr('grudge', -2); react({ emo: 'sulk', say: line('praise_grudge'), disc: 'praise_grudge', act: '誇獎' }); return; }
  if (T.grudge > 20) { tr('grudge', -3); react({ emo: 'shy', say: line('praise_tsundere'), disc: 'praise_tsundere', act: '誇獎' }); return; }
  if (n >= 4) { tr('snark', 4); react({ emo: 'speechless', say: line('praise_spam'), disc: 'praise_spam', act: '一直誇' }); return; }
  if (n >= 2) { tr('trust', 1); react({ emo: 'shy', say: line('praise_shy'), fx: 'heart', disc: 'praise_shy', act: '誇獎' }); return; }
  tr('trust', 2); tr('sorrow', -2);
  if (T.trust > 70) react({ emo: 'love', say: line('praise_love'), fx: 'heart', act: '誇獎' });
  else react({ emo: 'happy', say: line('praise_happy'), fx: 'note', act: '誇獎' });
}

function actNuzzle() {
  touch(); note('nuzzle');
  const T = S.T, c = ctx();
  if (X.sleeping) {
    if (T.trust > 60) { tr('trust', 1); react({ emo: 'sleep', say: line('nuzzle_sleep'), fx: 'heart', disc: 'nuzzle_sleep', act: '貼貼' }); }
    else wakeUp('grumpy');
    return;
  }
  if (T.grudge > 45) { tr('grudge', -0.5); react({ emo: 'angry', say: line('nuzzle_reject'), anim: 'dodge', disc: 'nuzzle_reject', act: '貼貼' }); return; }
  if (c.hot) { react({ emo: 'speechless', say: line('nuzzle_hot'), fx: 'sweat', disc: 'nuzzle_hot', act: '貼貼' }); return; }
  if (X.wear.doodle) { react({ emo: 'shy', say: line('nuzzle_doodle'), disc: 'nuzzle_doodle', act: '貼貼' }); return; }
  if (c.wet) { react({ emo: 'shy', say: line('nuzzle_wet'), disc: 'nuzzle_wet', act: '貼貼' }); return; }
  if (c.cold) { tr('trust', 2); body('warmFx', 6, -40, 40); react({ emo: 'love', say: line('nuzzle_cold'), fx: 'heart', disc: 'nuzzle_cold', act: '貼貼' }); return; }
  if (recent('nuzzle', 20000) >= 4) { react({ emo: 'shy', say: line('nuzzle_many'), act: '貼貼' }); return; }
  tr('trust', 2); tr('grudge', -1);
  if (T.trust > 60) react({ emo: 'love', say: line('nuzzle_love'), fx: 'heart', anim: 'squish', disc: 'nuzzle_love', act: '貼貼' });
  else react({ emo: 'shy', say: line('nuzzle_shy'), anim: 'squish', act: '貼貼' });
}

function actScare() {
  touch(); note('scare');
  const n = recent('scare', 40000), T = S.T;
  S.c.scare++;
  Sound.squeak();
  if (X.sleeping) {
    X.sleeping = false; X.lastScare = now();
    tr('fear', 8); tr('grudge', 6); offense(1.5);
    react({ emo: 'startle', say: line('scare_sleep'), anim: 'jump', fx: 'excl', over: 18, overDur: 9000, disc: 'scare_sleep', act: '嚇睡著的牠' });
    later(1500, () => react({ emo: T.fear > 50 ? 'cry' : 'angry', say: line(T.fear > 50 ? 'scare_sleep_cry' : 'scare_sleep_angry'), fx: T.fear > 50 ? 'tear' : 'anger' }));
    return;
  }
  if (T.smug > 55 && n <= 1 && chance(0.55)) {
    tr('smug', 3);
    react({ emo: 'smug', say: line('scare_back'), anim: 'jump', disc: 'scare_back', act: '嚇牠' });
    return;
  }
  if (n >= 3) {
    tr('snark', 5); tr('grudge', 2);
    react({ emo: 'speechless', say: line('scare_habituated'), disc: 'scare_habituated', act: '嚇牠' });
    return;
  }
  X.lastScare = now();
  offense();
  if (now() - X.lastThunder < 10000 || T.fear > 65) {
    tr('fear', 10); tr('grudge', 4); tr('sorrow', 4);
    react({ emo: 'cry', say: line('scare_cry'), anim: 'jump', fx: 'tear', n: 4, over: 18, overDur: 10000, disc: 'scare_cry', act: '嚇牠' });
    later(1800, () => { if (!X.carried && !X.hugging) walkTo(P.nestX); });
    return;
  }
  if (X.held === 'teddy' || inNest()) {
    tr('fear', 3);
    react({ emo: 'startle', say: line('scare_with_teddy'), anim: 'jump', disc: 'scare_with_teddy', act: '嚇牠' });
    return;
  }
  tr('fear', 6); tr('grudge', 3);
  react({ emo: 'startle', say: line('scare_basic'), anim: 'jump', fx: 'excl', disc: 'scare_basic', act: '嚇牠' });
  if (X.held && X.held !== 'cookie' && chance(0.6)) {
    const it = X.held;
    later(700, () => {
      if (X.held !== it) return;
      react({ emo: 'afraid', say: line('scare_drop', { item: ITEMS[it].sname }), disc: 'scare_drop_item' });
      X.held = null; renderAttachments();
      later(1300, () => { if (!X.held && S.loc[it] === 'tuan') { X.held = it; renderAttachments(); react({ emo: 'sulk', say: line('scare_pickup')}); } });
    });
    return;
  }
  later(1300, () => {
    if (T.trust > 60) react({ emo: 'sulk', say: line('scare_after_trust'), fx: 'anger' });
    else react({ emo: 'afraid', say: line('scare_after_fear'), anim: 'shrink' });
  });
  if (n === 0 && T.fear > 40) later(1400, () => react({ over: 18, overDur: 6000 }));
}

function actTease() {
  touch(); note('tease');
  const T = S.T, t = now(), B = S.B;
  if (X.sleeping) { react({ emo: 'sleep', say: line('tease_sleep'), act: '取笑' }); return; }
  if (t - X.fakeSadAt < 9000) {
    X.fakeSadAt = -1e9; S.c.fakeTrick++;
    tr('grudge', 8); tr('trust', -3); offense();
    react({ emo: 'angry', say: line('fake_sad_trick'), anim: 'shake', fx: 'anger', disc: 'fake_sad_trick', act: '取笑' });
    return;
  }
  offense(0.5);
  if (t - X.lastCry < 8000) { tr('sorrow', 8); tr('grudge', 5); react({ emo: 'cry', say: line('tease_crying'), fx: 'tear', n: 4, disc: 'tease_crying', act: '取笑' }); return; }
  if (X.wear.doodle) { tr('grudge', 3); react({ emo: 'angry', say: line('tease_doodle'), fx: 'anger', disc: 'tease_doodle', act: '取笑' }); return; }
  if (B.wet > 50) { tr('grudge', 2); react({ emo: 'sulk', say: line('tease_wet'), disc: 'tease_wet', act: '取笑' }); discover('soaked'); return; }
  if (B.dizzy > 40) { react({ emo: 'dizzy', say: line('tease_dizzy'), anim: 'spin', disc: 'tease_dizzy', act: '取笑' }); return; }
  if (t - X.lastLostTug < 20000) { tr('sorrow', 4); react({ emo: 'sad', say: line('tease_loser'), disc: 'tease_loser', act: '取笑' }); return; }
  if (T.smug > 50) { react({ emo: 'smug', say: line('tease_smug'), disc: 'tease_smug', act: '取笑' }); return; }
  if (T.snark > 40) { react({ emo: 'speechless', say: line('tease_snark'), act: '取笑' }); return; }
  tr('grudge', 2);
  react({ emo: 'sulk', say: line('tease_basic'), disc: 'tease_basic', act: '取笑' });
}

function actCall() {
  touch(); note('call');
  const n = recent('call', 15000), T = S.T;
  if (X.sleeping) {
    if (T.trust > 50 && S.B.energy > 40) { X.sleeping = false; react({ emo: 'calm', say: line('call_wake'), disc: 'call_sleep', act: '叫牠' }); }
    else react({ emo: 'sleep', say: line('call_sleep'), disc: 'call_sleep', act: '叫牠' });
    return;
  }
  if (T.grudge > 45) { react({ emo: 'sulk', say: line('call_ignored'), disc: 'call_ignored', act: '叫牠' }); return; }
  if (n >= 4) { tr('snark', 4); react({ emo: 'speechless', say: line('call_spam'), disc: 'call_spam', act: '叫牠' }); return; }
  if (Math.abs(X.x - P.homeX) > 0.15 && !X.carried) {
    if (S.env.rain > 15 && inNest() && !X.wear.umbrella) { react({ emo: 'sad', say: line('call_rain'), act: '叫牠' }); return; }
    react({ emo: 'happy', say: line('call_come'), fx: 'note', disc: 'call_come', act: '叫牠' });
    walkTo(P.homeX);
    return;
  }
  react({ emo: T.trust > 60 ? 'happy' : 'calm', say: line('call_basic'), act: '叫牠' });
}

function actFakeSad() {
  touch(); note('fakesad');
  const T = S.T;
  if (X.sleeping) { react({ emo: 'sleep', say: line('fake_sad_sleep'), act: '假裝難過' }); return; }
  if (S.c.fakeTrick >= 2) { tr('snark', 4); react({ emo: 'speechless', say: line('fake_sad_wise'), disc: 'fake_sad_wise', act: '假裝難過' }); return; }
  X.fakeSadAt = now();
  if (T.trust > 55 && T.grudge < 40) {
    tr('trust', 1);
    walkTo(P.homeX);
    react({ emo: 'moved', say: line('fake_sad_comfort'), fx: 'heart', over: 2, overDur: 10000, disc: 'fake_sad_comfort', act: '假裝難過' });
  } else if (T.grudge >= 40) {
    react({ emo: 'speechless', say: line('fake_sad_cold'), disc: 'fake_sad_cold', act: '假裝難過' });
  } else {
    react({ emo: 'afraid', say: line('fake_sad_unsure'), disc: 'fake_sad_unsure', act: '假裝難過' });
  }
}

function actHugTeddy() {
  touch(); note('teddyhug');
  const T = S.T;
  if (S.loc.teddy !== 'tray') { toast('布偶不在托盤上，先把它拿回來'); return; }
  if (X.sleeping) { toast('小團睡著了，沒看到'); return; }
  const n = recent('teddyhug', 30000);
  X.jealousUntil = now() + 15000;
  if (T.trust > 70 && n <= 1) {
    walkTo(P.homeX);
    react({ emo: 'love', say: line('teddy_squeeze'), anim: 'squish', over: 6, overDur: 12000, disc: 'teddy_squeeze', act: '抱布偶不理牠' });
    return;
  }
  if (n >= 2) { tr('grudge', 4); react({ emo: 'angry', say: line('teddy_jealous_angry'), anim: 'shake', over: 6, overDur: 15000, disc: 'teddy_jealous_angry', act: '抱布偶不理牠' }); return; }
  tr('sorrow', 2);
  if (X.curSet === 3 || T.smug > 50) react({ emo: 'sulk', say: line('teddy_jealous_proud'), over: 6, overDur: 15000, disc: 'teddy_jealous', act: '抱布偶不理牠' });
  else react({ emo: 'sulk', say: line('teddy_jealous'), over: 6, overDur: 15000, disc: 'teddy_jealous', act: '抱布偶不理牠' });
}

function actSoothe() {
  touch(); note('soothe');
  const T = S.T;
  S.c.soothe++;
  if (X.sleeping) { react({ emo: 'sleep', say: line('soothe_sleep'), act: '安撫' }); return; }
  const repeat = S.c.soothe >= 3 && S.c.offenses > S.c.soothe * 2;
  if (T.grudge > 70) { react({ emo: 'angry', say: line('soothe_fail'), anim: 'dodge', disc: 'soothe_fail', act: '安撫' }); tr('grudge', -2); return; }
  if (repeat && T.grudge > 15) { tr('grudge', -3); tr('snark', 3); react({ emo: 'speechless', say: line('soothe_repeat'), disc: 'soothe_repeat', act: '安撫' }); return; }
  if (T.grudge > 10 || T.sorrow > 20 || T.fear > 50) {
    tr('grudge', -10); tr('sorrow', -8); tr('fear', -5); tr('trust', 1);
    react({ emo: T.grudge > 30 ? 'sulk' : 'moved', say: line(T.grudge > 30 ? 'soothe_partial' : 'soothe_ok'), fx: 'heart', disc: 'soothe_ok', act: '安撫' });
    return;
  }
  react({ emo: 'calm', say: line('soothe_none'), act: '安撫' });
}

function actMessNest() {
  touch();
  NEST_PIECES.forEach(p => {
    const o = S.nest.pieces[p.id];
    o.dx = clamp(o.dx + rand(-0.09, 0.09), -0.12, 0.25);
    o.dy = clamp(o.dy + rand(-0.08, 0.04), -0.1, 0.03);
  });
  Sound.rustle();
  renderNest();
  onNestMessed('弄亂小窩');
}

function onNestMessed(act) {
  note('mess');
  S.c.mess++;
  const T = S.T;
  const n = recent('mess', 60000);
  if (X.sleeping) {
    if (inNest()) { wakeUp('grumpy'); return; }
    X.sleepFlags.mess = true;
    logLine(act, '小團睡著了，沒有發現。', X.lastFace);
    return;
  }
  offense();
  if (inNest()) { tr('grudge', 5); react({ emo: 'angry', say: line('mess_while_inside'), anim: 'jump', fx: 'anger', disc: 'mess_while_inside', act }); return; }
  if (X.tidying) { X.tidying = false; tr('grudge', 7); tr('sorrow', 3); react({ emo: 'cry', say: line('mess_while_tidying'), fx: 'tear', disc: 'mess_while_tidying', act }); return; }
  if (S.B.energy < 30) { tr('sorrow', 6); tr('grudge', 3); react({ emo: 'cry', say: line('mess_sleepy'), fx: 'tear', disc: 'mess_sleepy', act }); return; }
  if (n >= 3) {
    tr('grudge', 8);
    react({ emo: 'angry', say: line('mess_repeat_guard'), anim: 'shake', fx: 'anger', disc: 'mess_repeat_guard', act });
    later(1500, () => { if (!X.carried) walkTo(P.nestX); });
    return;
  }
  if (T.trust > 70 && T.grudge < 15 && n <= 1) { react({ emo: 'speechless', say: line('mess_trust'), act }); tr('grudge', 2); return; }
  tr('grudge', 4);
  react({ emo: 'angry', say: line('mess_basic'), anim: 'shake', disc: 'mess_basic', act });
}

function guardingNest() {
  return !X.sleeping && inNest() && (S.c.mess >= 3 || (S.c.mess >= 2 && S.T.grudge > 25));
}

// ----- 搶東西 -----
function guardLevel(id) {
  if (X.sleeping) return 0;
  const c = ctx();
  if (id === 'blanket' && c.hot) return 0;
  if (id === 'ice' && c.cold) return 0;
  const base = { bell: 22, teddy: 16, cookie: 26, blanket: c.cold ? 22 : 5, umbrella: S.env.rain > 15 ? 16 : 3, ice: c.hot ? 12 : 0 }[id] || 0;
  return clamp(base + (S.c.snatch[id] || 0) * 22 + S.T.grudge * 0.2 + (recentFright() && id === 'teddy' ? 20 : 0), 0, 92);
}

function attachedItems() {
  const a = [];
  if (X.held) a.push(X.held);
  if (X.wear.blanket) a.push('blanket');
  if (X.wear.umbrella) a.push('umbrella');
  if (iceOn()) a.push('ice');
  return a;
}

function detach(id) {
  if (X.held === id) { X.held = null; X.eatUntil = 0; }
  if (id === 'blanket') X.wear.blanket = false;
  if (id === 'umbrella') X.wear.umbrella = false;
  if (id === 'ice') X.wear.ice = 0;
  if (ITEMS[id].unique) S.loc[id] = 'tray';
  renderAttachments();
}

function guardResist(id) {
  if (X.lastGuardSay && now() - X.lastGuardSay < 2500) return;
  X.lastGuardSay = now();
  react({ emo: S.T.fear > 60 ? 'afraid' : 'angry', say: line('guard_item'), anim: 'struggle', disc: 'guard_item', act: '想拿走' + ITEMS[id].name });
}

function onTaken(id) {
  touch(); note('snatch');
  const c = ctx(), T = S.T;
  if (X.sleeping) {
    if (['bell', 'teddy', 'blanket', 'cookie'].includes(id)) X.sleepFlags.snatched = id;
    logLine('拿走' + ITEMS[id].name, '小團睡著了，沒有發現。', X.lastFace);
    return;
  }
  if (id === 'blanket' && c.hot) { tr('trust', 1); react({ emo: 'happy', say: line('remove_blanket_hot'), disc: 'remove_blanket_hot', act: '拿走毯子' }); return; }
  if (id === 'ice' && c.cold) { react({ emo: 'calm', say: line('remove_ice_cold'), disc: 'remove_ice_cold', act: '拿走冰塊' }); return; }
  if (id === 'umbrella' && !(S.env.rain > 15) && !c.hot) { react({ emo: 'calm', say: line('remove_umbrella'), act: '收走雨傘' }); return; }
  S.c.snatch[id] = (S.c.snatch[id] || 0) + 1;
  X.snatched = id; X.snatchedAt = now();
  offense();
  const n = S.c.snatch[id];
  if (id === 'cookie') { tr('grudge', 6); tr('sorrow', 3); react({ emo: 'cry', say: line('snatch_cookie'), fx: 'tear', disc: 'snatch_cookie', act: '搶餅乾' }); return; }
  if (id === 'blanket') { tr('grudge', 4); react({ emo: 'cry', say: line('snatch_blanket_cold'), anim: 'shrink', fx: 'shiver', disc: 'snatch_blanket_cold', act: '搶毯子' }); return; }
  if (id === 'umbrella') { tr('grudge', 4); react({ emo: 'angry', say: line('snatch_umbrella_rain'), anim: 'shake', disc: 'snatch_umbrella_rain', act: '搶雨傘' }); return; }
  if (id === 'ice') { tr('grudge', 2); react({ emo: 'sulk', say: line('snatch_ice_hot'), disc: 'snatch_ice_hot', act: '搶冰塊' }); return; }
  if (id === 'teddy') {
    if (recentFright() || S.env.thunder) { tr('fear', 5); tr('sorrow', 4); react({ emo: 'cry', say: line('snatch_teddy_scared'), fx: 'tear', disc: 'snatch_teddy_scared', act: '搶布偶' }); }
    else { tr('sorrow', 3); tr('grudge', 2); react({ emo: 'sad', say: line('snatch_teddy'), disc: 'snatch_teddy', act: '搶布偶' }); }
    return;
  }
  if (id === 'bell') {
    if (n >= 3) { tr('sorrow', 8); tr('grudge', 4); react({ emo: 'cry', say: line('snatch_bell_repeat'), fx: 'tear', n: 4, disc: 'snatch_bell_repeat', act: '搶鈴鐺' }); }
    else { tr('grudge', 5); react({ emo: 'angry', say: line('snatch_bell'), anim: 'jump', fx: 'anger', disc: 'snatch_bell', act: '搶鈴鐺' }); }
  }
}

function onReturned(id) {
  if (X.snatched !== id || X.sleeping) return false;
  const dt = now() - X.snatchedAt;
  X.snatched = null;
  if (dt > 60000) return false;
  S.c.snatchReturn++;
  note('snatchreturn');
  if (recent('snatchreturn', 90000) >= 3) {
    tr('snark', 5); tr('grudge', 4);
    react({ emo: 'speechless', say: line('snatch_return_tease'), disc: 'snatch_return_tease', act: '還回' + ITEMS[id].name });
    return true;
  }
  if (dt < 5000) { tr('grudge', -3); react({ emo: 'sulk', say: line('return_quick'), disc: 'return_quick', act: '還回' + ITEMS[id].name }); return true; }
  tr('grudge', -4); tr('trust', 1);
  react({ emo: 'moved', say: line('return_late'), fx: 'heart', disc: 'return_late', act: '還回' + ITEMS[id].name });
  return true;
}

function actSnatchButton() {
  touch();
  const items = attachedItems();
  if (!items.length) {
    // 手上沒東西：去拿小窩裡的收藏
    const inNestUnique = ['bell', 'teddy', 'blanket'].filter(id => S.loc[id] === 'nest');
    if (inNestUnique.length) {
      const id = inNestUnique[0];
      S.loc[id] = 'tray';
      renderNest(); renderAttachments();
      takeFromNest(id);
      return;
    }
    const p = S.nest.pieces.star;
    p.dx = 0.2; p.dy = -0.05;
    renderNest();
    if (!X.sleeping) {
      tr('grudge', 3); offense();
      react({ emo: 'angry', say: line('snatch_star'), anim: 'jump', disc: 'snatch_from_nest', act: '拿走窩裡的星星' });
    }
    return;
  }
  const id = items[0];
  const g = guardLevel(id);
  if (g > 30 && chance(g / 110)) {
    note('snatchfail');
    react({ emo: S.T.fear > 60 ? 'afraid' : 'angry', say: line('snatch_fail_guard'), anim: 'struggle', disc: 'snatch_fail_guard', act: '硬搶' + ITEMS[id].name });
    return;
  }
  detach(id);
  onTaken(id);
}

function takeFromNest(id) {
  touch();
  if (X.sleeping) { if (id !== 'blanket') X.sleepFlags.snatched = id; return; }
  S.c.snatch[id] = (S.c.snatch[id] || 0) + 1;
  X.snatched = id; X.snatchedAt = now();
  tr('grudge', 3); offense();
  react({ emo: 'angry', say: line('snatch_from_nest', { item: ITEMS[id].sname }), anim: 'jump', disc: 'snatch_from_nest', act: '從窩裡拿走' + ITEMS[id].name });
}

// ----- 物品：放到小團身上 -----
function giveHeld(id) {
  if (X.held && X.held !== id && ITEMS[X.held].unique) S.loc[X.held] = 'tray';
  X.held = id;
  if (ITEMS[id].unique) S.loc[id] = 'tuan';
}

function useItemOnTuan(id) {
  touch(); note('item:' + id);
  if (onReturned(id)) {
    if (id === 'blanket') { X.wear.blanket = true; S.loc.blanket = 'tuan'; }
    else if (id === 'umbrella') { X.wear.umbrella = true; S.loc.umbrella = 'tuan'; }
    else if (id === 'ice') X.wear.ice = now() + 20000;
    else { giveHeld(id); if (id === 'cookie') X.eatUntil = now() + 4000; }
    renderAttachments();
    return;
  }
  const c = ctx(), T = S.T, a = S.aff;
  const sl = X.sleeping;
  const ok = { blanket: true, umbrella: true, bell: true, teddy: true };
  switch (id) {
    case 'ice':
      if (sl) { X.sleeping = false; tr('grudge', 5); offense(); a.ice -= 4; react({ emo: 'startle', say: line('ice_sleep'), anim: 'jump', fx: 'excl', disc: 'ice_sleep', act: '放冰塊' }); break; }
      if (c.hot) { X.wear.ice = now() + 25000; a.ice += 5; tr('trust', 1); react({ emo: 'sparkle', say: line('ice_hot'), fx: 'sparkle', disc: 'ice_hot', act: '放冰塊' }); break; }
      if (c.cold) { tr('grudge', 4); a.ice -= 6; offense(); react({ emo: 'cry', say: line('ice_cold'), anim: 'shake', fx: 'shiver', disc: 'ice_cold', act: '放冰塊' }); break; }
      X.wear.ice = now() + 25000;
      react({ emo: 'startle', say: line('ice_neutral'), disc: 'ice_neutral', act: '放冰塊' });
      break;
    case 'blanket':
      if (sl) {
        if (c.hot) { react({ emo: 'sleep', say: line('blanket_sleep_hot'), disc: 'blanket_sleep_hot', act: '蓋毯子' }); ok.blanket = false; break; }
        X.wear.blanket = true; tr('trust', 3); a.blanket += 3;
        react({ emo: 'sleep', say: line('blanket_tuck_sleep'), fx: 'heart', disc: 'blanket_tuck_sleep', act: '幫牠蓋毯子' });
        break;
      }
      if (c.hot) { tr('grudge', 2); a.blanket -= 4; ok.blanket = false; react({ emo: 'angry', say: line('blanket_hot'), anim: 'shake', fx: 'sweat', disc: 'blanket_hot', act: '蓋毯子' }); break; }
      X.wear.blanket = true;
      if (recentFright()) { tr('fear', -3); a.blanket += 3; react({ emo: 'moved', say: line('blanket_hide_thunder'), disc: 'blanket_hide_thunder', act: '蓋毯子' }); break; }
      if (c.cold) { tr('trust', 2); a.blanket += 5; react({ emo: 'happy', say: line('blanket_cold'), fx: 'heart', disc: 'blanket_cold', act: '蓋毯子' }); break; }
      if (c.wet) { body('wet', -25); a.blanket += 3; react({ emo: 'happy', say: line('blanket_dry'), disc: 'blanket_dry', act: '蓋毯子' }); break; }
      react({ emo: 'calm', say: line('blanket_basic'), act: '蓋毯子' });
      break;
    case 'tea':
      if (sl) { react({ emo: 'sleep', say: line('tea_sleep'), act: '端茶' }); break; }
      body('full', 5);
      if (c.hot) { tr('snark', 3); a.tea -= 2; body('warmFx', 12, -40, 40); react({ emo: 'speechless', say: line('tea_hot'), fx: 'sweat', disc: 'tea_hot', act: '喝熱茶' }); break; }
      if (c.cold) { a.tea += 4; tr('trust', 1); body('warmFx', 30, -40, 40); react({ emo: 'moved', say: line('tea_cold'), fx: 'steam', disc: 'tea_cold', act: '喝熱茶' }); break; }
      body('warmFx', 10, -40, 40);
      react({ emo: 'happy', say: line('tea_basic'), fx: 'steam', act: '喝熱茶' });
      break;
    case 'cookie':
      if (sl) {
        if (c.hungry) { X.sleeping = false; giveHeld('cookie'); X.eatUntil = now() + 5000; react({ emo: 'sparkle', say: line('cookie_wake'), fx: 'sparkle', disc: 'cookie_wake', act: '給餅乾' }); }
        else react({ emo: 'sleep', say: line('cookie_sleep'), act: '給餅乾' });
        break;
      }
      if (c.full) { tr('glutton', 1); react({ emo: 'speechless', say: line('cookie_full'), disc: 'cookie_full', act: '給餅乾' }); break; }
      giveHeld('cookie'); X.eatUntil = now() + 5000;
      if (T.grudge > 50) { tr('grudge', -5); react({ emo: 'sulk', say: line('cookie_bribe'), disc: 'cookie_bribe', act: '給餅乾' }); break; }
      if (c.hungry) { tr('glutton', 6); a.cookie += 5; tr('trust', 2); react({ emo: 'sparkle', say: line('cookie_hungry'), fx: 'sparkle', anim: 'bounce', disc: 'cookie_hungry', act: '給餅乾' }); break; }
      tr('glutton', 3); a.cookie += 2;
      react({ emo: 'happy', say: line('cookie_basic'), fx: 'crumb', act: '給餅乾' });
      break;
    case 'water': {
      const wasWet = S.B.wet;
      body('wet', 35);
      Sound.splash();
      if (X.wear.doodle) { X.wear.doodle = false; X.sleepFlags.doodle = false; react({ emo: 'happy', say: line('water_wash'), fx: 'sparkle', disc: 'water_wash_doodle', act: '潑水' }); break; }
      if (sl) { X.sleeping = false; tr('grudge', 5); offense(); react({ emo: 'startle', say: line('water_sleep'), anim: 'jump', fx: 'tear', disc: 'water_sleep', act: '潑水' }); break; }
      if (c.hot) { a.water += 4; tr('trust', 1); react({ emo: 'happy', say: line('water_hot'), fx: 'sparkle', anim: 'bounce', disc: 'water_hot', act: '潑水' }); break; }
      if (c.cold) { tr('grudge', 5); tr('fear', 2); a.water -= 5; offense(); react({ emo: 'cry', say: line('water_cold'), anim: 'shake', fx: 'shiver', disc: 'water_cold', act: '潑水' }); break; }
      if (wasWet > 60) { tr('grudge', 3); offense(); react({ emo: 'angry', say: line('water_soaked'), fx: 'anger', disc: 'water_soaked', act: '潑水' }); break; }
      tr('grudge', 2); offense(0.5);
      react({ emo: 'startle', say: line('water_basic'), anim: 'jump', disc: 'water_basic', act: '潑水' });
      break;
    }
    case 'fan':
      X.fanUntil = now() + 9000;
      if (sl && c.hot) { tr('trust', 2); react({ emo: 'sleep', say: line('fan_sleep_hot'), disc: 'fan_sleep_hot', act: '搧風' }); break; }
      if (sl) { react({ emo: 'sleep', say: line('fan_sleep'), act: '搧風' }); break; }
      if (S.env.wind > 60) { tr('snark', 3); react({ emo: 'speechless', say: line('fan_windy'), disc: 'fan_windy', act: '搧風' }); break; }
      if (c.hot) { a.fan += 4; react({ emo: 'happy', say: line('fan_hot'), fx: 'note', disc: 'fan_hot', act: '搧風' }); break; }
      if (c.cold) { tr('grudge', 3); a.fan -= 4; offense(0.5); react({ emo: 'angry', say: line('fan_cold'), anim: 'shake', disc: 'fan_cold', act: '搧風' }); break; }
      react({ emo: 'calm', say: line('fan_basic'), act: '搧風' });
      break;
    case 'umbrella':
      X.wear.umbrella = true;
      if (sl) { react({ emo: 'sleep', say: line('umbrella_sleep'), act: '撐傘' }); break; }
      if (S.env.rain > 15 && !inNest()) {
        a.umbrella += 4; tr('trust', 1);
        react({ emo: 'happy', say: line('umbrella_rain'), fx: 'note', disc: 'umbrella_rain', act: '撐傘' });
        if (S.env.wind > 70) X.umbrellaFlipAt = now() + 1800;
        break;
      }
      if (inNest()) { tr('snark', 2); react({ emo: 'speechless', say: line('umbrella_nest'), act: '撐傘' }); break; }
      if (c.hot) { a.umbrella += 2; react({ emo: 'happy', say: line('umbrella_sun'), disc: 'umbrella_sun', act: '撐傘' }); break; }
      tr('snark', 3);
      react({ emo: 'speechless', say: line('umbrella_no_rain'), disc: 'umbrella_no_rain', act: '撐傘' });
      break;
    case 'bell':
      giveHeld('bell');
      Sound.bell();
      if (sl) { react({ emo: 'sleep', say: line('bell_sleep'), act: '給鈴鐺' }); break; }
      a.bell += 2; tr('trust', 1);
      react({ emo: 'sparkle', say: line('bell_give'), fx: 'note', anim: 'bounce', disc: 'bell_give', act: '給鈴鐺' });
      break;
    case 'teddy':
      giveHeld('teddy');
      if (sl) { tr('trust', 1); react({ emo: 'sleep', say: line('teddy_sleep'), fx: 'heart', act: '給布偶' }); break; }
      if (now() < X.jealousUntil) { X.jealousUntil = 0; react({ emo: 'sulk', say: line('teddy_jealous_take'), disc: 'teddy_jealous_take', act: '給布偶' }); break; }
      if (recentFright() || S.env.thunder) { tr('fear', -5); a.teddy += 3; react({ emo: 'moved', say: line('teddy_comfort'), fx: 'heart', disc: 'teddy_comfort', act: '給布偶' }); break; }
      react({ emo: 'happy', say: line('teddy_give'), fx: 'heart', act: '給布偶' });
      break;
    case 'crayon':
      X.wear.doodle = true; S.c.doodle++;
      X.doodleAt = now();
      if (sl) {
        if (T.trust > 40) { X.sleepFlags.doodle = true; logLine('在臉上畫畫', '小團睡得很熟，沒有醒。', X.lastFace); break; }
        wakeUp('grumpy'); break;
      }
      if (T.trust > 65 && T.grudge < 20 && S.c.doodle <= 2) { react({ emo: 'shy', say: line('doodle_trust'), fx: 'note', disc: 'doodle_trust', act: '在臉上畫畫' }); break; }
      tr('grudge', 4); offense(); a.crayon -= 3;
      react({ emo: 'angry', say: line('doodle_angry'), anim: 'shake', fx: 'anger', disc: 'doodle_angry', act: '在臉上畫畫' });
      break;
  }
  if (ITEMS[id].unique) {
    if ((id === 'blanket' || id === 'umbrella') && !ok[id]) { S.loc[id] = 'tray'; X.wear[id] = false; }
    else if (id === 'blanket' || id === 'umbrella') S.loc[id] = 'tuan';
  }
  renderAttachments();
}

// ----- 物品：放進小窩 -----
function useItemOnNest(id) {
  touch(); note('nest:' + id);
  const watching = !X.sleeping;
  const c = ctx(), N = S.nest;
  const r = (o) => { if (watching) react(o); else logLine(o.act, '小團睡著了，沒有看到。', X.lastFace); };
  switch (id) {
    case 'ice': N.wet = clamp(N.wet + 40, 0, 100); S.aff.ice -= 2; if (watching) { tr('grudge', 4); offense(); } r({ emo: 'angry', say: line('ice_nest'), anim: 'shake', disc: 'ice_nest', act: '冰塊放進小窩' }); break;
    case 'water': N.wet = clamp(N.wet + 55, 0, 100); Sound.splash(); if (watching) { tr('grudge', 4); tr('sorrow', 3); offense(); } r({ emo: 'cry', say: line('water_nest'), fx: 'tear', disc: 'water_nest', act: '往小窩倒水' }); break;
    case 'tea': N.wet = clamp(N.wet + 30, 0, 100); if (watching) { tr('grudge', 3); offense(); } r({ emo: 'angry', say: line('tea_nest'), disc: 'tea_nest', act: '茶倒進小窩' }); break;
    case 'cookie':
      N.crumbs = true;
      if (c.hungry) { r({ emo: 'happy', say: line('cookie_nest_hungry'), disc: 'cookie_nest_hungry', act: '餅乾放進小窩' }); if (watching) later(1200, () => walkTo(P.nestX, () => { N.crumbs = false; body('full', 20); react({ emo: 'happy', say: line('cookie_nest_eat')}); renderNest(); })); }
      else { if (watching) tr('grudge', 2); r({ emo: 'angry', say: line('cookie_nest'), disc: 'cookie_nest', act: '餅乾放進小窩' }); }
      break;
    case 'blanket': S.loc.blanket = 'nest'; r({ emo: 'happy', say: line('blanket_nest'), fx: 'heart', disc: 'blanket_nest', act: '毯子鋪進小窩' }); S.aff.blanket += 2; break;
    case 'teddy': S.loc.teddy = 'nest'; r({ emo: 'happy', say: line('teddy_nest'), disc: 'teddy_nest', act: '布偶放進小窩' }); break;
    case 'bell': S.loc.bell = 'nest'; Sound.bell(); r({ emo: 'calm', say: line('bell_nest'), disc: 'bell_nest', act: '鈴鐺放進小窩' }); break;
    case 'crayon':
      S.nest.pieces.pillow.dx += 0.02;
      if (watching) { tr('grudge', 3); offense(); }
      r({ emo: 'angry', say: line('crayon_nest'), disc: 'crayon_nest', act: '在小窩裡畫畫' });
      break;
    case 'fan':
      if (N.wet > 20) { N.wet = clamp(N.wet - 35, 0, 100); r({ emo: 'happy', say: line('fan_nest_dry'), disc: 'fan_nest_dry', act: '對小窩搧風' }); }
      else { if (watching) tr('snark', 2); r({ emo: 'speechless', say: line('fan_nest'), disc: 'fan_nest', act: '對小窩搧風' }); }
      break;
    case 'umbrella': if (watching) tr('snark', 3); r({ emo: 'speechless', say: line('umbrella_nest_roof'), disc: 'umbrella_nest', act: '在小窩撐傘' }); break;
  }
  renderNest(); renderAttachments();
}

// ----- 打雷 -----
function thunderStrike() {
  X.lastThunder = now();
  note('thunder');
  Sound.thunder();
  UI.flash && UI.flash();
  if (MG && MG.onThunder && MG.onThunder()) return;
  const T = S.T;
  const mit = (X.hugging ? 45 : 0) + (inNest() ? 18 : 0) + (X.wear.blanket ? 20 : 0) + (X.held === 'teddy' ? 20 : 0);
  const eff = T.fear + recent('thunder', 60000) * 4 - mit + rand(-10, 10);
  if (X.sleeping) {
    if (eff > 45) { X.sleeping = false; tr('fear', 3); react({ emo: 'cry', say: line('thunder_wake'), anim: 'jump', fx: 'tear', over: 18, overDur: 8000, act: '打雷' }); }
    else react({ emo: 'sleep', say: line('thunder_sleep_through'), disc: 'thunder_sleep_through', act: '打雷' });
    return;
  }
  if (X.hugging) {
    tr('fear', -3); tr('trust', 3); S.c.thunderHug++;
    if (eff > 40) react({ emo: 'afraid', say: line('thunder_hug'), anim: 'shrink', disc: 'thunder_hug', act: '抱著時打雷' });
    else react({ emo: 'moved', say: line('thunder_hug_brave'), fx: 'heart', disc: 'thunder_hug_brave', act: '抱著時打雷' });
    return;
  }
  if (mit === 0) { S.c.thunderAlone++; tr('fear', 1); }
  if (eff > 70) {
    tr('fear', 4); tr('sorrow', 2);
    react({ emo: 'cry', say: line('thunder_cry'), anim: 'jump', fx: 'tear', n: 4, over: 18, overDur: 9000, disc: 'thunder_cry', act: '打雷' });
    if (T.trust > 70) later(2200, () => { walkTo(P.homeX); react({ emo: 'cry', say: line('thunder_seek'), disc: 'thunder_seek' }); });
    else later(1500, () => { if (!inNest()) walkTo(P.nestX); });
  } else if (eff > 40) {
    tr('fear', 2);
    react({ emo: 'afraid', say: line('thunder_afraid'), anim: 'shrink', fx: 'shiver', disc: 'thunder_afraid', act: '打雷' });
  } else if (eff > 15) {
    tr('fear', 1);
    react({ emo: 'startle', say: line('thunder_startle'), anim: 'jump', fx: 'excl', disc: 'thunder_startle', act: '打雷' });
  } else if (T.fear < 10) {
    react({ emo: 'sparkle', say: line('thunder_pretty'), fx: 'sparkle', disc: 'thunder_pretty', act: '打雷' });
  } else {
    tr('smug', 2);
    react({ emo: 'smug', say: line('thunder_brave'), disc: 'thunder_brave', act: '打雷' });
  }
}

// 拿著物品靠近時，小團會先預期
function anticipate(id) {
  if (X.sleeping || now() - X.lastReact < 1500 || X.carried) return;
  const B = S.B;
  let a = (S.aff[id] || 0) * 2;
  if (id === 'blanket' || id === 'tea') a += B.feel < -25 ? 20 : B.feel > 25 ? -15 : 0;
  if (id === 'ice' || id === 'fan' || id === 'water') a += B.feel > 25 ? 20 : B.feel < -25 ? -20 : 0;
  if (id === 'water' && B.wet > 50) a -= 15;
  if (id === 'cookie') a += B.full < 35 ? 20 : B.full > 85 ? -10 : 5;
  if (id === 'umbrella') a += S.env.rain > 15 && !inNest() ? 20 : 0;
  if (id === 'teddy') a += recentFright() ? 20 : 0;
  if (id === 'crayon') a -= S.c.doodle * 6;
  if (id === X.snatched) a += 20;
  if (a >= 12) react({ emo: 'sparkle', say: line('item_hope', { item: ITEMS[id].sname }), dur: 1600, fx: 'sparkle', n: 2, disc: 'item_hope' });
  else if (a <= -12) {
    if (id === 'ice' && S.aff.ice <= -6) discover('ice_wary');
    react({ emo: S.T.grudge > 30 ? 'angry' : 'afraid', say: line(S.T.grudge > 30 ? 'item_wary_angry' : 'item_wary', { item: ITEMS[id].sname }), dur: 1600, anim: 'shrink' });
  } else burst('ques', 1);
}

// ===== 身體與環境的每一刻 =====
function bodyTick() {
  const B = S.B, env = S.env, t = now();
  let target = (env.temp - 50) * 1.4;
  const nest = inNest();
  target -= env.wind * (nest ? 0.06 : 0.25);
  target -= B.wet * 0.25;
  if (X.wear.blanket) target += 30;
  else if (nest && S.loc.blanket === 'nest' && X.sleeping) target += 22;
  if (X.hugging) target += 18;
  if (nest) target += 6;
  if (iceOn()) target -= 28;
  if (t < X.fanUntil) target -= 22;
  if (X.wear.umbrella && env.temp > 65 && env.rain < 10) target -= 8;
  target += B.warmFx;
  B.warmFx *= 0.985;
  B.feel = clamp(B.feel + (target - B.feel) * 0.04, -100, 100);

  const exposed = env.rain > 5 && !sheltered() && !X.carried;
  if (exposed) B.wet = clamp(B.wet + env.rain * (snowing() ? 0.006 : 0.012), 0, 100);
  if (iceOn()) B.wet = clamp(B.wet + 0.12, 0, 100);
  B.wet = clamp(B.wet - (0.06 + Math.max(0, B.feel) * 0.004 + (X.wear.blanket ? 0.15 : 0) + (t < X.fanUntil ? 0.2 : 0)), 0, 100);

  if (X.sleeping) B.energy = clamp(B.energy + (nest ? 0.32 : 0.2), 0, 100);
  else B.energy = clamp(B.energy - (X.walking ? 0.02 : 0.012), 0, 100);
  B.full = clamp(B.full - (X.sleeping ? 0.005 : 0.01), 0, 100);
  B.dizzy = clamp(B.dizzy - 0.5, 0, 100);
  if (X.held === 'cookie' && X.eatUntil && t > X.eatUntil) {
    X.held = null; X.eatUntil = 0; body('full', 25); renderAttachments();
  }
  if (X.wear.ice && t > X.wear.ice) { X.wear.ice = 0; renderAttachments(); }
  if (X.wear.doodle && X.doodleAt && t - X.doodleAt > 70000 && !X.sleeping) {
    X.wear.doodle = false; renderAttachments();
    react({ emo: 'calm', say: line('doodle_wipe'), act: '自己擦臉' });
  }
  if (X.umbrellaFlipAt && t > X.umbrellaFlipAt) {
    X.umbrellaFlipAt = 0;
    if (X.wear.umbrella && S.env.wind > 60) {
      detach('umbrella');
      react({ emo: 'startle', say: line('umbrella_wind'), anim: 'jump', fx: 'excl', disc: 'umbrella_wind', act: '大風' });
    }
  }
  // 小窩慢慢變乾
  S.nest.wet = clamp(S.nest.wet - 0.05, 0, 100);
  // 特質慢慢回到平常
  const T = S.T;
  T.grudge = clamp(T.grudge - 0.03, 0, 100);
  T.sorrow = clamp(T.sorrow - 0.02, 0, 100);
  T.smug = clamp(T.smug - (T.smug > 10 ? 0.01 : 0), 0, 100);
  T.snark = clamp(T.snark - 0.02, 0, 100);
  T.glutton = clamp(T.glutton - (T.glutton > 10 ? 0.008 : 0), 0, 100);
  if (T.fear > 22) T.fear -= 0.006;
  if (X.hugging) hugTick();
  if (X.carried && X.y < 0.32) carryHigh();
}

// 天氣變化的瞬間
const envPrev = { rain: 0, wind: 0, snow: false };
function envTick() {
  const env = S.env, t = now();
  const sn = snowing();
  if (env.rain > 20 && envPrev.rain <= 20) onRainStart(sn);
  else if (sn && !envPrev.snow && env.rain > 20) onRainStart(true);
  if (env.wind > 60 && envPrev.wind <= 60 && !X.sleeping) {
    react({ emo: 'afraid', say: line('wind_strong'), anim: 'shrink', disc: 'wind_strong', act: '颳大風' });
  }
  envPrev.rain = env.rain; envPrev.wind = env.wind; envPrev.snow = sn;
  // 大風會吹亂小窩，這不是你的錯，所以不記仇
  if (env.wind > 75 && chance(0.04)) {
    const p = pick(NEST_PIECES);
    const o = S.nest.pieces[p.id];
    o.dx = clamp(o.dx + rand(0.01, 0.05), -0.12, 0.3);
    o.dy = clamp(o.dy + rand(-0.02, 0.01), -0.08, 0.03);
    renderNest();
    if (!X.sleeping && t - X.lastReact > 4000 && nestTidy() < 70 && !X.windMessSaid) {
      X.windMessSaid = true;
      react({ emo: 'sad', say: line('wind_mess_nest'), disc: 'wind_mess_nest', act: '大風' });
    }
  }
  if (env.wind < 40) X.windMessSaid = false;
  if (env.thunder && t > (UI.nextThunder || 0)) {
    UI.nextThunder = t + rand(8000, 17000);
    thunderStrike();
  }
}

function onRainStart(isSnow) {
  if (X.sleeping) return;
  const c = ctx(), T = S.T;
  if (isSnow) {
    react({ emo: 'sparkle', say: line('snow_first'), fx: 'sparkle', disc: 'snow_first', act: '下雪' });
    return;
  }
  if (inNest()) { react({ emo: 'calm', say: line('rain_in_nest'), act: '下雨' }); return; }
  if (X.wear.umbrella) { react({ emo: 'happy', say: line('rain_umbrella'), act: '下雨' }); return; }
  if (c.hot) { react({ emo: 'happy', say: line('rain_hot'), fx: 'note', disc: 'rain_hot', act: '下雨' }); return; }
  if (!c.cold && S.B.energy > 55 && (T.trust > 70 || now() < X.playfulUntil) && T.grudge < 20) {
    X.rainPlay = true;
    react({ emo: 'happy', say: line('rain_play'), anim: 'bounce', fx: 'note', disc: 'rain_play', act: '下雨' });
    later(12000, () => { X.rainPlay = false; });
    return;
  }
  react({ emo: 'startle', say: line(c.cold ? 'rain_cold' : 'rain_run'), disc: 'rain_run', act: '下雨' });
  later(900, () => { if (!X.carried && !X.hugging && !inNest()) walkTo(P.nestX); });
}

// ===== 小團自己的行動 =====
function aiTick() {
  const t = now();
  if (t < X.nextAI) return;
  X.nextAI = t + rand(2600, 4200);
  if (X.carried || X.hugging || X.airborne || (MG && MG.active)) return;
  if (t - X.lastReact < 3500 || X.target) return;
  const B = S.B, T = S.T, env = S.env, c = ctx();
  if (X.sleeping) {
    if (B.energy >= 96) {
      X.sleeping = false;
      react({ emo: 'happy', say: line('wake_full'), fx: 'note', act: '醒來' });
      later(2500, checkAfterWake);
      return;
    }
    if (c.freezing && !X.wear.blanket) { wakeUp(); react({ emo: 'cry', say: line('cold_cant_sleep'), fx: 'shiver', disc: 'cold_cant_sleep', act: '醒來' }); return; }
    if (c.scorching && !iceOn()) { wakeUp(); react({ emo: 'dizzy', say: line('hot_cant_sleep'), fx: 'sweat', disc: 'hot_cant_sleep', act: '醒來' }); return; }
    if (env.rain > 20 && !sheltered() && B.wet > 40) { wakeUp(); react({ emo: 'sad', say: line('rain_woke'), fx: 'tear', act: '醒來' }); return; }
    if (chance(0.3)) burst('zzz', 2);
    return;
  }
  if (X.tidying) return;
  // 下雨找地方躲
  if (env.rain > 15 && !sheltered() && !X.rainPlay && B.wet > 25) {
    react({ emo: 'sad', say: line('rain_seek_shelter'), act: '躲雨' });
    walkTo(P.nestX);
    return;
  }
  if (B.wet > 75 && chance(0.4)) { discover('soaked'); react({ emo: 'sad', say: line('soaked'), fx: 'tear' }); return; }
  // 想睡
  if (B.energy < 22) {
    if (!inNest()) { react({ emo: 'speechless', say: line('sleepy_go_nest')}); walkTo(P.nestX); return; }
    if (S.nest.wet > 40) { tr('sorrow', 2); react({ emo: 'cry', say: line('nest_wet_cant_sleep'), fx: 'tear', disc: 'nest_wet_cant_sleep', act: '想睡' }); return; }
    if (nestTidy() < 50) {
      if (B.energy > 10) { startTidy(true); return; }
      tr('sorrow', 3);
      react({ emo: 'sad', say: line('nest_messy_cant_sleep'), disc: 'nest_messy_cant_sleep', act: '想睡' });
      return;
    }
    if (c.freezing && !X.wear.blanket) { react({ emo: 'cry', say: line('cold_cant_sleep'), disc: 'cold_cant_sleep' }); return; }
    fallAsleep();
    return;
  }
  // 整理小窩
  if ((nestTidy() < 75 || S.nest.crumbs) && T.grudge < 70 && B.energy > 25 && !recentFright() && chance(0.6)) { startTidy(false); return; }
  // 身體不舒服
  if (c.cold) {
    if (S.aff.blanket >= 4 && S.loc.blanket === 'tray') { discover('wish_item'); react({ emo: 'sad', say: line('wish_blanket'), fx: 'shiver', anim: 'shrink' }); return; }
    if (c.freezing && T.trust > 50 && T.grudge < 30) { react({ emo: 'cry', say: line('cold_want_hug'), fx: 'shiver' }); walkTo(P.homeX); return; }
    if (chance(0.6)) { react({ emo: 'sad', say: line('cold_idle'), fx: 'shiver' }); return; }
  }
  if (c.hot) {
    if (S.aff.ice >= 4) { discover('wish_item'); react({ emo: 'speechless', say: line('wish_ice'), fx: 'sweat' }); return; }
    if (S.aff.fan >= 4) { discover('wish_item'); react({ emo: 'speechless', say: line('wish_fan'), fx: 'sweat' }); return; }
    if (chance(0.6)) { react({ emo: c.scorching ? 'dizzy' : 'speechless', say: line(c.scorching ? 'scorching_idle' : 'hot_idle'), fx: 'sweat' }); return; }
  }
  if (c.hungry && chance(0.5)) {
    discover('hungry_ask');
    if (S.aff.cookie >= 4) discover('wish_item');
    react({ emo: 'sad', say: line(S.aff.cookie >= 4 ? 'hungry_cookie' : 'hungry'), act: '肚子餓' });
    return;
  }
  // 照顧芽
  if (sproutAI()) return;
  // 被搶走的東西
  if (X.snatched && t - X.snatchedAt > 25000 && t - X.snatchedAt < 90000 && S.loc[X.snatched] !== 'tuan' && chance(0.5)) {
    react({ emo: 'sulk', say: line('snatched_remind', { item: ITEMS[X.snatched].sname })});
    return;
  }
  // 寂寞
  if (t - X.lastInteract > 35000) {
    X.lastInteract = t - 15000;
    if (T.grudge > 50) { react({ emo: 'sulk', say: line('grudge_idle')}); return; }
    if (T.trust > 45) {
      walkTo(P.homeX);
      react({ emo: 'happy', say: line('lonely'), fx: 'note', disc: 'lonely', act: '找你玩' });
      return;
    }
  }
  // 隨意小動作
  const r = Math.random();
  if (r < 0.25 && X.held === 'bell') { Sound.bell(); react({ emo: 'happy', say: line('bell_idle'), fx: 'note' }); return; }
  if (r < 0.4) { walkTo(clamp(X.x + rand(-0.15, 0.15), P.nestR + 0.04, P.potX - 0.08)); return; }
  if (r < 0.5 && !c.cold && !c.hot && T.grudge < 20) { react({ emo: 'calm', say: line(env.rain > 15 ? 'idle_rainy' : 'idle_hum'), fx: 'note', n: 1 }); return; }
  if (r < 0.58 && now() < X.playfulUntil) { react({ emo: 'happy', say: line('playful_idle'), anim: 'bounce' }); }
}

function startTidy(thenSleep) {
  X.tidying = true;
  const messedByYou = recent('mess', 120000) > 0;
  react({ emo: messedByYou ? 'sulk' : 'calm', say: line(messedByYou ? 'tidy_annoyed' : 'tidy_start')});
  walkTo(P.nestX, () => tidyStep(thenSleep));
}

function tidyStep(thenSleep) {
  if (!X.tidying || X.carried || X.sleeping) { X.tidying = false; return; }
  let worst = null, wd = 6;
  NEST_PIECES.forEach(p => {
    const o = S.nest.pieces[p.id];
    const d = Math.hypot(o.dx * L.W, o.dy * L.H);
    if (d > wd) { wd = d; worst = p; }
  });
  if (worst) {
    const o = S.nest.pieces[worst.id];
    o.dx = 0; o.dy = 0;
    Sound.rustle();
    renderNest();
    later(900, () => tidyStep(thenSleep));
    return;
  }
  if (S.nest.crumbs) { S.nest.crumbs = false; renderNest(); later(900, () => tidyStep(thenSleep)); return; }
  X.tidying = false;
  X.lastGood = now();
  react({ emo: 'smug', say: line('tidy_done'), fx: 'sparkle', act: '自己整理小窩' });
  if (thenSleep) later(2500, () => { if (!X.carried && inNest() && S.B.energy < 30) fallAsleep(); });
}
