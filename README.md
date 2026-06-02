# mcp-config-lint

[![PyPI version](https://img.shields.io/pypi/v/mcp-config-lint.svg)](https://pypi.org/project/mcp-config-lint/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcp-config-lint.svg)](https://pypi.org/project/mcp-config-lint/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Validate and security-check your claude_desktop_config.json in CI or locally. Zero dependencies.**

---

## Install



Requires Python 3.9+. No third-party dependencies.

---

## Quickstart



Sample output:



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



| Flag | Description |
|---|---|
| --strict | Treat warnings as failures (exit 1) |
| --json | Machine-readable JSON output |
| --security-only | Only run security checks |
| --max-tokens N | Fail if estimated token cost exceeds N |
| --version | Print version and exit |

---

## GitHub Actions example



---

## JSON output schema



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
