# mcp-config-lint

[![PyPI version](https://img.shields.io/pypi/v/mcp-config-lint.svg)](https://pypi.org/project/mcp-config-lint/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcp-config-lint.svg)](https://pypi.org/project/mcp-config-lint/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Action](https://img.shields.io/badge/GitHub%20Action-mcp--config--lint-blue?logo=github)](https://github.com/basilalshukaili/mcp-config-lint)

**Validate and security-check your claude_desktop_config.json in CI or locally. Zero dependencies.**

---

## Install

```bash
pip install mcp-config-lint
```

Requires Python 3.9+. No third-party dependencies.

---

## Quickstart

```bash
mcp-config-lint claude_desktop_config.json
```

Sample output:

```
  mcp-lint  claude_desktop_config.json

  filesystem
    [WARN ]  Relative path used: ./my-project
              Fix: Use an absolute path, e.g. /Users/you/my-project

  github
    [SEC:HIGH]  GITHUB_PERSONAL_ACCESS_TOKEN has broad repo scope
              Fix: Use a fine-grained token scoped to specific repositories

  2 warning(s) (will fail in --strict mode)
```

Exits 0 if clean. Exits 1 if errors are found.

---

## What it checks

| Category | Examples |
|---|---|
| **Validity** | Invalid JSON, missing mcpServers key, empty config |
| **Structure** | Missing command/args, wrong data types |
| **Runtime mismatch** | uvx used with an npm package, and vice versa |
| **Unfilled placeholders** | your_token_here, /path/to/your/repo left in config |
| **Missing env vars** | GitHub server without GITHUB_PERSONAL_ACCESS_TOKEN |
| **Per-server gotchas** | Relative filesystem paths, postgres:// vs postgresql://, Brave quota |
| **Security** | Write-access servers, broad token scopes, AWS keys in args, 0.0.0.0 binds |
| **Token bloat** | Estimated context tax per server; warns when total exceeds 20k or 50k tokens |

---

## Flags

```
mcp-config-lint [config] [--strict] [--json] [--security-only] [--max-tokens N]
```

| Flag | Description |
|---|---|
| --strict | Treat warnings as failures (exit 1) |
| --json | Machine-readable JSON output |
| --security-only | Only run security checks |
| --max-tokens N | Fail if estimated token cost exceeds N |
| --version | Print version and exit |

---

## Use in CI

Drop this into `.github/workflows/mcp-lint.yml` in any repo that ships a `claude_desktop_config.json`:

```yaml
name: MCP Config Lint

on:
  push:
    branches: [main]
    paths: ['claude_desktop_config.json']
  pull_request:
    paths: ['claude_desktop_config.json']

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: basilalshukaili/mcp-config-lint@v1
        with:
          config-path: claude_desktop_config.json
```

### Action inputs

| Input | Description | Default |
|---|---|---|
| `config-path` | Path to the MCP config file | `claude_desktop_config.json` |
| `strict` | Treat warnings as failures | `false` |
| `max-tokens` | Fail if token budget exceeded | _(unset)_ |
| `security-only` | Security checks only | `false` |
| `python-version` | Python version to use | `3.12` |

### Advanced usage

```yaml
- uses: basilalshukaili/mcp-config-lint@v1
  with:
    config-path: configs/claude_desktop_config.json
    strict: 'true'
    max-tokens: '50000'
    security-only: 'false'
```

The action fails the job (exit 1) when errors are found, blocking PR merges until the config is fixed — a genuine CI gate for your MCP configuration.

---

## GitHub Actions example

```yaml
name: MCP Config Lint

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: basilalshukaili/mcp-config-lint@v1
        with:
          config-path: claude_desktop_config.json
          strict: 'true'
```

---

## JSON output schema

```bash
mcp-config-lint --json claude_desktop_config.json
```

```json
{
  "source": "claude_desktop_config.json",
  "exit_code": 1,
  "findings": [
    {
      "level": "warning",
      "server": "filesystem",
      "code": "fs:relative-path",
      "message": "Relative path used: ./my-project",
      "fix": "Use an absolute path, e.g. /Users/you/my-project"
    }
  ],
  "summary": {
    "errors": 0,
    "warnings": 1,
    "info": 0
  }
}
```

---

## Why this exists

MCP configs wire AI assistants to real tools — filesystems, GitHub, Slack, databases. A misconfigured
server silently fails. An insecure one exposes credentials or grants write access you did not intend.

The checks in this CLI are ported from the
[Hatchloop MCP Config Auditor](https://hatchloop.dev/tools/mcp-audit/) (battle-tested in the browser)
and the doctor.sh script from the MCP Setup Pack — now available as a zero-dependency CLI you can
drop into CI.

> GitHub Copilot cut their MCP toolset from 40 tools down to 13 and benchmark scores went up.
> Fewer, well-scoped tools consistently outperform a sprawling toolset. Use --max-tokens to stay disciplined.

---

## Contributing

Bug reports and new server checks welcome. Open an issue on
[github.com/basilalshukaili/mcp-config-lint](https://github.com/basilalshukaili/mcp-config-lint/issues).

---

## License

MIT — see [LICENSE](LICENSE).
