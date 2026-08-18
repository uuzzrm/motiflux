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

## Required behavior

- Pause when the document becomes hidden; do not accumulate time while hidden.
- Respect `prefers-reduced-motion` and show the static canonical mark.
- Provide visible, keyboard-accessible controls for nonessential motion.
- Avoid layout shift by reserving the stage geometry before playback.
- Avoid external requests and record any substituted runtime capability.
- Keep the canonical mark available while a plan is incomplete or interrupted.
- Make replay deterministic for a fixed plan and seed.

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

