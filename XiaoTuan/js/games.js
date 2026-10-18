'use strict';
// ===== 小遊戲：拉鋸、藏鈴、茶會、畫畫，以及一直在長的芽 =====
let MG = null;

const GAME_INFO = {
  tug: { name: '拉鋸', icon: '🪢', desc: '一人拉一頭。可以認真拉、偷偷放水，或突然放手。' },
  bell: { name: '藏鈴', icon: '🔔', desc: '把鈴鐺藏起來讓牠找，也可以作弊，或換牠藏。' },
  tea: { name: '茶會', icon: '🫖', desc: '倒茶、加糖、放點心、乾杯。也能偷喝或打翻。' },
  sprout: { name: '種芽', icon: '🌱', desc: '一起種一株芽。天氣會影響它，小團也會照顧它。' },
  draw: { name: '畫畫', icon: '🖍️', desc: '你畫你的，牠畫牠的。牠的畫會透露心情。' }
};

const Games = {
  view: null,

  refuse(type) {
    const T = S.T, c = S.c;
    if (X.sleeping) {
      wakeUp('grumpy');
      return true;
    }
    if (T.grudge > 60 && chance((T.grudge - 45) / 55)) {
      react({ emo: 'sulk', say: line('refuse_play'), disc: 'refuse_play', act: '找牠玩' + GAME_INFO[type].name });
      return true;
    }
    if (type === 'tug' && c.tugLetGo >= 2 && T.trust < 70 && chance(0.7)) {
      react({ emo: 'sulk', say: line('tug_refuse'), disc: 'tug_refuse', act: '找牠拉鋸' }); return true;
    }
    if (type === 'bell' && c.cheatBell >= 2 && chance(0.7)) {
      react({ emo: 'speechless', say: line('bell_refuse'), disc: 'bell_refuse', act: '找牠藏鈴' }); return true;
    }
    if (type === 'bell' && (c.snatch.bell || 0) >= 3 && T.grudge > 15) {
      react({ emo: 'sulk', say: line('bell_refuse_snatch'), disc: 'bell_refuse_snatch', act: '找牠藏鈴' }); return true;
    }
    if (type === 'tea' && c.spills >= 2 && chance(0.6)) {
      react({ emo: 'sulk', say: line('tea_refuse'), disc: 'tea_refuse', act: '找牠喝茶' }); return true;
    }
    if (type === 'draw' && c.tornDrawings >= 2 && chance(0.7)) {
      react({ emo: 'sad', say: line('draw_refuse'), disc: 'draw_refuse', act: '找牠畫畫' }); return true;
    }
    return false;
  },

  open(type) {
    Sound.init();
    touch();
    if (type === 'sprout') { this.end(true); this.view = 'sprout'; this.renderPanel(); return; }
    if (MG && MG.type === type && !MG.done) { this.view = type; this.renderPanel(); return; }
    if (X.carried || X.hugging) { toast('先放開小團'); return; }
    if (this.refuse(type)) { this.renderPanel(); return; }
    this.end(true);
    if (type === 'bell' && !this.takeBell()) return;
    stopWalk(); X.tidying = false; X.airborne = false;
    this.view = type;
    S.played++;
    ({ tug: startTug, bell: startBell, tea: startTea, draw: startDraw })[type]();
    this.renderPanel();
  },

  takeBell() {
    if (S.loc.bell === 'pot') { toast('鈴鐺掛在芽上，先把它拿下來'); return false; }
    if (X.held === 'bell') {
      if (guardLevel('bell') > 70) {
        react({ emo: 'sulk', say: line('bell_refuse_snatch'), disc: 'bell_refuse_snatch', act: '找牠藏鈴' });
        return false;
      }
      X.held = null;
    }
    S.loc.bell = 'game';
    renderAttachments(); renderNest();
    return true;
  },

  end(silent) {
    if (!MG) return;
    const g = MG;
    MG = null;
    if (g.cleanup) g.cleanup();
    $('#mg').innerHTML = '';
    $('#mg').className = '';
    if (g.type === 'bell' && S.loc.bell === 'game') {
      S.loc.bell = 'tuan'; X.held = 'bell';
      renderAttachments();
    }
    if (!silent && g.type !== 'bell') walkTo(P.homeX);
    this.view = null;
    this.renderPanel();
  },

  tick(dt) {
    if (MG && MG.tick) MG.tick(dt);
  },

  renderPanel() {
    const box = $('#gamePanel');
    if (!box) return;
    const v = this.view;
    if (!v) {
      box.innerHTML = '<div class="game-grid">' + Object.keys(GAME_INFO).map(k => {
        const g = GAME_INFO[k];
        return '<button class="game-card" data-g="open:' + k + '"><span class="gi">' + g.icon + '</span><b>' + g.name + '</b><small>' + g.desc + '</small></button>';
      }).join('') + '</div>';
      return;
    }
    if (v === 'sprout') { box.innerHTML = sproutPanel(); return; }
    if (MG && MG.panel) box.innerHTML = '<div class="game-head"><b>' + GAME_INFO[v].icon + ' ' + GAME_INFO[v].name + '</b><button class="ghost" data-g="end">結束</button></div>' + MG.panel();
  },

  click(cmd) {
    touch();
    const [a, b] = cmd.split(':');
    if (a === 'open') return this.open(b);
    if (a === 'end') { if (this.view === 'sprout') { this.view = null; this.renderPanel(); return; } if (MG && MG.onEnd) MG.onEnd(); this.end(); return; }
    if (a === 'back') { this.view = null; this.renderPanel(); return; }
    if (a === 'sp') return sproutCmd(b);
    if (MG && MG.cmd) MG.cmd(a, b);
    this.renderPanel();
  }
};

function mgSpot(fx) { return L.narrow ? 0.5 + (fx - 0.5) * 1.15 : fx; }
function bellX(i) { return (L.narrow ? [0.2, 0.5, 0.8] : [0.38, 0.55, 0.72])[i]; }

// ===================== 拉鋸 =====================
function tugStrength() {
  const B = S.B, T = S.T;
  let s = 1.0 * (B.energy / 100 * 0.6 + 0.4);
  if (B.feel > 30) s *= 0.6;
  else if (B.feel < -30) s *= 0.8;
  if (T.grudge > 30) s *= 1.3;
  if (T.sorrow > 40) s *= 0.7;
  if (T.smug > 50) s *= 1.1;
  if (B.wet > 50) s *= 0.85;
  if (B.dizzy > 50) s *= 0.6;
  return clamp(s, 0.35, 1.7);
}

function startTug() {
  MG = {
    type: 'tug', active: true, lockTuan: true, pos: 0, impulse: 0, eased: false, easedUsed: false,
    yanks: 0, t0: now(), done: false, force: 1, acc: 0, said: {},
    tick: tugTick, cmd: tugCmd, panel: tugPanel, onThunder: tugThunder, onEnd: () => tugFinish('quit')
  };
  X.x = mgSpot(0.72);
  $('#mg').className = 'mg-tug';
  $('#mg').innerHTML = '<div class="tug-hand">✊</div><div class="tug-rope"></div><div class="tug-knot"></div><div class="tug-mid"></div><div class="tug-tap" data-tug="pull">點這裡也能拉</div>';
  $('#mg .tug-tap').addEventListener('pointerdown', e => { e.preventDefault(); tugCmd('pull'); });
  react({ emo: 'smug', say: line(S.T.grudge > 30 ? 'tug_start_grudge' : 'tug_start'), anim: 'bounce', act: '開始拉鋸' });
  tugRender();
}

function tugPanel() {
  const m = MG;
  if (m.done) return '<p class="hint">' + m.result + '</p><div class="btns"><button data-g="open:tug">再來一局</button><button class="ghost" data-g="end">結束</button></div>';
  return '<div class="tug-meter"><span>你</span><div class="bar"><i style="left:' + (50 + m.pos / 2) + '%"></i></div><span>小團</span></div>' +
    '<div class="btns"><button class="big" data-g="pull">拉！</button><button data-g="yank">用力猛拉</button>' +
    '<button data-g="ease" class="' + (m.eased ? 'on' : '') + '">' + (m.eased ? '放水中…' : '偷偷放水') + '</button><button data-g="letgo">突然放手</button></div>' +
    '<p class="hint">連點「拉！」或空白鍵。小團的力氣跟牠的精神、冷熱和心情有關。</p>';
}

function tugCmd(a) {
  const m = MG;
  if (!m || m.type !== 'tug' || m.done) return;
  touch();
  if (a === 'pull') { m.impulse += m.eased ? 1.1 : 3.0; Sound.pop(); }
  if (a === 'ease') { m.eased = !m.eased; m.easedUsed = m.easedUsed || m.eased; Games.renderPanel(); }
  if (a === 'yank') {
    m.yanks++;
    m.pos -= 28;
    Sound.boing();
    if (m.force > 0.9) {
      body('dizzy', 12);
      react({ emo: 'startle', say: line('tug_yank_fall'), anim: 'tumble', fx: 'excl' });
    }
    if (m.yanks >= 2) { tr('grudge', 3); offense(0.5); react({ emo: 'angry', say: line('tug_yank'), anim: 'shake', disc: 'tug_yank', act: '拉鋸猛拉' }); }
  }
  if (a === 'letgo') tugFinish('letgo');
  tugRender();
}

function tugTick(dt) {
  const m = MG;
  if (m.done) return;
  m.acc += dt;
  while (m.acc >= 100) {
    m.acc -= 100;
    m.force = tugStrength() * (0.8 + Math.random() * 0.4);
    m.pos += m.force * 1.0 - m.impulse;
    m.impulse *= 0.6;
    body('energy', -0.04);
    S.B.warmFx = clamp(S.B.warmFx + 0.25, -40, 40);
    m.pos = clamp(m.pos, -100, 100);
    if (m.pos > 60 && !m.said.win) { m.said.win = true; react({ emo: 'smug', say: line('tug_almost_win'), dur: 1500 }); }
    if (m.pos < -60 && !m.said.lose) { m.said.lose = true; react({ emo: 'afraid', say: line('tug_almost_lose'), dur: 1500 }); }
    if (m.pos >= 100) { tugFinish('tuan'); return; }
    if (m.pos <= -100) { tugFinish('you'); return; }
  }
  if (now() > X.emoUntil) { X.emo = m.pos > 40 ? 'smug' : m.pos < -40 ? 'afraid' : 'angry'; X.emoUntil = now() + 400; updateFace(); }
  tugRender();
  const bar = document.querySelector('.tug-meter i');
  if (bar) bar.style.left = (50 + m.pos / 2) + '%';
}

function tugRender() {
  const m = MG;
  if (!m || m.type !== 'tug') return;
  if (!m.done) X.x = mgSpot(0.72) + m.pos / 100 * 0.04;
  const handX = mgSpot(0.2) * L.W + m.pos / 100 * 0.03 * L.W;
  const y = P.ground * L.H - 40;
  const tx = X.x * L.W - tuanSize.w / 2 + 10;
  const rope = $('#mg .tug-rope');
  if (!rope) return;
  rope.style.left = handX + 'px';
  rope.style.top = y + 'px';
  rope.style.width = Math.max(0, tx - handX) + 'px';
  $('#mg .tug-hand').style.left = (handX - 30) + 'px';
  $('#mg .tug-hand').style.top = (y - 26) + 'px';
  $('#mg .tug-knot').style.left = ((handX + tx) / 2) + 'px';
  $('#mg .tug-knot').style.top = (y - 12) + 'px';
  $('#mg .tug-mid').style.left = (mgSpot(0.46) * L.W) + 'px';
  $('#mg .tug-mid').style.top = (y + 20) + 'px';
  $('#twrap').style.setProperty('--lean', (m.done ? 0 : 6 + m.force * 6) + 'deg');
}

function tugThunder() {
  if (!MG || MG.type !== 'tug' || MG.done) return false;
  if (S.T.fear < 35) return false;
  MG.done = true;
  MG.result = '打雷了，小團丟下繩子跑掉了。';
  tr('fear', 2);
  react({ emo: 'cry', say: line('tug_thunder'), anim: 'jump', fx: 'tear', over: 18, overDur: 8000, disc: 'tug_thunder', act: '拉鋸時打雷' });
  later(1200, () => { Games.end(true); walkTo(P.nestX); });
  Games.renderPanel();
  return true;
}

function tugFinish(how) {
  const m = MG;
  if (!m || m.done) return;
  m.done = true;
  const T = S.T, dur = now() - m.t0;
  $('#twrap').style.setProperty('--lean', '0deg');
  if (how === 'quit') return;
  if (how === 'letgo') {
    S.c.tugLetGo++;
    m.result = '你突然放手，小團往後跌了一跤。';
    X.airborne = true; X.vx = 0.0011; X.vy = -0.0012;
    X.onLand = () => {
      body('dizzy', 25); X.lastFall = now();
      if (T.trust > 60 && T.grudge < 20) {
        X.playfulUntil = now() + 15000;
        react({ emo: 'happy', say: line('tug_letgo_fun'), fx: 'star', over: 4, overDur: 15000, disc: 'tug_letgo_fun', act: '突然放手' });
      } else {
        tr('grudge', 6); offense();
        react({ emo: T.fear > 50 ? 'cry' : 'angry', say: line(T.fear > 50 ? 'tug_letgo_hurt' : 'tug_letgo_angry'), anim: 'shake', fx: T.fear > 50 ? 'tear' : 'anger', disc: 'tug_letgo_angry', act: '突然放手' });
      }
    };
    $('#mg').innerHTML = '';
    Games.renderPanel();
    return;
  }
  if (how === 'tuan') {
    S.c.tugStreakYou = 0;
    if (m.easedUsed && T.trust > 50 && chance(0.4)) {
      tr('trust', 3);
      m.result = '小團贏了，但牠好像發現你在放水。';
      react({ emo: 'moved', say: line('tug_eased'), fx: 'heart', disc: 'tug_eased', act: '拉鋸輸了' });
    } else {
      tr('smug', 8); tr('trust', 1);
      X.lastGood = now();
      m.result = '小團贏了！牠得意得不得了。';
      react({ emo: 'smug', say: line('tug_win_tuan'), anim: 'bounce', fx: 'sparkle', disc: 'tug_win_tuan', act: '拉鋸輸了' });
    }
  } else {
    S.c.tugStreakYou++;
    X.lastLostTug = now();
    if (S.c.tugStreakYou >= 3) {
      tr('sorrow', 6); tr('smug', -6);
      m.result = '你又贏了。小團連輸好幾次，很受打擊。';
      react({ emo: T.fear > 45 ? 'cry' : 'speechless', say: line(T.fear > 45 ? 'tug_lose_repeat_cry' : 'tug_lose_repeat'), fx: 'tear', disc: 'tug_win_you_repeat', act: '拉鋸贏了' });
    } else if (dur < 4500) {
      tr('grudge', 3); tr('sorrow', 2);
      m.result = '你一下子就贏了。';
      react({ emo: 'sulk', say: line('tug_win_you_fast'), disc: 'tug_win_you_fast', act: '拉鋸贏了' });
    } else {
      tr('trust', 2);
      m.result = '你險勝。小團不服氣但很開心。';
      react({ emo: 'happy', say: line('tug_win_close'), fx: 'note', disc: 'tug_win_close', act: '拉鋸贏了' });
    }
  }
  if (S.played >= 3 && S.T.trust > 60 && S.B.energy > 50) { X.playfulUntil = now() + 15000; react({ over: 4, overDur: 15000 }); discover('playful_mode'); }
  Games.renderPanel();
}

// ===================== 藏鈴 =====================
const BELL_SPOTS = [{ name: '籃子', icon: '🧺' }, { name: '水桶', icon: '🪣' }, { name: '落葉堆', icon: '🍂' }];

function startBell() {
  MG = {
    type: 'bell', active: true, lockTuan: true, phase: 'hide', spot: -1, cheat: false, checked: [], count: 0,
    tick: bellTick, cmd: bellCmd, panel: bellPanel, cleanup: bellCleanup, onEnd: () => {}, timers: [], guesses: 0
  };
  bellSetup();
  bellBeginHide();
}

function bellSetup() {
  X.x = L.narrow ? 0.5 : 0.87;
  const box = $('#mg');
  box.className = 'mg-bell';
  box.innerHTML = BELL_SPOTS.map((s, i) => '<button class="spot" data-i="' + i + '" style="left:' + (bellX(i) * L.W) + 'px;top:' + (L.H * 0.985) + 'px"><span class="cover">' + s.icon + '</span><span class="bellmark">🔔</span><small>' + s.name + '</small></button>').join('') + '<div class="eyes-shut" hidden>閉上眼睛…</div>';
  box.querySelectorAll('.spot').forEach(el => el.addEventListener('click', () => bellSpotClick(+el.dataset.i)));
}

function bellT(ms, fn) { const id = setTimeout(fn, ms); MG.timers.push(id); }
function bellCleanup() { (this.timers || []).forEach(clearTimeout); }

function bellBeginHide() {
  const m = MG;
  m.phase = 'hide'; m.spot = -1; m.cheat = false; m.checked = []; m.count = 0;
  document.querySelectorAll('#mg .spot').forEach(el => el.classList.remove('lifted', 'has'));
  X.emo = 'sleep'; X.emoUntil = now() + 12000; updateFace(true);
  say(line('bell_count_start'), 1500);
  Games.renderPanel();
}

function bellTick(dt) {
  const m = MG;
  if (m.phase !== 'hide') return;
  m.cnt = (m.cnt || 0) + dt;
  if (m.cnt > 1000) {
    m.cnt = 0; m.count++;
    if (m.count < 10) { X.emoUntil = now() + 1500; say((m.count + 1) + '…', 1200); }
    else if (m.count === 10) say(line('bell_count_done'), 1500);
    else if (m.count >= 13) {
      tr('snark', 3);
      react({ emo: 'speechless', say: line('bell_not_hidden'), act: '藏鈴' });
      m.phase = 'done'; m.result = '你一直沒藏，小團睜開眼睛了。';
      Games.renderPanel();
    }
  }
}

function bellSpotClick(i) {
  const m = MG;
  if (!m || m.type !== 'bell') return;
  touch();
  if (m.phase === 'hide') { m.spot = i; m.cheat = false; Sound.bell(); bellBeginSeek(); return; }
  if (m.phase === 'guess') bellGuess(i);
}

function bellPanel() {
  const m = MG;
  if (m.phase === 'hide') return '<p class="hint">小團正閉著眼睛數數。點一個地方把鈴鐺藏進去。</p><div class="btns"><button data-g="cheat">藏在自己手裡（作弊）</button></div>';
  if (m.phase === 'seek') return '<p class="hint">小團在找…</p><div class="btns"><button data-g="swap">趁牠不注意偷換位置</button></div>';
  if (m.phase === 'cheatwait') return '<p class="hint">小團找不到鈴鐺，愣在那裡。</p><div class="btns"><button data-g="reveal">拿出來</button><button data-g="hush">不說</button></div>';
  if (m.phase === 'tuanhide') return '<p class="hint">你閉著眼睛，小團在藏…</p>';
  if (m.phase === 'guess') return '<p class="hint">鈴鐺藏在哪裡？點一個地方猜。</p><div class="btns"><button data-g="giveup">投降，找不到</button></div>';
  return '<p class="hint">' + (m.result || '') + '</p><div class="btns"><button data-g="again">再玩一次</button><button data-g="swaprole">換小團藏</button><button class="ghost" data-g="end">結束</button></div>';
}

function bellCmd(a) {
  const m = MG;
  if (!m || m.type !== 'bell') return;
  if (a === 'cheat' && m.phase === 'hide') { m.cheat = true; m.spot = -1; bellBeginSeek(); }
  if (a === 'swap' && m.phase === 'seek' && !m.cheat) bellSwap();
  if (a === 'reveal' && m.phase === 'cheatwait') bellReveal();
  if (a === 'hush' && m.phase === 'cheatwait') bellHush();
  if (a === 'again') bellBeginHide();
  if (a === 'swaprole') bellTuanHides();
  if (a === 'giveup' && m.phase === 'guess') bellGiveUp();
}

function bellBeginSeek() {
  const m = MG;
  m.phase = 'seek';
  X.emoUntil = 0;
  react({ emo: 'happy', say: line('bell_seek_start')});
  // 依照過去你常藏的地方決定先找哪裡
  const order = [0, 1, 2].sort((a, b) => (S.hide[b] + Math.random() * 0.8) - (S.hide[a] + Math.random() * 0.8));
  m.order = order;
  m.step = 0;
  if (S.c.cheatBell > 0 && chance(0.35 + 0.15 * S.c.cheatBell)) {
    bellT(1400, () => {
      if (m.cheat) {
        S.c.cheatBell++; tr('grudge', 4); tr('smug', 2); offense();
        react({ emo: 'angry', say: line('bell_cheat_caught_early'), anim: 'shake', fx: 'anger', disc: 'bell_cheat_caught', act: '藏鈴作弊' });
        m.phase = 'done'; m.result = '小團記得你上次作弊，一開始就檢查了你的手。';
        Games.renderPanel();
      } else {
        react({ emo: 'calm', say: line('bell_check_hand')});
        bellT(1300, bellCheckNext);
      }
    });
  } else bellT(1200, bellCheckNext);
  Games.renderPanel();
}

function bellCheckNext() {
  const m = MG;
  if (!m || m.phase !== 'seek') return;
  if (m.step >= 3) { bellNotFound(); return; }
  const i = m.order[m.step];
  walkTo(bellX(i), () => {
    if (!MG || MG.phase !== 'seek') return;
    const el = document.querySelector('#mg .spot[data-i="' + i + '"]');
    el.classList.add('lifted');
    m.checked.push(i);
    Sound.rustle();
    if (!m.cheat && m.spot === i) {
      el.classList.add('has');
      Sound.bell();
      const k = m.step;
      const prevSame = S.hide[i] >= 2;
      S.hide[i]++;
      X.lastGood = now(); tr('trust', 1);
      if (k === 0 && prevSame) { tr('smug', 4); react({ emo: 'smug', say: line('bell_found_fast'), fx: 'sparkle', disc: 'bell_found_fast', act: '藏鈴' }); }
      else react({ emo: 'happy', say: line(k === 0 ? 'bell_found_first' : 'bell_found'), fx: 'sparkle', anim: 'bounce', disc: 'bell_found', act: '藏鈴' });
      m.phase = 'done'; m.result = '小團在第 ' + (k + 1) + ' 個地方找到了。';
      Games.renderPanel();
      return;
    }
    say(line('bell_check_empty'), 1200);
    m.step++;
    bellT(1000, bellCheckNext);
  });
}

function bellSwap() {
  const m = MG;
  const options = [0, 1, 2].filter(i => i !== m.spot && !m.checked.includes(i));
  if (!options.length) { toast('沒有可以換的地方了'); return; }
  const noticed = chance(0.25 + S.c.bellSwapCaught * 0.2);
  m.spot = pick(options);
  Sound.rustle();
  if (noticed) {
    S.c.bellSwapCaught++; tr('grudge', 4); offense();
    react({ emo: 'angry', say: line('bell_swap_caught'), anim: 'jump', fx: 'anger', disc: 'bell_swap_caught', act: '偷換鈴鐺位置' });
    m.timers.forEach(clearTimeout); m.timers = [];
    stopWalk();
    m.phase = 'done'; m.result = '你偷換位置被抓到了。';
    Games.renderPanel();
  }
}

function bellNotFound() {
  const m = MG;
  m.phase = 'cheatwait';
  react({ emo: 'speechless', say: line('bell_not_found'), fx: 'ques', dur: 4000 });
  Games.renderPanel();
  bellT(8000, () => { if (MG && MG.phase === 'cheatwait') bellHush(true); });
}

function bellReveal() {
  const m = MG, T = S.T;
  m.phase = 'done';
  if (T.trust > 65 && T.grudge < 20) {
    react({ emo: 'happy', say: line('bell_cheat_laugh'), fx: 'note', disc: 'bell_cheat_laugh', act: '作弊後拿出鈴鐺' });
    m.result = '小團笑著說被騙了。';
  } else {
    S.c.cheatBell++; tr('grudge', 6); offense();
    react({ emo: 'angry', say: line('bell_cheat_caught'), anim: 'shake', fx: 'anger', disc: 'bell_cheat_caught', act: '作弊後拿出鈴鐺' });
    m.result = '小團氣你作弊。';
  }
  Games.renderPanel();
}

function bellHush(timeout) {
  const m = MG;
  m.phase = 'done';
  S.c.cheatBell++;
  tr('sorrow', 8); offense();
  react({ emo: 'cry', say: line('bell_cheat_cry'), fx: 'tear', n: 4, disc: 'bell_cheat_cry', act: timeout ? '一直不拿出來' : '不說' });
  S.loc.bell = 'tray';
  m.result = '鈴鐺留在你手上（回到托盤）。小團以為它不見了。';
  renderAttachments();
  Games.renderPanel();
}

function bellTuanHides() {
  const m = MG;
  if (S.loc.bell !== 'game') S.loc.bell = 'game';
  m.phase = 'tuanhide';
  m.guesses = 0;
  document.querySelectorAll('#mg .spot').forEach(el => el.classList.remove('lifted', 'has'));
  $('#mg .eyes-shut').hidden = false;
  react({ emo: 'smug', say: line('bell_tuan_hide')});
  m.spot = chance(0.4) ? 0 : Math.floor(Math.random() * 3);
  bellT(2600, () => {
    $('#mg .eyes-shut').hidden = true;
    m.phase = 'guess';
    react({ emo: 'smug', say: line('bell_ready')});
    Games.renderPanel();
  });
  Games.renderPanel();
}

function bellGuess(i) {
  const m = MG;
  m.guesses++;
  const el = document.querySelector('#mg .spot[data-i="' + i + '"]');
  el.classList.add('lifted');
  if (i === m.spot) {
    el.classList.add('has');
    Sound.bell();
    m.phase = 'done';
    if (m.guesses === 1) {
      S.c.firstHits = (S.c.firstHits || 0) + 1;
      if (S.c.firstHits >= 2) { tr('grudge', 2); react({ emo: 'sulk', say: line('bell_you_found_fast'), disc: 'bell_you_found_fast', act: '猜中鈴鐺' }); }
      else react({ emo: 'startle', say: line('bell_you_found_first'), act: '猜中鈴鐺' });
    } else react({ emo: 'happy', say: line('bell_you_found'), act: '猜中鈴鐺' });
    m.result = '你在第 ' + m.guesses + ' 次找到了。';
  } else {
    tr('smug', 1);
    react({ emo: 'smug', say: line('bell_wrong_guess'), dur: 1500 });
  }
  Games.renderPanel();
}

function bellGiveUp() {
  const m = MG;
  m.phase = 'done';
  const el = document.querySelector('#mg .spot[data-i="' + m.spot + '"]');
  el.classList.add('lifted', 'has');
  Sound.bell();
  tr('trust', 2); tr('smug', 4); X.lastGood = now();
  react({ emo: 'smug', say: line('bell_you_giveup'), fx: 'sparkle', anim: 'bounce', disc: 'bell_you_giveup', act: '投降' });
  m.result = '你投降了，小團超得意。';
  Games.renderPanel();
}

// ===================== 茶會 =====================
function startTea() {
  MG = {
    type: 'tea', active: true, lockTuan: false, cup: { tea: null, sugar: 0 }, cookie: false, cheered: false,
    perfect: false, bad: 0, cmd: teaCmd, panel: teaPanel, onEnd: teaEnd
  };
  X.x = 0.8;
  $('#mg').className = 'mg-tea';
  $('#mg').innerHTML = '<div class="tea-table" style="left:' + ((L.narrow ? 0.34 : 0.47) * L.W) + 'px;top:' + (P.ground * L.H - 8) + 'px">' +
    '<span class="t-pot">🫖</span><span class="t-cup mine">☕</span><span class="t-cup theirs"><i class="liquid"></i>🍵</span><span class="t-plate">🍽️<i class="ck">🍪</i></span><span class="t-sugar">🧂</span></div>';
  react({ emo: 'sparkle', say: line('tea_start'), fx: 'sparkle', act: '開始茶會' });
  teaRender();
}

function teaRender() {
  const m = MG;
  const cup = $('#mg .theirs');
  if (!cup) return;
  cup.classList.toggle('full', !!m.cup.tea);
  cup.classList.toggle('iced', m.cup.tea === 'iced');
  $('#mg .ck').hidden = !m.cookie;
}

function teaPanel() {
  const m = MG;
  const cupText = m.cup.tea ? (m.cup.tea === 'hot' ? '熱茶' : '冰茶') + (m.cup.sugar ? '・' + m.cup.sugar + ' 顆糖' : '') : '空杯';
  return '<p class="hint">小團的杯子：' + cupText + (m.cookie ? '　盤子：有餅乾' : '') + '</p>' +
    '<div class="btns"><button data-g="hot">倒熱茶</button><button data-g="iced">倒冰茶</button><button data-g="sugar">加一顆糖</button><button data-g="cookie">放餅乾</button>' +
    '<button class="big" data-g="cheers">乾杯</button><button data-g="steal">偷喝牠的茶</button><button data-g="spill">打翻茶杯</button></div>';
}

function teaCmd(a) {
  const m = MG, c = ctx(), T = S.T;
  if (!m || m.type !== 'tea') return;
  touch();
  if (X.sleeping) { react({ emo: 'sleep', say: line('tea_sleep_table')}); return; }
  if (a === 'hot' || a === 'iced') {
    if (m.cup.tea) { react({ emo: 'speechless', say: line('tea_cup_full')}); return; }
    m.cup.tea = a; m.cup.sugar = 0;
    Sound.splash();
    if (a === 'hot') {
      if (c.hot) { tr('snark', 2); react({ emo: 'speechless', say: line('tea_pour_hot_hot'), fx: 'sweat', act: '倒熱茶' }); }
      else if (c.cold) react({ emo: 'happy', say: line('tea_pour_hot_cold'), fx: 'steam', disc: 'tea_warm_cold', act: '倒熱茶' });
      else react({ emo: 'happy', say: line('tea_pour_hot'), fx: 'steam', act: '倒熱茶' });
    } else {
      if (c.hot) react({ emo: 'sparkle', say: line('tea_pour_iced_hot'), fx: 'sparkle', disc: 'tea_iced_hot', act: '倒冰茶' });
      else if (c.cold) { react({ emo: 'afraid', say: line('tea_pour_iced_cold'), fx: 'shiver', disc: 'tea_iced_cold', act: '倒冰茶' }); }
      else react({ emo: 'happy', say: line('tea_pour_iced'), act: '倒冰茶' });
    }
  }
  if (a === 'sugar') {
    if (!m.cup.tea) { react({ emo: 'speechless', say: line('tea_sugar_nocup')}); return; }
    m.cup.sugar++;
    const s = m.cup.sugar;
    if (s <= 2) react({ emo: 'happy', say: line(s === 1 ? 'tea_sugar_1' : 'tea_sugar_2'), act: '加糖' });
    else if (s === 3) react({ emo: 'speechless', say: line('tea_sugar_3'), act: '加糖' });
    else { tr('grudge', 1); m.bad++; react({ emo: 'angry', say: line('tea_sugar_much'), anim: 'shake', disc: 'tea_sugar_much', act: '加糖' }); }
  }
  if (a === 'cookie') {
    if (m.cookie) { react({ emo: 'happy', say: line('tea_cookie_already')}); return; }
    m.cookie = true;
    if (c.full) react({ emo: 'speechless', say: line('tea_cookie_full'), act: '放餅乾' });
    else if (c.hungry) { tr('glutton', 3); react({ emo: 'sparkle', say: line('tea_cookie_hungry'), fx: 'sparkle', act: '放餅乾' }); }
    else react({ emo: 'happy', say: line('tea_cookie'), act: '放餅乾' });
  }
  if (a === 'cheers') {
    if (!m.cup.tea) { tr('snark', 3); react({ emo: 'speechless', say: line('tea_cheers_empty'), disc: 'tea_cheers_empty', act: '乾杯' }); return; }
    const tea = m.cup.tea, sugar = m.cup.sugar, hadCookie = m.cookie;
    const tempOK = tea === 'hot' ? !c.hot : !c.cold;
    const sugarOK = sugar >= 1 && sugar <= 2;
    body('full', 8);
    S.B.warmFx = clamp(S.B.warmFx + (tea === 'hot' ? 25 : -25), -40, 40);
    m.cheered = true;
    if (m.cookie) { body('full', 15); m.cookie = false; }
    m.cup = { tea: null, sugar: 0 };
    Sound.bell();
    if (tempOK && sugarOK && hadCookie) {
      m.perfect = true;
      tr('trust', 5); tr('sorrow', -5); tr('grudge', -3); X.lastGood = now();
      react({ emo: 'moved', say: line('tea_perfect'), fx: 'heart', n: 4, disc: 'tea_perfect', act: '乾杯' });
    } else if (tempOK) react({ emo: 'happy', say: line(sugarOK ? 'tea_cheers_good' : sugar === 0 ? 'tea_cheers_bitter' : 'tea_cheers_sweet'), fx: 'note', act: '乾杯' });
    else react({ emo: tea === 'hot' ? 'speechless' : 'sad', say: line(tea === 'hot' ? 'tea_cheers_hotter' : 'tea_cheers_colder'), act: '乾杯' });
  }
  if (a === 'steal') {
    if (!m.cup.tea) { react({ emo: 'speechless', say: line('tea_steal_empty')}); return; }
    m.cup = { tea: null, sugar: 0 };
    m.bad++;
    if (T.smug > 50 || X.curSet === 11) { tr('smug', 3); react({ emo: 'smug', say: line('tea_steal_back'), disc: 'tea_steal_back', act: '偷喝牠的茶' }); }
    else { tr('grudge', 4); offense(); react({ emo: 'angry', say: line('tea_steal'), anim: 'jump', fx: 'anger', disc: 'tea_steal', act: '偷喝牠的茶' }); }
  }
  if (a === 'spill') {
    m.bad++;
    S.c.spills++;
    Sound.splash();
    const tea = m.cup.tea;
    m.cup = { tea: null, sugar: 0 };
    offense();
    if (tea) body('wet', 20);
    if (tea === 'hot') {
      tr('fear', 3); tr('grudge', 4);
      S.B.warmFx = clamp(S.B.warmFx + 15, -40, 40);
      react({ emo: 'startle', say: line('tea_spill_hot'), anim: 'jump', fx: 'excl', disc: 'tea_spill_hot', act: '打翻熱茶' });
      later(1300, () => react({ emo: 'cry', say: line('tea_spill_hot_cry'), fx: 'tear' }));
    } else if (tea === 'iced') {
      tr('grudge', 3);
      S.B.warmFx = clamp(S.B.warmFx - 20, -40, 40);
      react({ emo: 'startle', say: line('tea_spill_cold'), anim: 'jump', fx: 'shiver', disc: 'tea_spill_cold', act: '打翻冰茶' });
    } else react({ emo: 'startle', say: line('tea_spill_empty'), anim: 'jump', act: '打翻杯子' });
  }
  teaRender();
}

function teaEnd() {
  const m = MG;
  if (m.perfect) react({ emo: 'happy', say: line('tea_end_good'), fx: 'heart' });
  else if (m.bad >= 2) react({ emo: 'sulk', say: line('tea_end_bad')});
  else if (m.cheered) react({ emo: 'calm', say: line('tea_end_ok')});
}

// ===================== 畫畫 =====================
const COLORS = ['#e46a6a', '#f2b33d', '#6bb38a', '#5b8fd9', '#8a63c9', '#4a3b33'];

function startDraw() {
  const w = Math.round(L.W * (L.narrow ? 0.92 : 0.56)), h = Math.round(L.H * (L.narrow ? 0.5 : 0.46));
  MG = {
    type: 'draw', active: true, lockTuan: false, ink: 0, fastLen: 0, colors: {}, tuanDrew: false, tuanStrokes: null,
    color: COLORS[0], w, h, cmd: drawCmd, panel: drawPanel, cleanup: drawCleanup, tick: drawTick, mood: null, onEnd: () => {}
  };
  X.x = L.narrow ? 0.5 : 0.84;
  const left = L.narrow ? L.W * 0.04 : L.W * 0.12;
  const box = $('#mg');
  box.className = 'mg-draw';
  box.innerHTML = '<div class="paper" style="left:' + left + 'px;top:' + (L.H * (L.narrow ? 0.13 : 0.3)) + 'px;width:' + w + 'px;height:' + h + 'px"><canvas id="drawCanvas" width="' + w + '" height="' + h + '"></canvas><span class="mine-label">你的</span><span class="theirs-label">小團的</span></div>';
  const cv = $('#drawCanvas');
  MG.cv = cv; MG.g = cv.getContext('2d');
  MG.g.fillStyle = '#fffaf2'; MG.g.fillRect(0, 0, w, h);
  MG.g.lineCap = 'round'; MG.g.lineJoin = 'round';
  drawGuides();
  cv.addEventListener('pointerdown', drawDown);
  react({ emo: 'happy', say: line('draw_start'), act: '開始畫畫' });
  later(1800, () => { if (MG && MG.type === 'draw') tuanStartDrawing(); });
}

function drawGuides() {
  const m = MG, g = m.g;
  g.save();
  g.setLineDash([6, 8]); g.strokeStyle = 'rgba(120,100,80,.25)'; g.lineWidth = 2;
  g.beginPath(); g.moveTo(m.w * 0.6, 10); g.lineTo(m.w * 0.6, m.h - 10); g.stroke();
  g.restore();
}

function drawCleanup() { this.drawing = false; }

function drawDown(e) {
  const m = MG;
  if (!m || m.type !== 'draw') return;
  e.preventDefault();
  touch();
  const cv = m.cv;
  const r = cv.getBoundingClientRect();
  const toC = ev => ({ x: (ev.clientX - r.left) / r.width * m.w, y: (ev.clientY - r.top) / r.height * m.h, t: ev.timeStamp });
  let last = toC(e);
  m.colors[m.color] = true;
  const g = m.g;
  g.strokeStyle = m.color; g.lineWidth = 5;
  const move = ev => {
    const p = toC(ev);
    g.beginPath(); g.moveTo(last.x, last.y); g.lineTo(p.x, p.y); g.stroke();
    const d = Math.hypot(p.x - last.x, p.y - last.y);
    m.ink += d;
    const dt = Math.max(1, p.t - last.t);
    if (d / dt > 1.6) m.fastLen += d;
    last = p;
  };
  const up = () => { window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up); window.removeEventListener('pointercancel', up); };
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', up);
  window.addEventListener('pointercancel', up);
}

function tuanMood() {
  const T = S.T;
  if (T.grudge > 40) return 'storm';
  if (T.sorrow > 35 || T.fear > 60) return 'rain';
  if (T.smug > 50) return 'self';
  if (T.trust > 70) return 'heart';
  return pick(['flower', 'sun', 'sprout', 'self']);
}

function tuanStartDrawing() {
  const m = MG;
  if (X.sleeping) return;
  const mood = tuanMood();
  m.mood = mood;
  const ox = m.w * 0.62, ow = m.w * 0.36, oy = 18, oh = m.h - 36;
  const cx = ox + ow / 2, cy = oy + oh / 2;
  const strokes = [];
  const circle = (x, y, r, col, n) => { const pts = []; for (let i = 0; i <= (n || 28); i++) { const a = i / (n || 28) * Math.PI * 2; pts.push([x + Math.cos(a) * r, y + Math.sin(a) * r]); } strokes.push({ col, pts }); };
  const stroke = (pts, col) => strokes.push({ col, pts });
  if (mood === 'flower') {
    for (let k = 0; k < 6; k++) { const a = k / 6 * Math.PI * 2; circle(cx + Math.cos(a) * 22, cy - 20 + Math.sin(a) * 22, 14, '#e46a6a', 16); }
    circle(cx, cy - 20, 10, '#f2b33d', 14);
    stroke([[cx, cy - 6], [cx - 4, cy + 30], [cx, cy + 60]], '#6bb38a');
  } else if (mood === 'sun') {
    circle(cx, cy, 28, '#f2b33d');
    for (let k = 0; k < 10; k++) { const a = k / 10 * Math.PI * 2; stroke([[cx + Math.cos(a) * 38, cy + Math.sin(a) * 38], [cx + Math.cos(a) * 56, cy + Math.sin(a) * 56]], '#f2b33d'); }
  } else if (mood === 'heart') {
    const pts = []; for (let i = 0; i <= 40; i++) { const t = i / 40 * Math.PI * 2; pts.push([cx + 2.4 * 16 * Math.pow(Math.sin(t), 3), cy - 2.4 * (13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t))]); }
    stroke(pts, '#e46a6a');
  } else if (mood === 'sprout') {
    stroke([[cx, cy + 60], [cx, cy]], '#6bb38a');
    stroke([[cx, cy + 10], [cx - 30, cy - 15], [cx - 5, cy - 5]], '#6bb38a');
    stroke([[cx, cy], [cx + 30, cy - 25], [cx + 4, cy - 8]], '#6bb38a');
    stroke([[cx - 40, cy + 62], [cx + 40, cy + 62]], '#8a6a4f');
  } else if (mood === 'rain') {
    stroke([[cx - 50, cy - 30], [cx - 40, cy - 55], [cx - 10, cy - 60], [cx + 10, cy - 70], [cx + 40, cy - 55], [cx + 55, cy - 30], [cx - 50, cy - 30]], '#7f8ea3');
    for (let k = 0; k < 6; k++) stroke([[cx - 40 + k * 16, cy - 15], [cx - 46 + k * 16, cy + 10]], '#5b8fd9');
    strokes.push({ text: faceOf(X.curSet, 'sad'), x: cx, y: cy + 50, col: '#4a3b33' });
  } else if (mood === 'storm') {
    const pts = []; for (let i = 0; i < 26; i++) pts.push([ox + 10 + Math.random() * (ow - 20), oy + 10 + Math.random() * (oh - 20)]);
    stroke(pts, '#4a3b33');
    stroke([[cx, cy - 60], [cx - 15, cy - 10], [cx + 8, cy - 10], [cx - 8, cy + 45]], '#f2b33d');
  } else {
    circle(cx, cy, 52, '#e8a7a0');
    strokes.push({ text: faceOf(X.curSet, 'happy'), x: cx, y: cy + 6, col: '#4a3b33' });
  }
  m.tuanStrokes = strokes; m.tdIdx = 0; m.tdPt = 0; m.tdAcc = 0; m.tuanDrawing = true;
  if (mood === 'rain' || mood === 'storm') react({ emo: mood === 'storm' ? 'sulk' : 'sad', say: line(mood === 'storm' ? 'draw_mood_storm' : 'draw_mood_rain'), disc: 'draw_mood', act: '小團畫畫' });
  else react({ emo: 'happy', say: line('draw_tuan_start'), fx: 'note' });
}

function drawTick(dt) {
  const m = MG;
  if (!m.tuanDrawing || !m.tuanStrokes) return;
  m.tdAcc += dt;
  const g = m.g;
  while (m.tdAcc > 30 && m.tuanDrawing) {
    m.tdAcc -= 30;
    const s = m.tuanStrokes[m.tdIdx];
    if (!s) { m.tuanDrawing = false; m.tuanDrew = true; X.lastGood = now(); Games.renderPanel(); return; }
    if (s.text) {
      g.fillStyle = s.col; g.font = '22px sans-serif'; g.textAlign = 'center';
      g.fillText(s.text, s.x, s.y);
      m.tdIdx++; m.tdPt = 0; continue;
    }
    if (m.tdPt >= s.pts.length - 1) { m.tdIdx++; m.tdPt = 0; continue; }
    const a = s.pts[m.tdPt], b = s.pts[m.tdPt + 1];
    g.strokeStyle = s.col; g.lineWidth = 4;
    g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke();
    m.tdPt++;
  }
}

function drawPanel() {
  const m = MG;
  return '<div class="swatches">' + COLORS.map(c => '<button class="sw' + (c === m.color ? ' on' : '') + '" style="background:' + c + '" data-g="color:' + c + '" aria-label="顏色"></button>').join('') + '</div>' +
    '<div class="btns"><button data-g="praise">誇牠的畫</button><button data-g="ruin">塗掉牠的畫</button><button data-g="show">給牠看我的畫</button>' +
    '<button data-g="face">畫在牠臉上</button><button data-g="hang">掛起來</button><button data-g="tear">撕掉</button><button class="ghost" data-g="new">新的一張</button></div>' +
    '<p class="hint">' + (m.tuanDrawing ? '小團正在畫…' : m.tuanDrew ? '小團畫好了。' : '小團正在想要畫什麼。') + '在紙上拖動就能畫。</p>';
}

function drawCmd(a, b) {
  const m = MG, T = S.T;
  if (!m || m.type !== 'draw') return;
  if (a === 'color') { m.color = b; return; }
  if (X.sleeping) { react({ emo: 'sleep', say: line('draw_sleep')}); return; }
  if (a === 'praise') {
    if (!m.tuanDrew) { react({ emo: 'speechless', say: line('draw_praise_early')}); return; }
    tr('smug', 5); tr('trust', 2); tr('sorrow', -3);
    if (m.mood === 'rain' || m.mood === 'storm') react({ emo: 'moved', say: line('draw_praise_mood'), fx: 'heart', disc: 'draw_praise', act: '誇牠的畫' });
    else if (T.trust > 60) react({ emo: 'shy', say: line('draw_praise_shy'), fx: 'heart', anim: 'bounce', disc: 'draw_praise', act: '誇牠的畫' });
    else react({ emo: 'smug', say: line('draw_praise_smug'), fx: 'sparkle', disc: 'draw_praise', act: '誇牠的畫' });
  }
  if (a === 'ruin') {
    if (!m.tuanDrew && !m.tuanDrawing) { react({ emo: 'speechless', say: line('draw_ruin_nothing')}); return; }
    m.tuanDrawing = false; m.tuanDrew = false; m.ruined = true;
    const g = m.g;
    g.strokeStyle = '#4a3b33'; g.lineWidth = 8;
    g.beginPath();
    for (let i = 0; i < 18; i++) g.lineTo(m.w * 0.62 + Math.random() * m.w * 0.36, 15 + Math.random() * (m.h - 30));
    g.stroke();
    tr('sorrow', 8); tr('grudge', 6); offense();
    react({ emo: T.fear > 50 || T.sorrow > 40 ? 'cry' : 'angry', say: line('draw_ruin'), anim: 'shake', fx: 'tear', n: 3, disc: 'draw_ruin', act: '塗掉牠的畫' });
  }
  if (a === 'show') {
    const ncol = Object.keys(m.colors).length;
    if (m.ink < 250) { tr('snark', 2); react({ emo: 'speechless', say: line('draw_show_bad'), disc: 'draw_show_bad', act: '給牠看你的畫' }); }
    else if (m.fastLen > m.ink * 0.6) react({ emo: 'dizzy', say: line('draw_show_scribble'), disc: 'draw_show_scribble', act: '給牠看你的畫' });
    else if (T.grudge > 40) react({ emo: 'sulk', say: line('draw_show_grudge'), act: '給牠看你的畫' });
    else if (ncol >= 3) { tr('trust', 2); react({ emo: 'sparkle', say: line(X.curSet === 3 ? 'draw_show_good_tsun' : 'draw_show_good'), fx: 'sparkle', disc: 'draw_show_good', act: '給牠看你的畫' }); }
    else { tr('trust', 1); react({ emo: 'happy', say: line('draw_show_ok'), fx: 'note', act: '給牠看你的畫' }); }
  }
  if (a === 'face') { useItemOnTuan('crayon'); }
  if (a === 'hang') {
    const thumb = document.createElement('canvas');
    thumb.width = 180; thumb.height = Math.round(180 * m.h / m.w);
    thumb.getContext('2d').drawImage(m.cv, 0, 0, thumb.width, thumb.height);
    let url = '';
    try { url = thumb.toDataURL('image/jpeg', 0.7); } catch (e) { url = ''; }
    if (url) {
      S.wall.push({ url, tuan: m.tuanDrew });
      if (S.wall.length > 4) S.wall.shift();
      UI.renderWall && UI.renderWall();
    }
    if (m.tuanDrew) { tr('trust', 6); tr('smug', 4); X.lastGood = now(); react({ emo: 'moved', say: line('draw_hang'), fx: 'heart', n: 4, disc: 'draw_hang', act: '把畫掛起來' }); }
    else react({ emo: 'happy', say: line('draw_hang_mine'), act: '把畫掛起來' });
    drawClear();
  }
  if (a === 'tear') {
    if (m.tuanDrew || m.tuanDrawing) {
      S.c.tornDrawings++;
      tr('sorrow', 10); tr('grudge', 5); offense();
      react({ emo: 'cry', say: line('draw_tear'), fx: 'tear', n: 4, disc: 'draw_tear', act: '撕掉畫' });
    } else react({ emo: 'startle', say: line('draw_tear_empty'), anim: 'jump', act: '撕掉畫' });
    $('#mg .paper').classList.add('torn');
    later(500, () => { const p = $('#mg .paper'); if (p) p.classList.remove('torn'); });
    drawClear();
  }
  if (a === 'new') drawClear(true);
}

function drawClear(restart) {
  const m = MG;
  m.g.fillStyle = '#fffaf2'; m.g.fillRect(0, 0, m.w, m.h);
  drawGuides();
  m.ink = 0; m.fastLen = 0; m.colors = {}; m.tuanDrew = false; m.tuanDrawing = false; m.tuanStrokes = null;
  later(restart ? 1200 : 2500, () => { if (MG === m && !m.tuanDrawing && !m.tuanDrew) tuanStartDrawing(); });
}

// ===================== 種芽（不是一局一局的遊戲，會一直長） =====================
const SPROUT_STAGE = ['種子', '冒芽', '小苗', '長葉', '花苞', '開花'];
const SPROUT_STAGE_S = ['种子', '嫩芽', '小苗', '长叶', '花苞', '开花'];

function sproutTick() {
  const sp = S.sprout, env = S.env;
  if (sp.stage < 0 || sp.dead) return;
  const covered = S.loc.umbrella === 'pot';
  const warmed = S.loc.blanket === 'pot';
  if (env.rain > 5 && !covered) sp.water = clamp(sp.water + env.rain * 0.04, 0, 100);
  sp.water = clamp(sp.water - 0.35 - Math.max(0, env.temp - 50) * 0.012, 0, 100);
  let dh = 0.4;
  if (sp.water < 10) dh = -1.2;
  else if (sp.water > 92) dh = -0.8;
  if (env.temp < 18 && !warmed) dh = -1;
  if (env.temp > 85) dh = -0.8;
  if (env.wind > 70 && sp.stage >= 1 && !covered) dh = Math.min(dh, -0.8);
  sp.health = clamp(sp.health + dh, 0, 100);
  if (sp.health <= 0) {
    sp.dead = true;
    if (!X.sleeping) { tr('sorrow', 12); react({ emo: 'cry', say: line('sprout_dead'), fx: 'tear', n: 4, disc: 'sprout_dead', act: '芽枯了' }); }
    UI.renderPot && UI.renderPot();
    return;
  }
  if (sp.stage < 5 && sp.water >= 25 && sp.water <= 85 && env.temp >= 25 && env.temp <= 80) {
    const sunny = env.rain < 10 && !env.thunder && !covered;
    sp.growth += 1.2 + (sunny ? 0.8 : 0);
    if (sp.growth >= 100) {
      sp.growth = 0; sp.stage++;
      if (sp.stage === 5) {
        tr('trust', 8); tr('sorrow', -10); X.lastGood = now();
        if (!X.sleeping) react({ emo: 'sparkle', say: line('sprout_bloom'), fx: 'sparkle', n: 5, anim: 'bounce', disc: 'sprout_bloom', act: '芽開花了' });
      } else if (!X.sleeping) react({ emo: 'happy', say: line('sprout_grow', { stage: SPROUT_STAGE_S[sp.stage] }), fx: 'note', act: '芽長大了' });
    }
  }
  UI.renderPot && UI.renderPot();
  if (Games.view === 'sprout') updateSproutStats();
}

function sproutAI() {
  const sp = S.sprout;
  if (sp.stage < 0) return false;
  if (sp.dead) {
    if (chance(0.12)) { walkTo(P.potX - 0.08, () => react({ emo: 'sad', say: line('sprout_dead_visit')})); return true; }
    return false;
  }
  if (sp.water < 22 && S.B.energy > 25 && chance(0.7)) {
    react({ emo: 'afraid', say: line('sprout_thirsty')});
    walkTo(P.potX - 0.08, () => tuanWaters());
    return true;
  }
  if (sp.stage === 5 && chance(0.12)) { walkTo(P.potX - 0.08, () => react({ emo: 'sparkle', say: line('sprout_admire'), fx: 'sparkle' })); return true; }
  return false;
}

function tuanWaters() {
  const sp = S.sprout;
  if (sp.stage < 0 || sp.dead) return;
  if (S.B.energy > 60 && (now() < X.playfulUntil || chance(0.3))) {
    sp.water = clamp(sp.water + 50, 0, 100);
    react({ emo: 'shy', say: line('sprout_overwater'), disc: 'sprout_overwater', act: '小團澆水' });
  } else {
    sp.water = clamp(sp.water + 28, 0, 100);
    X.lastGood = now();
    react({ emo: 'happy', say: line('sprout_water_self'), fx: 'note', disc: 'sprout_water_self', act: '小團澆水' });
  }
  Sound.splash();
  UI.renderPot && UI.renderPot();
}

function sproutPanel() {
  const sp = S.sprout;
  let html = '';
  if (sp.stage < 0) html = '<p class="hint">花盆還是空的。</p><div class="btns"><button class="big" data-g="sp:plant">和小團一起播種</button></div>';
  else if (sp.dead) html = '<p class="hint">芽枯掉了。</p><div class="btns"><button data-g="sp:pull">把它拔掉</button><button data-g="sp:plant">重新播種</button></div>';
  else html = '<div class="sp-stats" id="spStats"></div>' +
    '<div class="btns"><button data-g="sp:water">澆水</button><button data-g="sp:tuan">讓小團澆水</button><button data-g="sp:talk">一起對芽說話</button><button data-g="sp:pull">拔掉</button></div>' +
    '<p class="hint">雨會澆水，太熱會乾，太冷或大風會傷到它。把雨傘拖到花盆上可以遮風雨，毯子可以保暖，水滴可以澆水。</p>';
  setTimeout(updateSproutStats, 0);
  return '<div class="game-head"><b>🌱 種芽</b><button class="ghost" data-g="end">返回</button></div>' + html;
}

function updateSproutStats() {
  const el = $('#spStats');
  if (!el) return;
  const sp = S.sprout;
  const row = (name, v, cls) => '<div class="meter ' + (cls || '') + '"><span>' + name + '</span><div class="bar"><i style="width:' + Math.round(v) + '%"></i></div></div>';
  el.innerHTML = '<p><b>' + SPROUT_STAGE[sp.stage] + '</b>' + (sp.stage < 5 ? '　成長 ' + Math.round(sp.growth) + '%' : '') + '</p>' +
    row('水分', sp.water, sp.water < 20 || sp.water > 90 ? 'warn' : '') + row('健康', sp.health, sp.health < 35 ? 'warn' : '');
}

function sproutCmd(a) {
  const sp = S.sprout, T = S.T;
  touch();
  if (a === 'plant') {
    if (sp.stage >= 0 && !sp.dead) return;
    Object.assign(sp, { stage: 0, growth: 0, water: 45, health: 100, dead: false });
    if (S.loc.bell === 'pot') S.loc.bell = 'tray';
    if (!X.sleeping) { walkTo(P.potX - 0.08); react({ emo: 'sparkle', say: line('sprout_plant'), fx: 'sparkle', act: '播種' }); }
  }
  if (a === 'water') { waterSprout(); }
  if (a === 'tuan') {
    if (X.sleeping) { toast('小團睡著了'); return; }
    if (sp.stage < 0 || sp.dead) return;
    walkTo(P.potX - 0.08, () => tuanWaters());
  }
  if (a === 'talk') {
    if (sp.stage < 0 || sp.dead) return;
    if (now() - (sp.talkAt || 0) < 8000) { react({ emo: 'speechless', say: line('sprout_talk_again')}); return; }
    sp.talkAt = now();
    sp.growth = Math.min(99, sp.growth + 4);
    tr('trust', 1);
    if (!X.sleeping) react({ emo: 'happy', say: line('sprout_talk'), fx: 'heart', disc: 'sprout_talk', act: '對芽說話' });
  }
  if (a === 'pull') {
    if (sp.stage < 0) return;
    const wasDead = sp.dead, st = sp.stage;
    Object.assign(sp, { stage: -1, growth: 0, water: 50, health: 100, dead: false });
    ['umbrella', 'blanket', 'bell'].forEach(id => { if (S.loc[id] === 'pot') S.loc[id] = 'tray'; });
    if (!X.sleeping) {
      if (wasDead) react({ emo: 'sad', say: line('sprout_pull_dead'), act: '拔掉枯芽' });
      else if (st === 0) { tr('grudge', 5); offense(); react({ emo: 'startle', say: line('sprout_pull_seed'), anim: 'jump', act: '挖出種子' }); }
      else { tr('grudge', 15); tr('sorrow', 15); offense(2); react({ emo: 'cry', say: line('sprout_pulled'), anim: 'shake', fx: 'tear', n: 5, over: 18, overDur: 8000, disc: 'sprout_pulled', act: '拔掉芽' }); }
    }
  }
  UI.renderPot && UI.renderPot();
  renderAttachments();
  Games.renderPanel();
}

function waterSprout() {
  const sp = S.sprout;
  if (sp.stage < 0 || sp.dead) { toast('花盆裡沒有活著的芽'); return; }
  sp.water = clamp(sp.water + 30, 0, 100);
  Sound.splash();
  if (sp.water > 92 && !X.sleeping) react({ emo: 'afraid', say: line('sprout_too_wet'), act: '澆水' });
  else if (!X.sleeping) react({ emo: 'happy', say: line('sprout_water'), act: '澆水' });
  UI.renderPot && UI.renderPot();
}

function useItemOnPot(id) {
  touch();
  const sp = S.sprout;
  if (sp.stage < 0) { toast('花盆是空的，先到「小遊戲 → 種芽」播種'); return false; }
  const awake = !X.sleeping;
  const r = o => { if (awake) react(o); };
  switch (id) {
    case 'water': waterSprout(); break;
    case 'ice': sp.water = clamp(sp.water + 10, 0, 100); sp.health = clamp(sp.health - 10, 0, 100); r({ emo: 'afraid', say: line('pot_ice'), disc: 'sprout_cold', act: '冰塊放進花盆' }); break;
    case 'tea': sp.health = clamp(sp.health - 12, 0, 100); r({ emo: 'speechless', say: line('pot_tea'), disc: 'sprout_tea', act: '茶倒進花盆' }); break;
    case 'cookie': r({ emo: 'speechless', say: line('pot_cookie'), act: '餅乾放進花盆' }); break;
    case 'fan': sp.water = clamp(sp.water - 20, 0, 100); r({ emo: 'calm', say: line('pot_fan'), act: '對芽搧風' }); break;
    case 'crayon': r({ emo: 'happy', say: line('pot_crayon'), act: '在花盆上畫畫' }); break;
    case 'umbrella': S.loc.umbrella = 'pot'; r({ emo: 'happy', say: line('pot_umbrella'), act: '雨傘撐在花盆上' }); break;
    case 'blanket': S.loc.blanket = 'pot'; r({ emo: 'happy', say: line('pot_blanket'), act: '毯子蓋在花盆上' }); break;
    case 'bell': S.loc.bell = 'pot'; Sound.bell(); r({ emo: 'sparkle', say: line('pot_bell'), act: '鈴鐺掛在芽上' }); break;
    case 'teddy': r({ emo: 'happy', say: line('pot_teddy'), act: '布偶放在花盆旁' }); return false;
    default: return false;
  }
  UI.renderPot && UI.renderPot();
  renderAttachments();
  return true;
}
