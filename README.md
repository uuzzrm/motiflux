# Motiflux

Motiflux is an AI skill for turning a brand mark into an editable SVG scene and a
responsive, validated motion package. It treats logo animation as a constrained
design-and-verification problem: identity, topology, motion language, runtime
behavior, accessibility, and the canonical final state are all explicit.

Status: private development · Motiflux V1 · plugin release `1.0.0`

## What is included

- `.codex-plugin/plugin.json` — Codex plugin manifest and project metadata.
- `skills/motiflux/SKILL.md` — the core AI workflow and completion contract.
- `skills/motiflux/guides/motion-themes.md` — 13 theme routes with algorithm
  stacks, implementation controls, exclusions, and QA focus.
- `skills/motiflux/agents/openai.yaml` — UI metadata for skill discovery.
- `scripts/validate_project.py` — dependency-free repository structure and
  content checks.

The skill keeps its working context focused. Project-level documentation and
validation stay outside the skill directory so they do not become accidental
instructions during an AI task.

## Design model

```text
source mark
    ↓
constraint graph → scene graph → motion graph → runtime package
    ↓                 ↓              ↓               ↓
evidence ledger ← geometry QA ← temporal QA ← accessibility QA
```

Theme selection changes choreography and implementation parameters; it must not
change identity constraints of the source mark. Public design systems are used
only as principle references, never as claims about private vendor algorithms or
copied assets.

## Local validation

From the repository root:

```powershell
python scripts/validate_project.py
python H:\Codex\home\skills\.system\skill-creator\scripts\quick_validate.py skills\motiflux
python H:\Codex\home\skills\.system\plugin-creator\scripts\validate_plugin.py .
```

The two paths into `H:\Codex\home` are local development helpers. The first
command is the repository's portable check and is the one used by GitHub Actions.

## Development boundary

This repository is intentionally private while Motiflux V1 is being developed.
No public release, GitHub Pages deployment, or production runtime is implied by
the repository itself. A consuming project supplies the source mark and produces
the output package described by the skill contract.

