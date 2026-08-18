(() => {
  "use strict";
  const body = document.body;
  const cards = [...document.querySelectorAll(".theme-card")];
  const filter = document.querySelector("[data-filter]");
  const status = document.querySelector("[data-filter-status]");
  const prefersReduced = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  let motion = prefersReduced ? "reduced" : "running";
  function setMotion(next) {
    motion = next;
    body.dataset.motion = next;
    document.querySelectorAll("[data-motion-label]").forEach((node) => {
      node.textContent = next === "reduced" ? "REDUCED" : next.toUpperCase();
    });
  }
  function replay() {
    cards.forEach((card) => {
      card.querySelectorAll(".output-mark, .effect").forEach((node) => {
        node.style.animation = "none";
        void node.offsetWidth;
        node.style.animation = "";
      });
    });
    setMotion(prefersReduced ? "reduced" : "running");
  }
  document.querySelector("[data-action=play]")?.addEventListener("click", () => setMotion("running"));
  document.querySelector("[data-action=pause]")?.addEventListener("click", () => setMotion("paused"));
  document.querySelector("[data-action=replay]")?.addEventListener("click", replay);
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
  setMotion(motion);
  window.__motifluxShowcaseReady = true;
  window.__motifluxShowcaseControl = { play: () => setMotion("running"), pause: () => setMotion("paused"), replay, setMotion };
})();
