(() => {
  "use strict";
  const body = document.body;
  body.dataset.runtimeState = "booting";
  body.dataset.runtimeContract = "showcase-controls";
  const cards = [...document.querySelectorAll(".theme-card")];
  const stages = [...document.querySelectorAll("[data-motion-card]")];
  const filter = document.querySelector("[data-filter]");
  const status = document.querySelector("[data-filter-status]");
  const guideLive = document.querySelector("[data-guide-live]");
  const guideDetail = document.querySelector("[data-guide-detail]");
  const guideStatus = document.querySelector("[data-guide-status]");
  const guideSteps = [...document.querySelectorAll("[data-guide-step]")];
  const guideCopy = {
    source: {
      live: "01 / SOURCE · start here",
      detail: "Confirm the supplied image and the parts that must remain unchanged.",
      status: "Current session: identity is locked to the supplied source; no route or file change has been made."
    },
    theme: {
      live: "02 / THEME · choose a route",
      detail: "Select the design intention; the route must change the foreground reveal, not only the background.",
      status: "Theme selected: the route changes the identity-bearing construction path while the canonical source handoff remains fixed."
    },
    tune: {
      live: "03 / TUNE · make it measurable",
      detail: "Set background, duration, speed, direction, particles, and motion policy in words the exporter can reproduce.",
      status: "Preview only: controls changed the local shell and request summary; no media file has been written."
    },
    bake: {
      live: "04 / BAKE · run the exporter",
      detail: "Copy the command, run it from the project root, then inspect the generated GIF, checkpoints, manifest, and PDF.",
      status: "Command prepared: the browser copied or displayed an export command; it did not execute the shell or claim a new bake."
    },
    verify: {
      live: "05 / VERIFY · inspect evidence",
      detail: "Confirm source identity, final-frame equality, runtime behavior, accessibility, fingerprints, and human review.",
      status: "Verification remains an evidence step: browser interaction alone cannot promote a preview or baked file to verified."
    }
  };
  let guideState = "source";
  function setGuide(next) {
    if (!guideCopy[next]) return;
    guideState = next;
    const copy = guideCopy[next];
    const currentIndex = guideSteps.findIndex((step) => step.dataset.guideStep === next);
    if (guideLive) guideLive.textContent = copy.live;
    if (guideDetail) guideDetail.textContent = copy.detail;
    if (guideStatus) guideStatus.textContent = copy.status;
    guideSteps.forEach((step, index) => {
      step.classList.toggle("is-current", index === currentIndex);
      step.classList.toggle("is-complete", currentIndex > index);
      const state = step.querySelector("[data-guide-step-status]");
      if (state) state.textContent = index < currentIndex ? "complete" : index === currentIndex ? "current" : "next";
    });
  }
  const motionPreference = window.matchMedia?.("(prefers-reduced-motion: reduce)");
  const systemPrefersReduced = () => Boolean(motionPreference?.matches);
  const CANONICAL_HANDOFF_PROGRESS = 1;
  const STAGE_ORDER = ["blank", "spark", "arc", "bar", "monogram", "wordmark", "canonical"];
  const DEFAULT_STAGE_PROGRESS = Object.freeze({ blank: 0, spark: .16, arc: .33, bar: .47, monogram: .64, wordmark: .985, canonical: 1 });
  const presets = {
    grid: [-28, 16, -6, .78], quiet: [0, 10, 0, .9], scan: [-26, 0, 0, .8],
    field: [-10, 22, -8, .72], ring: [0, 0, -22, .78], shield: [0, 24, 0, .74],
    burst: [0, 0, -18, .76], track: [-42, 0, 0, .8], speed: [-48, 6, -10, .7],
    curtain: [0, 0, 0, .84], wave: [16, 22, 8, .76], orbit: [0, -16, 16, .78],
    plain: [0, 12, 0, .86]
  };
  const players = [];
  let motion = systemPrefersReduced() ? "reduced" : "running";
  let motionOverride = null;
  const tuning = { duration: 1.8, speed: 1, direction: "radial", background: "theme", color: "#0B0D12", particles: true, surface: "brand identity" };
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const ease = (value, effect) => {
    const p = clamp(value, 0, 1);
    if (effect === "speed" || effect === "burst") return 1 - Math.pow(1 - p, 3);
    if (effect === "quiet" || effect === "curtain") return p * p * (3 - 2 * p);
    if (effect === "wave" || effect === "orbit") return p < .78 ? p / .78 : 1 - Math.pow((1 - p) / .22, 2) * .035;
    return 1 - Math.pow(1 - p, 2.4);
  };
  function readStageProgress(stage) {
    let parsed = {};
    try { parsed = JSON.parse(stage.dataset.stageProgress || "{}"); } catch (error) { parsed = {}; }
    const result = { blank: 0 };
    let previous = 0;
    STAGE_ORDER.slice(1, -1).forEach((name) => {
      const candidate = Number(parsed[name]);
      const fallback = DEFAULT_STAGE_PROGRESS[name];
      const value = Number.isFinite(candidate) ? clamp(candidate, previous, 1) : fallback;
      result[name] = Math.max(previous, value);
      previous = result[name];
    });
    result.canonical = 1;
    return result;
  }
  function phaseFor(progress, stageProgress = DEFAULT_STAGE_PROGRESS) {
    const p = clamp(progress, 0, 1);
    if (p <= stageProgress.blank) return "blank";
    for (const name of STAGE_ORDER.slice(1, -1)) {
      if (p <= stageProgress[name]) return name;
    }
    return p >= stageProgress.canonical ? "canonical" : "wordmark";
  }
  function beatFor(player, progress) {
    const beats = player.beats || [];
    if (!beats.length) return "";
    if (progress < .34) return beats[0] || "entry";
    if (progress < .68) return beats[1] || beats[0] || "build";
    return beats[2] || beats[beats.length - 1] || "settle";
  }
  function render(player, progress) {
    const p = clamp(progress, 0, 1);
    const phase = phaseFor(p, player.stageProgress);
    player.stage.style.setProperty("--motion-progress", p.toFixed(4));
    player.stage.dataset.state = phase;
    if (player.phase) player.phase.textContent = phase;
    if (player.beat) player.beat.textContent = beatFor(player, p);
    player.stage.querySelectorAll("[data-growth-stage]").forEach((node) => {
      node.classList.toggle("is-active", node.dataset.growthStage === phase);
    });
    if (player.progress) player.progress.style.width = `${p * 100}%`;
    if (player.time) player.time.textContent = `${(p * player.duration / 1000).toFixed(1)}s`;
    if (player.seek && document.activeElement !== player.seek) player.seek.value = p.toFixed(3);
  }
  function showReadyGif(player) {
    if (!player.gif) return;
    player.gif.hidden = false;
    player.stage.dataset.playback = player.playing ? "playing" : "ready";
    if (player.canonical) player.canonical.hidden = true;
    if (player.poster) player.poster.hidden = true;
    if (player.loading) player.loading.hidden = true;
  }
  function showGif(player, restart = false) {
    if (!player.gif) return Promise.resolve(false);
    const currentSource = player.gif.dataset.mediaSrc || "";
    if (!restart && player.gif.dataset.loaded === "true" && currentSource === player.src) {
      showReadyGif(player);
      return Promise.resolve(true);
    }
    const token = (player.loadToken || 0) + 1;
    player.loadToken = token;
    const next = player.gif.cloneNode(false);
    next.hidden = true;
    next.loading = "eager";
    next.removeAttribute("loading");
    next.dataset.loaded = "loading";
    next.dataset.mediaSrc = player.src;
    player.gif.replaceWith(next);
    player.gif = next;
    showLoading(player);
    return new Promise((resolve) => {
      let settled = false;
      const finish = (loaded) => {
        if (settled) return;
        settled = true;
        if (token !== player.loadToken) { resolve(false); return; }
        if (!loaded) { showCanonical(player); resolve(false); return; }
        player.gif.dataset.loaded = "true";
        if (player.playing) showReadyGif(player);
        else if (player.paused) freezeCurrentFrame(player);
        resolve(true);
      };
      next.addEventListener("load", () => finish(true), { once: true });
      next.addEventListener("error", () => finish(false), { once: true });
      next.src = player.src;
    });
  }
  function showPoster(player, source) {
    if (!player.gif) return;
    player.gif.hidden = true;
    player.stage.dataset.playback = source ? "paused" : "poster";
    if (player.canonical) player.canonical.hidden = true;
    if (player.loading) player.loading.hidden = true;
    if (player.poster) {
      player.poster.src = source || player.posterSrc;
      player.poster.alt = source
        ? `${player.name} paused frame of the logo growth animation`
        : `${player.name} static canonical reduced-motion fallback`;
      player.poster.hidden = false;
    }
  }
  function showCheckpoint(player, progress) {
    const p = clamp(progress, 0, 1);
    const stage = phaseFor(p, player.stageProgress);
    if (stage === "canonical") { showCanonical(player); return; }
    const checkpoint = player.stageFiles?.[stage] || player.posterSrc;
    player.current = p * player.duration;
    render(player, p);
    if (player.gif) player.gif.hidden = true;
    player.stage.dataset.playback = "checkpoint";
    if (player.canonical) player.canonical.hidden = true;
    if (player.loading) player.loading.hidden = true;
    if (player.poster) {
      player.poster.src = checkpoint;
      player.poster.alt = `${player.name} baked ${stage} checkpoint of the logo growth animation`;
      player.poster.hidden = false;
    }
  }
  function seekPlayer(player, progress) {
    stop(player);
    player.paused = true;
    showCheckpoint(player, progress);
  }
  function showCanonical(player) {
    if (!player.gif) return;
    player.current = player.duration;
    render(player, 1);
    player.gif.hidden = true;
    player.stage.dataset.playback = "canonical";
    if (player.poster) player.poster.hidden = true;
    if (player.loading) player.loading.hidden = true;
    if (player.canonical) {
      player.canonical.src = player.posterSrc;
      player.canonical.hidden = false;
    }
  }
  function showLoading(player) {
    if (player.gif) player.gif.hidden = true;
    player.stage.dataset.playback = "loading";
    if (player.canonical) player.canonical.hidden = true;
    if (player.poster) player.poster.hidden = true;
    if (player.loading) player.loading.hidden = false;
  }
  function freezeCurrentFrame(player) {
    if (!player.gif || player.gif.dataset.loaded !== "true" || !player.gif.complete || !player.gif.naturalWidth) { showCanonical(player); return; }
    const canvas = document.createElement("canvas");
    canvas.width = player.gif.naturalWidth;
    canvas.height = player.gif.naturalHeight;
    try {
      canvas.getContext("2d").drawImage(player.gif, 0, 0);
      showPoster(player, canvas.toDataURL("image/png"));
    } catch (error) {
      showCanonical(player);
    }
  }
  function stop(player) {
    player.playing = false;
    player.loadToken = (player.loadToken || 0) + 1;
    if (player.frame) cancelAnimationFrame(player.frame);
    player.frame = 0;
  }
  function tick(player, timestamp) {
    if (!player.playing || motion === "paused" || motion === "reduced") return;
    if (player.last === null) player.last = timestamp;
    player.current += (timestamp - player.last) * tuning.speed;
    player.last = timestamp;
    const progress = clamp(player.current / player.duration, 0, 1);
    render(player, progress);
    // Hold a separate canonical overlay so the native GIF cannot loop back to
    // its blank frame while the storyboard is still reporting the final state.
    // showCanonical() clamps the visible state to the exact final frame. Call
    // it only once at the handoff so the separate final hold can advance.
    if (player.current >= player.duration && player.stage.dataset.playback !== "canonical") showCanonical(player);
    if (player.current >= player.duration + player.finalHoldMs) {
      player.current = 0;
      render(player, 0);
      player.last = null;
      player.frame = 0;
      void showGif(player, true).then((loaded) => {
        if (loaded && player.playing && motion === "running" && !player.frame) {
          player.frame = requestAnimationFrame((next) => tick(player, next));
        }
      });
      return;
    }
    player.frame = requestAnimationFrame((next) => tick(player, next));
  }
  async function play(player, forceRestart = false) {
    if (motion === "reduced") { stop(player); player.current = player.duration; render(player, 1); showCanonical(player); return; }
    // A portable GIF cannot seek. Resume by restarting it so the timer and pixels agree.
    const restart = forceRestart || player.current > 0 || player.paused || player.current >= player.duration;
    if (restart) { player.current = 0; render(player, 0); }
    player.paused = false;
    player.playing = true;
    const loaded = await showGif(player, restart);
    if (!loaded || !player.playing || motion !== "running") return;
    player.last = null;
    if (!player.frame) player.frame = requestAnimationFrame((next) => tick(player, next));
  }
  function pause(player) {
    stop(player);
    player.paused = true;
    player.stage.dataset.playback = "paused";
    if (player.current >= player.duration) showCanonical(player); else freezeCurrentFrame(player);
  }
  function replay(player) { stop(player); player.current = 0; player.paused = false; render(player, 0); play(player, true); }
  stages.forEach((stage) => {
     let stageFiles = {};
     try { stageFiles = JSON.parse(stage.dataset.stageFiles || "{}"); } catch (error) { stageFiles = {}; }
     const player = { stage, stageProgress: readStageProgress(stage), id: stage.dataset.themeId || "", autoPlay: stage.dataset.themeId === "ai-field", name: stage.closest(".theme-card")?.querySelector("h2")?.textContent.trim() || "Logo", effect: stage.dataset.effect || "plain", beats: (stage.dataset.beats || "").split(" / ").filter(Boolean), stageFiles, baseDuration: Number(stage.dataset.durationMs || 1800), duration: Number(stage.dataset.durationMs || 1800), finalHoldMs: 720, current: 0, last: null, playing: false, paused: false, frame: 0, loadToken: 0, src: stage.dataset.animationSrc || "", posterSrc: stage.dataset.posterSrc || "", gif: stage.querySelector(".growth-gif"), canonical: stage.querySelector(".motion-canonical"), poster: stage.querySelector(".motion-freeze"), loading: stage.querySelector(".motion-loading"), phase: stage.querySelector("[data-motion-phase]"), beat: stage.querySelector("[data-motion-beat]"), progress: stage.closest(".motion-output")?.querySelector("[data-motion-progress]"), time: stage.closest(".motion-output")?.querySelector("[data-motion-time]"), seek: stage.closest(".motion-output")?.querySelector("[data-motion-seek]") };
    player.playButton = stage.closest(".motion-output")?.querySelector('[data-card-action="play"]');
    player.pauseButton = stage.closest(".motion-output")?.querySelector('[data-card-action="pause"]');
    player.replayButton = stage.closest(".motion-output")?.querySelector('[data-card-action="replay"]');
    player.playButton?.addEventListener("click", () => { setMotion("running"); play(player); });
    player.pauseButton?.addEventListener("click", () => pause(player));
    player.replayButton?.addEventListener("click", () => { setMotion(motion === "reduced" ? "reduced" : "running"); replay(player); });
    player.seek?.addEventListener("input", () => seekPlayer(player, Number(player.seek.value)));
    player.seek?.addEventListener("change", () => seekPlayer(player, Number(player.seek.value)));
    players.push(player);
     render(player, systemPrefersReduced() || !player.autoPlay ? 1 : 0);
     if (systemPrefersReduced()) showCanonical(player); else if (player.autoPlay) play(player); else showCanonical(player);
  });
  function setMotion(next, forceReducedOverride = null, syncPlayers = false) {
    if (forceReducedOverride !== null) motionOverride = forceReducedOverride;
    const previous = motion;
     if (next === "running" && (systemPrefersReduced() || motionOverride === true) && motionOverride !== false) next = "reduced";
    motion = next;
    body.dataset.motion = next;
    document.querySelectorAll("[data-motion-label]").forEach((node) => {
      node.textContent = next === "reduced" ? "REDUCED" : next.toUpperCase();
    });
    if (routeAnimation && routeAnimationPoster) {
      routeAnimation.hidden = next === "reduced";
      routeAnimationPoster.hidden = next !== "reduced";
    }
    if (routePreviewState) routePreviewState.textContent = next === "reduced"
      ? "Static poster · reduced-motion fallback · checked-in asset"
      : "GIF evidence · checked-in route asset · browser tuning is preview-only until the generator is rerun.";
    if (!syncPlayers) return;
    if (next === "paused") players.forEach(pause);
    if (next === "reduced") players.forEach(play);
    if (next === "running" && previous !== "running") players.forEach(play);
  }
  function replayAll() {
    setMotion(motion === "reduced" ? "reduced" : "running");
    players.forEach(replay);
  }
  document.querySelector("[data-action=play]")?.addEventListener("click", () => { setMotion("running"); players.forEach(play); });
  document.querySelector("[data-action=pause]")?.addEventListener("click", () => { setMotion("paused"); players.forEach(pause); });
  document.querySelector("[data-action=replay]")?.addEventListener("click", replayAll);
  filter?.addEventListener("input", () => {
    const query = filter.value.trim().toLowerCase();
    let visible = 0;
    cards.forEach((card) => {
      const terms = query.split(/\s+/).filter(Boolean);
      const searchable = card.dataset.search.toLowerCase().split(/[\s,;|/]+/).filter(Boolean);
      const match = !terms.length || terms.every((term) => searchable.includes(term));
      const player = players.find((candidate) => candidate.stage.closest(".theme-card") === card);
      card.hidden = !match;
      if (!match && player?.playing) { player.filteredPlaying = true; pause(player); }
      if (match && player?.filteredPlaying && motion === "running") { player.filteredPlaying = false; play(player); }
      if (match) visible += 1;
    });
    if (status) status.textContent = `${visible} of ${cards.length} routes shown`;
  });

  const prompt = document.querySelector("[data-motion-prompt]");
  const routeSelect = document.querySelector("[data-route-select]");
  const routeName = document.querySelector("[data-route-name]");
  const routeTrigger = document.querySelector("[data-route-trigger]");
  const routeTrajectory = document.querySelector("[data-route-trajectory]");
  const routeConstruction = document.querySelector("[data-route-construction]");
  const routeSpeed = document.querySelector("[data-route-speed]");
  const routeSequence = document.querySelector("[data-route-sequence]");
  const routeGif = document.querySelector("[data-route-gif]");
  const routeAnimation = document.querySelector("[data-route-animation]");
  const routeAnimationPoster = document.querySelector("[data-route-animation-poster]");
  const routePreviewState = document.querySelector("[data-preview-state]");
  const routeExportCommand = document.querySelector("[data-route-export-command]");
  const copyExportCommandButton = document.querySelector("[data-copy-export-command]");
  const requestSummary = document.querySelector("[data-config-summary]");
  const copyStatus = document.querySelector("[data-copy-status]");
   const syncPromptButton = document.querySelector("[data-sync-prompt]");
   const exportPlan = document.querySelector("[data-export-plan]");
   const exportApprovalState = document.querySelector("[data-export-approval-state]");
   const exportApproveButton = document.querySelector("[data-export-approve]");
   const exportCorrectButton = document.querySelector("[data-export-correct]");
   const exportDeclineButton = document.querySelector("[data-export-decline]");
   const routeExportNote = document.querySelector("[data-route-export-note]");
   let exportApproval = "pending";
   let promptDirty = false;
  const routeCards = new Map(cards.map((card) => {
    const stage = card.querySelector("[data-motion-card]");
    return [card.dataset.theme, {
      id: card.dataset.theme,
      card,
      name: card.querySelector("h2")?.textContent.trim() || card.dataset.theme,
      trigger: card.querySelector(".trigger")?.textContent.trim() || "",
      intent: card.querySelector(".intent")?.textContent.trim() || "",
       trajectory: card.querySelector(".trajectory-note")?.textContent.replace(/^FOREGROUND TRAJECTORY\s*/i, "").trim() || "The supplied mark follows the selected route.",
       mode: stage?.dataset.foregroundMode || "source-derived",
       variant: stage?.dataset.foregroundVariant || "default",
       pathStrategy: stage?.dataset.pathStrategy || "source-derived draw-on path",
       speedProfile: stage?.dataset.speedProfile || "declared route timing",
       construction: stage?.dataset.foregroundMode ? `${stage.dataset.foregroundMode} / ${stage.dataset.foregroundVariant || "default"} / ${stage.dataset.pathStrategy || "source-derived draw-on path"}` : card.querySelector(".motion-route-banner")?.textContent.replace(/^THEME-SPECIFIC FOREGROUND ROUTE\s*/i, "").replace(/\s+/g, " ").trim() || "Source-derived draw-on path.",
       sequence: (stage?.dataset.growthDisplay || "blank / origin dot / circular arc / horizontal bar / P / monogram / Prysai wordmark / complete Logo").replace(/\s*\/\s*/g, " → "),
        gif: card.querySelector(".download-animation")?.getAttribute("href") || "",
        poster: stage?.dataset.posterSrc || card.querySelector(".motion-canonical")?.getAttribute("src") || "",
        beats: (stage?.dataset.beats || "").split(" / ").filter(Boolean)
    }];
  }));
  const promptPresets = {
     ai: { route: "ai-field", controls: { background: "solid", "background-color": "#0B0D12", duration: "1.6", speed: "1.25", direction: "radial", particles: false, "reduced-motion": "respect", format: "gif" }, text: "Animate this supplied logo for an AI technology company. Route it to ai-field. Preserve the supplied source geometry and grow only observed actors in this order: blank → origin dot → circular arc → horizontal bar → P / monogram → Prysai wordmark → complete Logo. Execute the source-pixel foreground route convergence / polar-counter / seeded signals converge into measured actors. Treat raster roles as candidates, use a solid #0B0D12 background, 1600ms, speed 1.25x, center outward, no particles, respect reduced motion, and export GIF." },
     education: { route: "system-spatial", controls: { background: "solid", "background-color": "#F4F1E8", duration: "2.4", speed: "0.75", direction: "left-to-right", particles: false, "reduced-motion": "respect", format: "gif" }, text: "Animate this supplied logo for an education product. Route it to system-spatial. Preserve the source geometry and place observed actors on a clear spatial grid: blank → origin dot → circular arc → horizontal bar → P / monogram → Prysai wordmark → complete Logo. Execute the source-pixel foreground route grid / scan-forward / measured actor-to-actor grid locks. Use a solid #F4F1E8 background, 2400ms, speed 0.75x, left to right entry, no particles, respect reduced motion, and export GIF." },
     premium: { route: "premium-quiet", controls: { background: "solid", "background-color": "#0B0D12", duration: "2.8", speed: "0.75", direction: "radial", particles: false, "reduced-motion": "respect", format: "gif" }, text: "Animate this supplied logo for a premium editorial brand. Route it to premium-quiet. Preserve the source geometry and execute the source-pixel foreground route contour / polar-clockwise / source contour trace followed by fill before the Prysai wordmark. Use a solid #0B0D12 background, 2800ms, speed 0.75x, center outward, no particles, respect reduced motion, and export GIF. Request HTML/SVG only if an accepted SVG source or approved raster reconstruction adapter is available."
    }
  };
  const recipes = {
    solid: { background: "solid", "background-color": "#F4F1E8", particles: false },
    quiet: { duration: "2.4", speed: "0.75" },
    clean: { particles: false },
    accessible: { "reduced-motion": "reduced" }
  };
  function setCopyStatus(message) { if (copyStatus) copyStatus.textContent = message; }
  function setExportApproval(next, message = "") {
    exportApproval = next;
    if (exportApprovalState) {
      exportApprovalState.textContent = next === "approved"
        ? "approved · this exact route and tuning may now be exported"
        : next === "declined"
          ? "declined · export is blocked until the plan is reviewed again"
          : "pending · review the source, candidate actor map, tuning, output, and open gaps";
      exportApprovalState.dataset.state = next;
    }
    if (exportApproveButton) exportApproveButton.disabled = next === "approved";
    if (message) setCopyStatus(message);
  }
  function invalidateExportApproval() {
    if (exportApproval === "approved") setExportApproval("pending", "The export plan changed. Review and approve the updated configuration before copying a command.");
  }
  function readTuningFromControls() {
    tuning.background = document.querySelector('[data-param="background"]')?.value || tuning.background;
    tuning.color = (document.querySelector('[data-param="background-color"]')?.value || tuning.color).toUpperCase();
    tuning.duration = Number(document.querySelector('[data-param="duration"]')?.value) || tuning.duration;
    tuning.speed = Number(document.querySelector('[data-param="speed"]')?.value) || tuning.speed;
    tuning.direction = document.querySelector('[data-param="direction"]')?.value || tuning.direction;
    tuning.particles = Boolean(document.querySelector('[data-param="particles"]')?.checked);
  }
  function applyPresetControls(preset) {
    Object.entries(preset.controls || {}).forEach(([param, value]) => {
      const control = document.querySelector(`[data-param="${param}"]`);
      if (!control) return;
      if (control.type === "checkbox") control.checked = Boolean(value);
      else control.value = String(value);
    });
    readTuningFromControls();
    const motionControl = document.querySelector('[data-param="reduced-motion"]')?.value || "respect";
    motionOverride = motionControl === "reduced" ? true : motionControl === "full" ? false : null;
    setMotion(motionControl === "reduced" || (motionControl === "respect" && systemPrefersReduced()) ? "reduced" : "running");
    applyPreviewTuning();
  }
  async function copyPrompt() {
    const value = prompt?.value.trim();
    if (!value) { setCopyStatus("Write a prompt first."); return; }
    let copied = false;
    try { if (navigator.clipboard?.writeText) { await navigator.clipboard.writeText(value); copied = true; } } catch (error) { copied = false; }
    if (!copied) {
      const fallback = document.createElement("textarea"); fallback.value = value; fallback.setAttribute("readonly", ""); fallback.style.position = "fixed"; fallback.style.opacity = "0"; document.body.appendChild(fallback); fallback.select();
      try { copied = document.execCommand("copy"); } catch (error) { copied = false; }
      fallback.remove();
    }
    setCopyStatus(copied ? "Prompt copied. Paste it into the skill request." : "Select the prompt text and copy it manually.");
  }
  function selectedLabel(name) { return document.querySelector(`[data-param="${name}"]`)?.selectedOptions?.[0]?.textContent.trim() || ""; }
  function selectedFormat() {
    const value = document.querySelector('[data-param="format"]')?.value || "gif";
    return value === "html-svg" ? "HTML/SVG" : value === "pdf" ? "PDF atlas" : "GIF";
  }
  function routeCommand() {
    const route = routeCards.get(routeSelect?.value) || routeCards.values().next().value;
    const format = document.querySelector('[data-param="format"]')?.value || "gif";
    const parts = ["python showcase/generate_showcase.py"];
    if (format === "gif") parts.push(`--theme ${route?.id || "ai-field"}`);
    if (tuning.background === "solid") parts.push(`--background '${tuning.color}'`);
    if (tuning.duration) parts.push(`--duration-ms ${Math.round(tuning.duration * 1000)}`);
    if (tuning.speed !== 1) parts.push(`--speed ${tuning.speed}`);
    if (!tuning.particles) parts.push("--no-particles");
    if (format === "pdf") return `${parts.join(" ")}  # writes showcase/output/pdf/motiflux-theme-atlas.pdf`;
    if (format === "html-svg") return "NOT_RUN: HTML/SVG export requires an accepted SVG source or approved raster reconstruction adapter.";
    return parts.join(" ");
  }
  async function copyExportCommand() {
    if (exportApproval !== "approved") {
      setGuide("bake");
      setCopyStatus("Approve the export plan first. The browser will not copy an unreviewed route or candidate actor mapping.");
      return;
    }
    const value = routeCommand();
    if (value.startsWith("NOT_RUN:")) {
      setGuide("bake");
      setCopyStatus(value);
      return;
    }
    let copied = false;
    try { if (navigator.clipboard?.writeText) { await navigator.clipboard.writeText(value); copied = true; } } catch (error) { copied = false; }
    setGuide("bake");
    setCopyStatus(copied ? "Export command copied. Run it from the project root; the browser does not execute it." : `Export command: ${value}`);
  }
  function composePrompt() {
    const route = routeCards.get(routeSelect?.value) || routeCards.values().next().value;
    const background = tuning.background === "solid" ? `solid ${tuning.color}` : tuning.background === "dark" ? "plain dark" : tuning.background === "transparent" ? "transparent stage shell" : "the theme background";
    const surface = selectedLabel("surface") || tuning.surface || "brand identity";
    const direction = (selectedLabel("direction") || "center outward").toLowerCase();
    const particles = tuning.particles ? "allow secondary particles" : "no particles";
    const motionControl = document.querySelector('[data-param="reduced-motion"]')?.value || "respect";
    const motionText = motionControl === "reduced" ? "use a static canonical reduced-motion fallback" : motionControl === "full" ? "allow the full motion preview" : "respect reduced motion";
    const stages = (route?.sequence || "blank -> origin dot -> circular arc -> horizontal bar -> P / monogram -> Prysai wordmark -> complete Logo").replace(/→/g, "->");
    const pathStrategy = route?.pathStrategy || "the declared source-derived path";
    const speedProfile = route?.speedProfile || "the declared route timing";
    return `Animate this supplied logo for the selected brand context. Surface: ${surface}. Route it to ${route?.id || "the selected theme"}. Preserve the source geometry and grow only observed actors in this order: ${stages}. Execute the source-pixel foreground route ${route?.construction || "with the declared theme variant"}. Path strategy: ${pathStrategy}. Speed profile: ${speedProfile}. This variant must change the identity-bearing reveal, not only the background, particles, or whole-logo transform. Treat raster role labels as candidates and keep a static canonical fallback. Use ${background}, ${Math.round(tuning.duration * 1000)}ms, speed ${tuning.speed}x, ${direction} direction, ${particles}, ${motionText}, and export ${selectedFormat()}. Lifecycle: browser changes are preview-only; a named generator creates baked files; call the result verified only after source identity, frame, runtime, accessibility, and human-review checks pass. Evidence required: report actual output paths plus candidate, needs-review, not_run, and unresolved items.`;
  }
  function syncPrompt(message = "Request synced from the selected route and controls.") {
    if (!prompt) return;
    prompt.value = composePrompt();
    promptDirty = false;
    setCopyStatus(message);
  }
  function updateRequestSummary() {
    const route = routeCards.get(routeSelect?.value) || routeCards.values().next().value;
    const duration = `${tuning.duration.toFixed(1)} s`;
    const speed = `${tuning.speed}x`;
    const direction = selectedLabel("direction") || "Center outward";
    const background = tuning.background === "solid" ? `solid ${tuning.color}` : tuning.background === "dark" ? "plain dark" : tuning.background === "transparent" ? "transparent shell" : "theme background";
    const particles = tuning.particles ? "particles on" : "particles off";
    const motionControl = document.querySelector('[data-param="reduced-motion"]')?.value || "respect";
    const motionText = motionControl === "reduced" ? "reduced motion" : motionControl === "full" ? "full motion preview" : "respect system motion";
    const format = document.querySelector('[data-param="format"]')?.value === "html-svg" ? "HTML/SVG" : document.querySelector('[data-param="format"]')?.value === "pdf" ? "PDF atlas" : "GIF";
    const surface = selectedLabel("surface") || tuning.surface || "Brand identity";
    if (requestSummary) requestSummary.textContent = `${route?.name || "Selected route"} · ${surface} · ${background} · ${duration} · ${speed} · ${direction.toLowerCase()} · ${particles} · ${motionText} · ${format}`;
    const durationOutput = document.querySelector('[data-value-for="duration"]'); if (durationOutput) durationOutput.textContent = duration;
    const colorOutput = document.querySelector("[data-background-swatch]"); if (colorOutput) colorOutput.textContent = tuning.color;
    if (prompt && !promptDirty) prompt.value = composePrompt();
    if (routeExportCommand) routeExportCommand.textContent = routeCommand();
    if (routeExportNote) routeExportNote.textContent = selectedFormat() === "HTML/SVG"
      ? "not_run · requires accepted SVG or an approved raster reconstruction adapter"
      : selectedFormat() === "PDF atlas"
        ? "baked target · regenerates the seven-stage atlas and repository showcase outputs"
        : "baked target · writes the selected route export manifest and GIF";
    if (exportPlan) exportPlan.textContent = `source: supplied Prysai JPG · route: ${route?.name || "selected"} · actor map: candidate / needs-review · tuning: ${surface}, ${background}, ${duration}, ${speed}, ${direction.toLowerCase()}, ${particles} · output: ${selectedFormat()} · gaps: raster role acceptance and browser/accessibility proof remain open`;
  }
  function applyPreviewTuning() {
    body.dataset.previewBackground = tuning.background;
    body.dataset.particles = tuning.particles ? "on" : "off";
    body.style.setProperty("--preview-solid-bg", tuning.color);
    const entry = tuning.direction === "left-to-right" ? "-8%" : tuning.direction === "right-to-left" ? "8%" : "0%";
    stages.forEach((stage) => { stage.dataset.direction = tuning.direction; stage.style.setProperty("--preview-entry-x", entry); });
    players.forEach((player) => {
      const progress = player.duration ? player.current / player.duration : 0;
      player.duration = player.baseDuration * (tuning.duration / 1.8);
      const isStaticCanonical = player.stage.dataset.playback === "canonical" && !player.playing;
      player.current = isStaticCanonical ? player.duration : clamp(progress, 0, 1) * player.duration;
      if (isStaticCanonical) showCanonical(player); else render(player, clamp(progress, 0, 1));
    });
    updateRequestSummary();
  }
  function applyRecipe(name) {
    const recipe = recipes[name];
    if (!recipe) return;
    Object.entries(recipe).forEach(([param, value]) => {
      const control = document.querySelector(`[data-param="${param}"]`);
      if (!control) return;
      if (control.type === "checkbox") control.checked = Boolean(value);
      else control.value = String(value);
    });
    tuning.background = document.querySelector('[data-param="background"]')?.value || tuning.background;
    tuning.color = (document.querySelector('[data-param="background-color"]')?.value || tuning.color).toUpperCase();
    tuning.duration = Number(document.querySelector('[data-param="duration"]')?.value) || tuning.duration;
    tuning.speed = Number(document.querySelector('[data-param="speed"]')?.value) || tuning.speed;
     tuning.particles = Boolean(document.querySelector('[data-param="particles"]')?.checked);
     tuning.surface = document.querySelector('[data-param="surface"]')?.value || tuning.surface;
     invalidateExportApproval();
    const motionControl = document.querySelector('[data-param="reduced-motion"]')?.value || "respect";
    motionOverride = motionControl === "reduced" ? true : motionControl === "full" ? false : null;
    if (motionControl === "reduced") {
      setMotion("reduced");
      players.forEach(play);
    }
    setGuide("tune");
    applyPreviewTuning();
    setCopyStatus(`${name} recipe applied to the local preview. Sync controls to copy it into the request.`);
  }
  function updateRoute(value, focusCard = false) {
    const route = routeCards.get(value) || routeCards.values().next().value;
    if (!route) return;
    if (routeSelect && routeSelect.value !== value) routeSelect.value = value;
    if (routeName) routeName.textContent = route.name;
    if (routeTrigger) routeTrigger.textContent = route.trigger;
    if (routeTrajectory) routeTrajectory.textContent = route.trajectory;
    if (routeConstruction) routeConstruction.textContent = route.construction;
    if (routeSpeed) routeSpeed.textContent = route.speedProfile;
    if (routeSequence) routeSequence.textContent = route.sequence;
    if (routeGif) { routeGif.href = route.gif; routeGif.textContent = `Open selected ${route.name} GIF`; }
    if (routeAnimation) {
      routeAnimation.src = route.gif;
      routeAnimation.alt = `${route.name} selected route preview: source logo growth animation`;
    }
    if (routeAnimationPoster) {
      const poster = route.poster || route.gif.replace(/\.gif$/i, "-poster.png");
      routeAnimationPoster.src = poster;
      routeAnimationPoster.alt = `${route.name} static canonical fallback for reduced motion`;
      routeAnimationPoster.hidden = motion !== "reduced";
    }
    if (routePreviewState) routePreviewState.textContent = motion === "reduced" ? "Static poster · reduced-motion fallback · checked-in asset" : "GIF evidence · checked-in route asset · browser tuning is preview-only until the generator is rerun.";
    routeCards.forEach((candidate) => candidate.card.classList.toggle("route-selected", candidate === route));
     if (focusCard) route.card.scrollIntoView({ behavior: systemPrefersReduced() ? "auto" : "smooth", block: "center" });
    updateRequestSummary();
  }
  document.querySelectorAll("[data-prompt-preset]").forEach((button) => button.addEventListener("click", () => {
    const preset = promptPresets[button.dataset.promptPreset];
    if (!preset || !prompt) return;
     promptDirty = true; invalidateExportApproval(); updateRoute(preset.route); setGuide("theme"); applyPresetControls(preset); promptDirty = false; prompt.value = composePrompt(); setCopyStatus(`${button.textContent.trim()} loaded. Preview controls now match this request. Review the export plan before copying a command.`); prompt.focus();
  }));
  document.querySelectorAll("[data-recipe]").forEach((button) => button.addEventListener("click", () => applyRecipe(button.dataset.recipe)));
  document.querySelector("[data-copy-prompt]")?.addEventListener("click", copyPrompt);
  copyExportCommandButton?.addEventListener("click", copyExportCommand);
  syncPromptButton?.addEventListener("click", () => syncPrompt());
  prompt?.addEventListener("input", () => { promptDirty = true; setCopyStatus("Prompt edited. The preview stays on the selected route; sync controls only when you want to replace it."); });
  routeSelect?.addEventListener("change", () => {
    invalidateExportApproval();
    updateRoute(routeSelect.value, true);
    setGuide("theme");
    setCopyStatus(promptDirty ? "Route preview changed. Your edited prompt is unchanged; sync controls only if you want to replace it." : "Route preview changed. The request text follows the selected route until you edit it.");
  });
  document.querySelectorAll("[data-param]").forEach((control) => {
    const update = () => {
      const name = control.dataset.param;
      if (name === "duration") tuning.duration = Number(control.value) || 1.8;
      if (name === "speed") tuning.speed = Number(control.value) || 1;
      if (name === "direction") tuning.direction = control.value;
      if (name === "background") tuning.background = control.value;
       if (name === "background-color") tuning.color = control.value.toUpperCase();
       if (name === "surface") tuning.surface = control.value;
       if (name === "particles") tuning.particles = control.checked;
       invalidateExportApproval();
       if (["duration", "speed", "direction", "background", "background-color", "particles", "reduced-motion", "format"].includes(name)) setGuide("tune");
       if (name === "reduced-motion") {
        const nextMotion = control.value === "reduced" || (control.value === "respect" && systemPrefersReduced()) ? "reduced" : "running";
        motionOverride = control.value === "reduced" ? true : control.value === "full" ? false : null;
        setMotion(nextMotion);
        players.forEach(play);
      }
      applyPreviewTuning();
    };
    control.addEventListener("input", update); control.addEventListener("change", update);
  });
   exportApproveButton?.addEventListener("click", () => setExportApproval("approved", "Export plan approved. The command is now eligible to copy; the browser still does not execute it."));
   exportCorrectButton?.addEventListener("click", () => setExportApproval("pending", "Actor mapping correction requested. Keep raster roles as candidate hypotheses until source or human review accepts them."));
   exportDeclineButton?.addEventListener("click", () => setExportApproval("declined", "Export declined. No command was copied."));
   updateRoute(routeSelect?.value || "ai-field");
  applyPreviewTuning();
   setExportApproval("pending");
   setGuide(guideState);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      players.forEach((player) => { player.wasPlaying = player.playing; if (player.playing) pause(player); });
      return;
    }
    if (motion === "running") players.forEach((player) => { if (player.wasPlaying) { player.wasPlaying = false; play(player); } });
  });
  setMotion(motion);
  motionPreference?.addEventListener?.("change", (event) => {
    if (motionOverride !== null) return;
    setMotion(event.matches ? "reduced" : "running", null, true);
  });
  function seek(milliseconds) {
    const target = Number.isFinite(Number(milliseconds)) ? Math.max(0, Number(milliseconds)) : 0;
    players.forEach((player) => {
      stop(player);
      player.current = clamp(target, 0, player.duration);
      player.paused = true;
      render(player, player.duration ? player.current / player.duration : 1);
      if (player.current >= player.duration) showCanonical(player); else showPoster(player);
    });
  }
  function finish() {
    players.forEach((player) => {
      stop(player);
      player.current = player.duration;
      player.paused = true;
      render(player, 1);
      showCanonical(player);
    });
    setMotion("paused");
  }
  function setTempo(value) {
    tuning.speed = clamp(Number(value) || 1, .25, 4);
    const control = document.querySelector('[data-param="speed"]');
    if (control) control.value = String([.75, 1, 1.25, 1.5].reduce((best, option) => Math.abs(option - tuning.speed) < Math.abs(best - tuning.speed) ? option : best, 1));
    updateRequestSummary();
  }
  const runtimeControl = { play: () => { setMotion("running", null, true); }, pause: () => { setMotion("paused", null, true); }, replay: replayAll, seek, finish, setTempo, setMotion: (next) => setMotion(next, null, true) };
  body.dataset.runtimeState = "ready";
  body.dataset.runtimeReady = "true";
  window.__motifluxReady = true;
  window.__motifluxControl = runtimeControl;
  window.__motifluxShowcaseReady = true;
  window.__motifluxShowcaseControl = runtimeControl;
})();
