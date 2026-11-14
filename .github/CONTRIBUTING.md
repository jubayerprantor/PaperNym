# Contributing to PaperNym

Thank you for your interest in improving PaperNym! Whether you are fixing a bug, adding a new scholarly metadata provider, improving identification accuracy, or refining the desktop UI, contributions are warmly welcomed.

---

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Development Setup

PaperNym requires **Python 3.10+**.

### 1. Clone and Create Virtual Environment

```bash
git clone https://github.com/jubayerprantor/PaperNym.git
cd PaperNym

python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Windows (cmd):
.venv\Scripts\activate.bat
```

### 2. Install Development Dependencies

```bash
pip install -e ".[gui,dev,build]"
```

### 3. Running Tests

Always test with an isolated temporary `PAPERNYM_HOME` and offscreen Qt platform:

**Linux / macOS:**
```bash
export PAPERNYM_HOME=$(mktemp -d)
export QT_QPA_PLATFORM=offscreen
pytest -q
```

**Windows (PowerShell):**
```powershell
$env:PAPERNYM_HOME = Join-Path $env:TEMP ('papernym-test-' + [guid]::NewGuid().ToString('N'))
$env:QT_QPA_PLATFORM = 'offscreen'
pytest -q
```

### 4. Code Formatting and Linting

PaperNym uses [Ruff](https://docs.astral.sh/ruff/) for formatting and linting:

```bash
# Check code style
ruff check src tests scripts

# Auto-format
ruff format src tests scripts
```

---

## Architectural Principles

1. **Zero GUI Imports in Core:**
   `src/papernym/core/` must never import `PySide6` or any Qt modules. The core logic must run cleanly in headless CLI and server environments.
2. **Safe File Operations:**
   PDF renaming must always be atomic or rollback-safe. Never overwrite existing files without explicit collision resolution.
3. **Privacy First:**
   Never log or transmit sensitive filesystem paths, user names, or document contents to third-party APIs. Only send extracted DOIs, arXiv IDs, or sanitized titles (when title search is permitted).
4. **Offline Resilience:**
   Network calls must time out gracefully and fall back to local parsing or `_CHECK` status rather than crashing or freezing the UI.

---

## Pull Request Guidelines

1. **Create a Feature Branch:**
   ```bash
   git checkout -b feature/my-improvement
   ```
2. **Add Tests:**
   Include tests under `tests/` for any new logic, edge cases, or bug fixes.
3. **Verify:**
   Ensure all tests pass and `ruff check` / `ruff format --check` succeed.
4. **Update Work Log:**
   Append a brief entry to `docs/PROGRESS.md` documenting your work.
5. **Submit PR:**
   Push your branch and open a pull request on GitHub describing the motivation and changes.
