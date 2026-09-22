# Local files and GitHub storage

## Repository contents

The following files are source files and belong in GitHub:

- `app.py`
- `dressing_assistant/`
- `tests/`
- `docs/`
- `README.md`
- `LICENSE`
- `THIRD_PARTY_NOTICES.md`
- `requirements.txt`
- `requirements-dev.txt`
- `pyproject.toml`
- `.streamlit/config.toml`
- `run.sh`

They are small, platform-independent, and required to run or update the project.

## Local-only private data

The following files are intentionally outside the Git repository:

```text
~/Documents/WardrobeAssistantData/
├── profile.md
├── wardrobe.yaml
├── config.yaml
├── backups/
└── codex-home/
```

The private data directory is not committed, uploaded, or included in the public repository.

## Generated files that do not belong in GitHub

- `.venv/` — Python environment, currently about 381 MB.
- `__pycache__/` — bytecode cache.
- `.pytest_cache/` — test cache.
- `outputs/` — local research artifacts.
- `work/` — scratch files.

These are ignored by Git. `.venv/` is platform-specific and can be deleted at any time. Recreate it with:

```bash
./run.sh
```

On first run, `run.sh` creates `.venv` and installs dependencies. After that, it starts Streamlit directly.

## What remains on the computer

Even if all source files are on GitHub, a local copy is required to run the application. The normal local footprint is:

- Repository source and Git history: very small.
- `.venv`: about 381 MB, optionally deletable.
- `WardrobeAssistantData`: private data, required and should not be committed.
- `codex-home`: local ChatGPT/Codex authentication and state for Dressing.

The `codex-home` directory contains login state and local Codex state. It is private and should remain local.
