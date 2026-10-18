'use strict';
// ===== 聲音：全部用 WebAudio 即時合成，第一次互動後才啟動 =====
const Sound = {
  ctx: null, master: null, on: true, rainGain: null, windGain: null,

  init() {
    if (this.ctx) return;
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    try {
      this.ctx = new AC();
    } catch (e) { return; }
    this.master = this.ctx.createGain();
    this.master.gain.value = this.on ? 0.5 : 0;
    this.master.connect(this.ctx.destination);
    this.noiseBuf = this.makeNoise(2);
    this.rainGain = this.loopNoise('highpass', 1200, 0.7);
    this.windGain = this.loopNoise('bandpass', 380, 1.2);
  },

  makeNoise(seconds) {
    const len = this.ctx.sampleRate * seconds;
    const buf = this.ctx.createBuffer(1, len, this.ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
    return buf;
  },

  loopNoise(type, freq, q) {
    const src = this.ctx.createBufferSource();
    src.buffer = this.noiseBuf;
    src.loop = true;
    const f = this.ctx.createBiquadFilter();
    f.type = type; f.frequency.value = freq; f.Q.value = q;
    const g = this.ctx.createGain();
    g.gain.value = 0;
    src.connect(f); f.connect(g); g.connect(this.master);
    src.start();
    return g;
  },

  setOn(v) {
    this.on = v;
    if (this.master) this.master.gain.setTargetAtTime(v ? 0.5 : 0, this.ctx.currentTime, 0.05);
  },

  ambient(rain, wind) {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    this.rainGain.gain.setTargetAtTime(rain / 100 * 0.16, t, 0.4);
    this.windGain.gain.setTargetAtTime(wind / 100 * 0.22, t, 0.6);
  },

  tone(freq, dur, type, vol, slideTo) {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const o = this.ctx.createOscillator();
    const g = this.ctx.createGain();
    o.type = type || 'sine';
    o.frequency.setValueAtTime(freq, t);
    if (slideTo) o.frequency.exponentialRampToValueAtTime(slideTo, t + dur);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(vol || 0.2, t + 0.015);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(this.master);
    o.start(t); o.stop(t + dur + 0.05);
  },

  bell() {
    this.tone(1318, 1.4, 'sine', 0.18);
    this.tone(2637, 0.9, 'sine', 0.06);
    this.tone(3951, 0.5, 'triangle', 0.03);
  },
  pop() { this.tone(520, 0.12, 'triangle', 0.12, 780); },
  boing() { this.tone(300, 0.35, 'sine', 0.15, 900); },
  squeak() { this.tone(900, 0.22, 'square', 0.05, 1500); },
  sad() { this.tone(520, 0.6, 'sine', 0.08, 300); },
  chirp() { this.tone(880, 0.08, 'sine', 0.08, 1100); },
  splash() { this.burst(0.35, 'bandpass', 1800, 0.25); },
  rustle() { this.burst(0.25, 'highpass', 2500, 0.12); },

  burst(dur, type, freq, vol) {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const src = this.ctx.createBufferSource();
    src.buffer = this.noiseBuf;
    const f = this.ctx.createBiquadFilter();
    f.type = type; f.frequency.value = freq;
    const g = this.ctx.createGain();
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    src.connect(f); f.connect(g); g.connect(this.master);
    src.start(t, Math.random()); src.stop(t + dur + 0.05);
  },

  thunder() {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const src = this.ctx.createBufferSource();
    src.buffer = this.noiseBuf;
    const f = this.ctx.createBiquadFilter();
    f.type = 'lowpass';
    f.frequency.setValueAtTime(900, t);
    f.frequency.exponentialRampToValueAtTime(120, t + 2.2);
    const g = this.ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.9, t + 0.05);
    g.gain.exponentialRampToValueAtTime(0.25, t + 0.5);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 2.6);
    src.connect(f); f.connect(g); g.connect(this.master);
    src.start(t); src.stop(t + 2.7);
  }
};
