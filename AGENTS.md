# Repository Guidelines

## Project Structure & Module Organization

- `custom_components/hexagon_light/` — Home Assistant custom integration (domain: `hexagon_light`).
  - Core code: `__init__.py`, `light.py`, `device.py`, `config_flow.py`, `models.py`, `const.py`.
  - Metadata: `manifest.json`, `strings.json`, `translations/en.json`.
- `hacs.json` — HACS metadata for distribution.
- `README.md` — install/config notes for end users.

Avoid committing generated artifacts (e.g., `custom_components/hexagon_light/__pycache__/`).

## Build, Test, and Development Commands

This repo has no build pipeline. Useful local checks:

- `python -m compileall custom_components/hexagon_light` — quick syntax/bytecode compile check.
- `rg "<pattern>" -n` — fast search across the repo.
- `python -m json.tool custom_components/hexagon_light/manifest.json` — validate JSON formatting.

For runtime testing, install as a custom integration (via HACS or manual copy) and verify in Home Assistant:
- Settings → Devices & services → Add integration → `Hexagon Light`.

## Coding Style & Naming Conventions

- Python: follow Home Assistant conventions (4-space indentation; keep changes minimal and readable).
- JSON: 2-space indentation, double quotes, no trailing commas.
- Filenames: lowercase with underscores for Python modules (existing pattern), and keep translations under `translations/`.

## Testing Guidelines

No automated tests are currently included. Prefer adding small, focused tests only when introducing non-trivial logic; name files `tests/test_<feature>.py` if a test suite is introduced later.

## Commit & Pull Request Guidelines

There is no commit history yet. Use concise, imperative commit messages with an optional scope prefix:
- `integration: handle reconnect`
- `docs: clarify HACS install`

For PRs: include purpose, summary of changes, manual verification steps (in HA), and any risk/behavior notes.

## Security & Configuration Tips

- Never commit credentials, tokens, or host-specific configuration.
- Keep the repo clean of logs, caches, and local state (e.g., `__pycache__/`).
