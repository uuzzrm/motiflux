# Motiflux runtime contract

The web delivery adapter must be dependency-free unless the consuming project
explicitly approves dependencies. It may be replaced by a framework adapter,
but the observable controls and safety behavior remain stable.

## Required browser surface

Expose these globals after initialization:

```javascript
window.__motifluxReady === true
window.__motifluxControl.seek(milliseconds)
window.__motifluxControl.finish()
```

The control object should also provide `play`, `pause`, `replay`, and `setTempo`
when the surface supports playback. `finish()` must render the canonical mark,
not merely stop at an approximate frame.

The staged runtime uses the fixed foreground order
`seed -> trace -> assemble -> lockup -> canonical`. A request may describe
user-visible substeps such as point, arc, bar, monogram, and wordmark, but the
runtime maps them into this order; it does not expose arbitrary foreground
reordering or an independent canonical reading-hold field. Use duration, tempo,
and stage timing intent when the canonical result needs more reading time.

For the staged source-actor runtime, the generated root exposes
`data-growth-mode="staged-source-actors"`, each addressable source element
receives `data-motiflux-actor` and `data-motiflux-role`, and the root records
the actor-to-stage map. The runtime reveals the actor with a role-appropriate
operation (dot scale, arc stroke/clip reveal, bar scan, or wordmark scan),
applies the requested direction as a bounded entry offset, and then resets
every inline transform and mask at `finish()` so the canonical source paint
remains authoritative. If any planned actor cannot be bound to the source,
the runtime exposes `data-motiflux-runtime="static-canonical"` and keeps the
full mark visible instead of presenting a partial reveal as successful.

## Required behavior

- Pause when the document becomes hidden; do not accumulate time while hidden.
- Respect `prefers-reduced-motion` and show the static canonical mark.
- Provide visible, keyboard-accessible controls for nonessential motion.
- Avoid layout shift by reserving the stage geometry before playback.
- Avoid external requests and record any substituted runtime capability.
- Keep the canonical mark available while a plan is incomplete or interrupted.
- Make replay deterministic for a fixed plan and seed.
- Keep decorative secondary effects at zero opacity at the blank boundary; they
  must never be the only visible construction evidence.
- For raster input, treat structure as a bounded geometric observation only;
  retain `candidate` and `needs-review` until role review is complete.

## Runtime telemetry

Emit samples with:

```yaml
time_ms: 0
active_beat: orient
actor_states: {}
visible_bounds: {}
progress_values: {}
runtime_errors: []
```

Record risk intervals at crossings, occluder changes, actor handoffs, spring
extrema, viewport approaches, and loop seams. The audit adapter treats absent
telemetry as missing evidence.
