# mcp-config-lint

[![PyPI version](https://img.shields.io/pypi/v/mcp-config-lint.svg)](https://pypi.org/project/mcp-config-lint/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcp-config-lint.svg)](https://pypi.org/project/mcp-config-lint/)
[![CI](https://github.com/basilalshukaili/mcp-config-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/basilalshukaili/mcp-config-lint/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Action](https://img.shields.io/badge/GitHub%20Action-available-blue?logo=github)](https://github.com/basilalshukaili/mcp-config-lint)

**Validate and security-check your `claude_desktop_config.json` before it bites you. Zero dependencies.**

MCP configs wire Claude to real tools — filesystems, GitHub, databases, payment APIs. A single misconfiguration can silently break a server, expose credentials in a process list, or grant Claude write access to your entire home directory. `mcp-config-lint` catches these issues locally and in CI, before they reach production.

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

  (global)
    [WARN ]  High context tax: ~82,000 tokens (41% of 200k window) consumed by tool
              definitions before any conversation.
              Fix: Remove servers you rarely use, or replace heavy multi-purpose servers
              with focused single-purpose ones.

  filesystem
    [WARN ]  Filesystem path "projects/" appears to be relative.
              Fix: Use an absolute path (e.g. /Users/you/projects). Relative paths break
              when Claude spawns the server from a different working directory.
    [SEC:HIGH]  filesystem gives Claude READ + WRITE access to all listed paths.
              Fix: Review each path. Only include directories you are comfortable with
              Claude modifying.

  github
    [SEC:MED]  GITHUB_PERSONAL_ACCESS_TOKEN - classic PAT with repo scope grants
               read+write to all repos. Consider fine-grained PATs scoped to specific
               repositories.

  my-custom-server
    [SEC:HIGH]  Possible GitHub classic PAT found directly in args array.
               Fix: Move credentials to the env object. Args are visible in process
               lists (ps aux) and shell history.

  3 error(s), 2 warning(s)
```

Exit code 0 if clean. Exit code 1 if errors are found (or warnings in `--strict` mode).

---

## Flags

```
mcp-config-lint [config] [--strict] [--json] [--security-only] [--max-tokens N]
```

| Flag | Description |
|---|---|
| `--strict` | Treat warnings as failures (exit 1) |
| `--json` | Machine-readable JSON output |
| `--security-only` | Only run security checks |
| `--max-tokens N` | Fail if estimated token cost exceeds N |
| `--version` | Print version and exit |

---

## Use in CI

Add this to `.github/workflows/mcp-lint.yml` in any repo that ships a `claude_desktop_config.json`:

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

The action fails the job (exit 1) when errors are found, blocking PR merges until the config is fixed.

### Action inputs

| Input | Description | Default |
|---|---|---|
| `config-path` | Path to the MCP config file | `claude_desktop_config.json` |
| `strict` | Treat warnings as failures | `false` |
| `max-tokens` | Fail if token budget exceeded | _(unset)_ |
| `security-only` | Security checks only | `false` |
| `python-version` | Python version to use | `3.12` |

### Advanced action usage

```yaml
- uses: basilalshukaili/mcp-config-lint@v1
  with:
    config-path: configs/claude_desktop_config.json
    strict: 'true'
    max-tokens: '50000'
    security-only: 'false'
```

---

## Full rule reference

### Structural

| Code | Level | What it catches |
|---|---|---|
| `structure:not-object` | ERROR | Config root is not a JSON object |
| `structure:missing-mcp-servers` | ERROR | Top-level `mcpServers` key is absent |
| `structure:mcp-servers-not-object` | ERROR | `mcpServers` is an array or scalar |
| `structure:empty` | WARN | `mcpServers` has no entries |
| `json:parse-error` | ERROR | File contains invalid JSON |

### Per-server

| Code | Level | What it catches |
|---|---|---|
| `server:not-object` | ERROR | Server config is not a JSON object |
| `server:missing-command` | ERROR | `command` field is absent |
| `server:missing-args` | ERROR | `args` field is absent or empty |
| `server:cmd-mismatch-uvx-for-npm` | ERROR | `uvx` used with an npm package |
| `server:cmd-mismatch-npx-for-uv` | ERROR | `npx` used with a Python/uv package |
| `server:missing-env-object` | ERROR | No `env` object; required vars are absent |
| `server:missing-env-var` | ERROR | Required env var is missing |
| `server:placeholder-env-var` | WARN | Required env var still has a placeholder value |
| `server:placeholder-extra-env` | WARN | Extra env var has an unfilled placeholder |
| `server:placeholder-arg` | WARN | Arg looks like an unfilled path placeholder |

### Per-server gotchas

| Code | Level | What it catches |
|---|---|---|
| `gotcha:filesystem-relative-path` | WARN | Filesystem path is relative (breaks when server spawns from different cwd) |
| `gotcha:filesystem-write-access` | INFO | Reminder that filesystem gives read + write access |
| `gotcha:filesystem-docker-socket` | WARN | `/var/run/docker.sock` exposed — allows container escape |
| `gotcha:github-fine-grained-pat` | WARN | Fine-grained PAT needs explicit per-repo permission grants |
| `gotcha:github-write` | INFO | Reminder that GitHub server can push commits and merge PRs |
| `gotcha:postgres-prefix` | WARN | `postgres://` prefix — some drivers require `postgresql://` |
| `gotcha:postgres-creds-in-args` | WARN | Database credentials visible in args |
| `gotcha:brave-search-quota` | INFO | Brave Search free tier: 2,000 queries/month |
| `gotcha:slack-scopes` | INFO | Reminder to keep Slack bot scopes minimal |
| `gotcha:redis-creds-in-url` | WARN | Redis password visible in `REDIS_URL` |
| `gotcha:gdrive-relative-path` | WARN | `GDRIVE_CREDENTIALS_PATH` is a relative path |
| `gotcha:sentry-scopes` | INFO | Sentry token needs org:read and project:read |
| `gotcha:notion-oauth-token` | WARN | Notion OAuth token (`ntn_...`) expires; integration tokens are more reliable |
| `gotcha:notion-invalid-token-format` | WARN | `NOTION_API_KEY` doesn't match expected `secret_` format |
| `gotcha:browser-no-sandbox` | WARN | `--no-sandbox` disables Chromium security sandboxing |
| `gotcha:stripe-live-key` | WARN | Stripe live key (`sk_live_...`) can create real charges |

### Security

| Code | Level | What it catches |
|---|---|---|
| `sec:write-access` | SEC:HIGH | Server can modify files, data, or send messages |
| `sec:broad-scope` | SEC:MED | Server uses a broad-scoped token |
| `sec:classic-github-pat` | SEC:MED | Classic GitHub PAT (`ghp_...`) grants repo-wide read+write |
| `sec:aws-key-in-config` | SEC:HIGH | AWS access key present in config |
| `sec:db-creds-in-env` | SEC:MED | DB connection string with credentials in env var |
| `sec:db-creds-in-args` | SEC:HIGH | DB credentials visible in args (exposed in process lists) |
| `sec:bind-all-interfaces` | SEC:HIGH | Server bound to `0.0.0.0` |
| `sec:wildcard-cors` | SEC:MED | Wildcard CORS enabled |
| `sec:network-capable` | SEC:LOW | Server can make outbound requests (prompt-injection risk) |
| `sec:filesystem-root-path` | SEC:HIGH | Filesystem path covers `/`, `~`, or drive root |
| `sec:filesystem-home-path` | SEC:MED | Filesystem path covers an entire home directory |
| `sec:secret-in-args` | SEC:HIGH | Known secret pattern (PAT, API key, token) found directly in args |
| `sec:private-key-in-env` | SEC:HIGH | Raw PEM private key or certificate content in env var |

Patterns detected by `sec:secret-in-args`: GitHub PATs (`ghp_`, `github_pat_`, `ghs_`), OpenAI keys (`sk-`), Slack tokens (`xoxb-`, `xoxp-`), AWS key IDs (`AKIA...`), Google API keys (`AIza...`), Google OAuth tokens (`ya29.`), PyPI tokens (`pypi-`), GitLab PATs (`glpat-`), Linear keys (`lin_api_`), Notion tokens (`secret_`), DigitalOcean PATs (`dp.pt.`).

### Token cost

| Code | Level | What it catches |
|---|---|---|
| `token:high-context-tax` | WARN | Total token cost exceeds 50k tokens |
| `token:moderate-context-tax` | INFO | Total token cost between 20k–50k tokens |
| `token:estimate:<tier>` | INFO | Per-server token estimate |
| `token:exceeds-max` | ERROR | Total cost exceeds `--max-tokens` limit |

Token estimates are available for 30+ servers. Unknown servers default to 5k tokens.

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
      "level": "security:high",
      "server": "my-custom-server",
      "code": "sec:secret-in-args",
      "message": "Possible GitHub classic PAT found directly in args array.",
      "fix": "Move credentials to the env object. Args are visible in process lists (ps aux) and shell history."
    }
  ],
  "summary": {
    "errors": 1,
    "warnings": 0,
    "info": 2
  }
}
```

---

## FAQ

**Why does `sec:write-access` fire on servers I trust?**

The write-access check is informational about capability, not a bug. It fires on any server that can modify data (filesystem, GitHub, Slack, databases, etc.) to ensure you've made a conscious decision to include it. It will always fire for these servers; review the included paths/repos/channels to confirm the scope is intentional.

**How do I suppress a false positive?**

There is no per-server suppression yet. If a check fires on a valid config, please [open an issue](https://github.com/basilalshukaili/mcp-config-lint/issues) with a minimal reproducer and we'll either fix the check or add a suppression mechanism.

**Can I lint configs other than `claude_desktop_config.json`?**

Yes — pass any JSON file that matches the `{"mcpServers": {...}}` schema.

**What does `--max-tokens` do?**

It fails the run if the estimated total token cost of all configured servers exceeds the given number. Useful for enforcing a budget in CI. The default threshold warnings (20k / 50k) still apply regardless of this flag.

**Does this send my config anywhere?**

No. The linter runs entirely locally and makes no network requests.

**Where do the token estimates come from?**

Community benchmarks, MCP server READMEs, and direct measurement. GitHub Copilot's public announcement that cutting their toolset from 40 to 13 tools improved benchmark scores is one calibration point. Estimates are conservative; the actual cost depends on the server version and runtime.

---

## Why this exists

MCP configs wire AI assistants to real tools. A misconfigured server silently fails. An insecure one exposes credentials or grants write access you did not intend.

The checks in this CLI are ported from the [Hatchloop MCP Config Auditor](https://hatchloop.dev/tools/mcp-audit/) (battle-tested in the browser) — now available as a zero-dependency CLI you can drop into CI.

> GitHub Copilot cut their MCP toolset from 40 tools down to 13 and benchmark scores went up.
> Fewer, well-scoped tools consistently outperform a sprawling toolset. Use `--max-tokens` to stay disciplined.

---

## Contributing

Bug reports and new server checks are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide, or open an issue at [github.com/basilalshukaili/mcp-config-lint/issues](https://github.com/basilalshukaili/mcp-config-lint/issues).

---

## License

MIT — see [LICENSE](LICENSE).
