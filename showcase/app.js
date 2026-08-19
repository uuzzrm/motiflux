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
    if (progress < .08) return "blank";
    if (progress < .18) return "spark";
    if (progress < .38) return "arc";
    if (progress < .52) return "bar";
    if (progress < .66) return "monogram";
    if (progress < .94) return "wordmark";
    return "canonical";
  }
  function render(player, progress) {
    const p = clamp(progress, 0, 1);
    player.stage.style.setProperty("--motion-progress", p.toFixed(4));
    player.stage.dataset.state = phaseFor(p);
    if (player.phase) player.phase.textContent = phaseFor(p);
    if (player.progress) player.progress.style.width = `${p * 100}%`;
    if (player.time) player.time.textContent = `${(p * player.duration / 1000).toFixed(1)}s`;
  }
  function showGif(player, restart) {
    if (!player.gif) return;
    player.gif.src = restart ? `${player.src}?play=${Date.now()}` : player.src;
    player.gif.hidden = false;
    if (player.poster) player.poster.hidden = true;
  }
  function showPoster(player, source) {
    if (!player.gif) return;
    player.gif.hidden = true;
    if (player.poster) {
      player.poster.src = source || player.posterSrc;
      player.poster.hidden = false;
    }
  }
  function freezeCurrentFrame(player) {
    if (!player.gif || !player.gif.complete || !player.gif.naturalWidth) { showPoster(player); return; }
    const canvas = document.createElement("canvas");
    canvas.width = player.gif.naturalWidth;
    canvas.height = player.gif.naturalHeight;
    try {
      canvas.getContext("2d").drawImage(player.gif, 0, 0);
      showPoster(player, canvas.toDataURL("image/png"));
    } catch (error) {
      // A local GIF should be readable; keep the canonical poster as a safe fallback.
      showPoster(player);
    }
  }
  function stop(player) { player.playing = false; if (player.frame) cancelAnimationFrame(player.frame); player.frame = 0; }
  function tick(player, timestamp) {
    if (!player.playing || motion === "paused" || motion === "reduced") return;
    if (player.last === null) player.last = timestamp;
    player.current += timestamp - player.last;
    player.last = timestamp;
    const progress = clamp(player.current / player.duration, 0, 1);
    render(player, progress);
    if (progress >= 1) { stop(player); render(player, 1); showPoster(player); } else player.frame = requestAnimationFrame((next) => tick(player, next));
  }
  function play(player) {
    if (prefersReduced) { render(player, 1); showPoster(player); return; }
    // A portable GIF cannot seek. Resume by restarting it so the timer and pixels agree.
    const restart = player.current > 0 || player.paused || player.current >= player.duration;
    if (restart) { player.current = 0; render(player, 0); }
    player.paused = false;
    showGif(player, restart);
    player.playing = true; player.last = null; if (!player.frame) player.frame = requestAnimationFrame((next) => tick(player, next));
  }
  function pause(player) { stop(player); player.paused = true; freezeCurrentFrame(player); }
  function replay(player) { stop(player); player.current = 0; player.paused = false; render(player, 0); showGif(player, true); play(player); }
  stages.forEach((stage) => {
    const player = { stage, effect: stage.dataset.effect || "plain", duration: Number(stage.dataset.durationMs || 1800), current: 0, last: null, playing: false, paused: false, frame: 0, src: stage.dataset.animationSrc || "", posterSrc: stage.dataset.posterSrc || "", gif: stage.querySelector(".growth-gif"), poster: stage.querySelector(".motion-freeze"), phase: stage.querySelector("[data-motion-phase]"), progress: stage.closest(".motion-output")?.querySelector("[data-motion-progress]"), time: stage.closest(".motion-output")?.querySelector("[data-motion-time]") };
    player.playButton = stage.closest(".motion-output")?.querySelector('[data-card-action="play"]');
    player.pauseButton = stage.closest(".motion-output")?.querySelector('[data-card-action="pause"]');
    player.replayButton = stage.closest(".motion-output")?.querySelector('[data-card-action="replay"]');
    player.playButton?.addEventListener("click", () => { setMotion("running"); play(player); });
    player.pauseButton?.addEventListener("click", () => pause(player));
    player.replayButton?.addEventListener("click", () => { setMotion("running"); replay(player); });
    players.push(player);
    render(player, prefersReduced ? 1 : 0);
    if (prefersReduced) showPoster(player); else play(player);
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
