(() => {
  "use strict";
  const body = document.body;
  const cards = [...document.querySelectorAll(".theme-card")];
  const stages = [...document.querySelectorAll("[data-motion-card]")];
  const filter = document.querySelector("[data-filter]");
  const status = document.querySelector("[data-filter-status]");
  const prefersReduced = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  const presets = {
    grid: [-28, 16, -6, .78], quiet: [0, 10, 0, .9], scan: [-26, 0, 0, .8],
    field: [-10, 22, -8, .72], ring: [0, 0, -22, .78], shield: [0, 24, 0, .74],
    burst: [0, 0, -18, .76], track: [-42, 0, 0, .8], speed: [-48, 6, -10, .7],
    curtain: [0, 0, 0, .84], wave: [16, 22, 8, .76], orbit: [0, -16, 16, .78],
    plain: [0, 12, 0, .86]
  };
  const players = [];
  let motion = prefersReduced ? "reduced" : "running";
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const ease = (value, effect) => {
    const p = clamp(value, 0, 1);
    if (effect === "speed" || effect === "burst") return 1 - Math.pow(1 - p, 3);
    if (effect === "quiet" || effect === "curtain") return p * p * (3 - 2 * p);
    if (effect === "wave" || effect === "orbit") return p < .78 ? p / .78 : 1 - Math.pow((1 - p) / .22, 2) * .035;
    return 1 - Math.pow(1 - p, 2.4);
  };
  function phaseFor(progress) {
    if (progress < .16) return "source";
    if (progress < .42) return "reveal";
    if (progress < .78) return "transform";
    if (progress < .96) return "settle";
    return "canonical";
  }
  function render(player, progress) {
    const p = clamp(progress, 0, 1);
    const eased = ease(p, player.effect);
    const [startX, startY, startRotate, startScale] = presets[player.effect] || presets.plain;
    const settle = p > .78 ? (p - .78) / .22 : 0;
    const overshoot = (player.effect === "sports-impact" || player.effect === "speed" || player.effect === "burst") ? Math.sin(Math.min(1, p) * Math.PI) * .06 : 0;
    const scale = startScale + (1 - startScale) * eased + overshoot;
    player.stage.style.setProperty("--motion-progress", p.toFixed(4));
    player.stage.style.setProperty("--motion-x", ((1 - eased) * startX).toFixed(3));
    player.stage.style.setProperty("--motion-y", ((1 - eased) * startY).toFixed(3));
    player.stage.style.setProperty("--motion-scale", scale.toFixed(4));
    player.stage.style.setProperty("--motion-rotate", `${((1 - eased) * startRotate).toFixed(3)}deg`);
    player.stage.style.setProperty("--motion-opacity", (.06 + eased * .94).toFixed(4));
    player.stage.dataset.state = phaseFor(p);
    if (player.phase) player.phase.textContent = phaseFor(p);
    if (player.progress) player.progress.style.width = `${p * 100}%`;
    if (player.time) player.time.textContent = `${(p * player.duration / 1000).toFixed(1)}s`;
  }
  function stop(player) { player.playing = false; if (player.frame) cancelAnimationFrame(player.frame); player.frame = 0; }
  function tick(player, timestamp) {
    if (!player.playing || motion === "paused" || motion === "reduced") return;
    if (player.last === null) player.last = timestamp;
    player.current += (timestamp - player.last) * player.tempo;
    player.last = timestamp;
    const progress = clamp(player.current / player.duration, 0, 1);
    render(player, progress);
    if (progress >= 1) stop(player); else player.frame = requestAnimationFrame((next) => tick(player, next));
  }
  function play(player) {
    if (prefersReduced) { render(player, 1); return; }
    player.playing = true; player.last = null; if (!player.frame) player.frame = requestAnimationFrame((next) => tick(player, next));
  }
  function pause(player) { stop(player); }
  function replay(player) { stop(player); player.current = 0; render(player, 0); play(player); }
  stages.forEach((stage) => {
    const player = { stage, effect: stage.dataset.effect || "plain", duration: Number(stage.dataset.durationMs || 1800), tempo: Number(stage.dataset.tempo || 1), current: 0, last: null, playing: false, frame: 0, phase: stage.querySelector("[data-motion-phase]"), progress: stage.closest(".motion-output")?.querySelector("[data-motion-progress]"), time: stage.closest(".motion-output")?.querySelector("[data-motion-time]") };
    player.playButton = stage.closest(".motion-output")?.querySelector('[data-card-action="play"]');
    player.pauseButton = stage.closest(".motion-output")?.querySelector('[data-card-action="pause"]');
    player.replayButton = stage.closest(".motion-output")?.querySelector('[data-card-action="replay"]');
    player.playButton?.addEventListener("click", () => { setMotion("running"); play(player); });
    player.pauseButton?.addEventListener("click", () => pause(player));
    player.replayButton?.addEventListener("click", () => { setMotion("running"); replay(player); });
    players.push(player);
    render(player, prefersReduced ? 1 : 0);
    if (!prefersReduced) play(player);
  });
  function setMotion(next) {
    motion = next;
    body.dataset.motion = next;
    document.querySelectorAll("[data-motion-label]").forEach((node) => {
      node.textContent = next === "reduced" ? "REDUCED" : next.toUpperCase();
    });
  }
  function replayAll() {
    players.forEach(replay);
    setMotion(prefersReduced ? "reduced" : "running");
  }
  document.querySelector("[data-action=play]")?.addEventListener("click", () => { setMotion("running"); players.forEach(play); });
  document.querySelector("[data-action=pause]")?.addEventListener("click", () => { setMotion("paused"); players.forEach(pause); });
  document.querySelector("[data-action=replay]")?.addEventListener("click", replayAll);
  filter?.addEventListener("input", () => {
    const query = filter.value.trim().toLowerCase();
    let visible = 0;
    cards.forEach((card) => {
      const match = !query || card.dataset.search.toLowerCase().includes(query);
      card.hidden = !match;
      if (match) visible += 1;
    });
    if (status) status.textContent = `${visible} of ${cards.length} routes shown`;
  });
  document.addEventListener("visibilitychange", () => { if (document.hidden) players.forEach(pause); });
  setMotion(motion);
  window.__motifluxShowcaseReady = true;
  window.__motifluxShowcaseControl = { play: () => { setMotion("running"); players.forEach(play); }, pause: () => { setMotion("paused"); players.forEach(pause); }, replay: replayAll, setMotion };
})();
