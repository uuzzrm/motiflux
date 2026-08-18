# ADR-001: Use artifact-first deep modules

## Status

Accepted

## Date

2026-08-18

## Context

Motiflux began as a strong design specification, but its analysis, comparison,
runtime, and evidence interfaces were only described. Adding more prose would
make the skill larger without making its behavior more reliable for an AI agent.
The project needs a stable seam between design reasoning and executable work.

## Decision

Use artifact-first deep modules. The main skill orchestrates a small number of
artifacts and CLI seams. Format-specific and validation complexity lives behind
those seams. JSON Schema defines the artifact shape; Markdown guides explain
decisions and algorithms; tools produce evidence rather than silently mutating
the source mark.

## Alternatives considered

### Put all algorithms in `SKILL.md`

Rejected because it increases context cost, duplicates implementation details,
and makes every change a prompt-level change.

### Build a large framework before defining contracts

Rejected because it would create shallow pass-through modules and make the
runtime contract difficult to test independently.

### Expose internal Python modules as the public interface

Rejected because future runtimes and agents may not use Python. The stable
interface is structured artifacts plus four command seams.

## Consequences

- Agents can load only the guide or schema needed for the current phase.
- The tools can be replaced without rewriting the orchestration contract.
- More files exist, but each has one role and a direct verification path.
- Browser and raster capabilities remain explicit instead of being implied by a
  green static check.

