# mcp-lint

**Validate and security-check your `claude_desktop_config.json` — in CI or locally.**

```
mcp-lint claude_desktop_config.json
```

Exits **0** if everything looks good. Exits **1** if errors are found — making it CI-friendly out of the box.

---

## Why

MCP (Model Context Protocol) configs wire AI assistants like Claude to external tools — filesystems, GitHub, Slack, databases. A misconfigured server silently fails; an insecure one exposes credentials or grants overly broad access.

`mcp-lint` catches the most common problems:

| Category | Examples |
|---|---|
| **Validity** | Invalid JSON, missing `mcpServers` key, empty config |
| **Structure** | Missing `command`/`args`, wrong data types |
| **Runtime mismatch** | `command: "uvx"` used with an npm package, and vice-versa |
| **Unfilled placeholders** | `"your_token_here"`, `/path/to/your/repo` left in config |
| **Missing env vars** | GitHub server without `GITHUB_PERSONAL_ACCESS_TOKEN` |
| **Per-server gotchas** | Relative filesystem paths, postgres:// vs postgresql://, Brave quota |
| **Security** | Write-access servers, broad token scopes, AWS keys in config, 0.0.0.0 binds, wildcard CORS, DB credentials in args |
| **Token bloat** | Estimated context tax per server; warns when total > 20k/50k tokens |

Checks are ported from the [Hatchloop MCP Config Auditor](https://hatchloop.dev/tools/mcp-audit/) (battle-tested in the browser) and the `doctor.sh` script from the MCP Setup Pack.

---

## Install

```bash
pip install mcp-lint
```

Requires Python 3.9+. No dependencies beyond the standard library.

---

## Usage

```bash
# Basic — exits 0 if clean, 1 if errors
mcp-lint ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Treat warnings as failures (recommended for CI)
mcp-lint --strict config.json

# Security checks only
mcp-lint --security-only config.json

# Machine-readable JSON output
mcp-lint --json config.json

# Fail if estimated context tax exceeds 40k tokens
mcp-lint --max-tokens 40000 config.json

# Pipe from stdin
cat config.json | mcp-lint
```

### Flags

| Flag | Description |
|---|---|
| `--strict` | Warnings are treated as failures (exit 1) |
| `--json` | Output machine-readable JSON instead of human text |
| `--security-only` | Only run security checks |
| `--max-tokens N` | Fail if estimated token cost exceeds N |
| `--version` | Print version and exit |

---

## GitHub Actions CI Example

```yaml
name: MCP Config Lint

on:
  push:
    paths:
      - 'claude_desktop_config.json'
      - '.claude/**'
  pull_request:

jobs:
  mcp-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install mcp-lint
        run: pip install mcp-lint

      - name: Lint MCP config
        run: mcp-lint --strict claude_desktop_config.json

      # Optional: save JSON report as artifact
      - name: Save lint report
        if: always()
        run: mcp-lint --json claude_desktop_config.json > mcp-lint-report.json

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: mcp-lint-report
          path: mcp-lint-report.json
```

---

## JSON output schema

When run with `--json`, `mcp-lint` prints a single JSON object:

```json
{
  "source": "config.json",
  "exit_code": 1,
  "findings": [
    {
      "level": "error",
      "server": "github",
      "code": "server:missing-env-var",
      "message": "\"github\" is missing required env var GITHUB_PERSONAL_ACCESS_TOKEN.",
      "fix": "Add \"GITHUB_PERSONAL_ACCESS_TOKEN\": \"<your-real-value>\" to the env object for github."
    }
  ],
  "summary": {
    "errors": 1,
    "warnings": 2,
    "info": 5
  }
}
```

Finding levels:

| Level | Meaning |
|---|---|
| `error` | Always fails CI |
| `warning` | Fails CI with `--strict` |
| `info` | Never fails CI |
| `security:high` | Always fails CI |
| `security:medium` | Fails CI with `--strict` |
| `security:low` | Never fails CI |

---

## Token cost estimates

`mcp-lint` estimates how many context-window tokens each server's tool definitions consume. These are based on known server tool counts and observed schema sizes:

| Server | Estimate | Tier |
|---|---|---|
| github | ~50,000 | heavy |
| linear | ~32,000 | heavy |
| notion | ~28,000 | heavy |
| slack | ~22,000 | heavy |
| sentry | ~18,000 | heavy |
| supabase | ~16,000 | heavy |
| postgres | ~8,000 | medium |
| redis | ~5,000 | medium |
| filesystem | ~3,500 | medium |
| git | ~3,000 | light |
| fetch | ~1,500 | light |
| time | ~1,000 | light |

**Real-world note:** GitHub Copilot reduced their MCP toolset from 40 tools to 13 and benchmark scores went *up*. Fewer, well-scoped tools consistently outperform a sprawling toolset.

---

## Development

```bash
git clone https://github.com/basilalshukaili/mcp-lint
cd mcp-lint
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

---

## License

MIT — see [LICENSE](LICENSE).
