# Changelog

All notable changes to `mcp-config-lint` are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.2.0] - 2026-06-02

### Added

**New security rules**
- `sec:secret-in-args` (SECURITY_HIGH): Detects 15 high-entropy secret patterns (GitHub PATs, OpenAI keys, Slack tokens, AWS key IDs, Google API keys, PyPI tokens, GitLab PATs, Linear keys, Notion tokens, DigitalOcean PATs) placed directly in the `args` array instead of `env`. Args are visible in process lists (`ps aux`) and shell history.
- `sec:private-key-in-env` (SECURITY_HIGH): Detects raw PEM private key or certificate content embedded in env vars. Keys should be stored as files (chmod 600) and referenced by path.

**New gotcha rules**
- `gotcha:filesystem-docker-socket` (WARNING): Fires when the filesystem server is given `/var/run/docker.sock` as a path. Docker socket access allows container escape to the host.
- `gotcha:notion-oauth-token` (WARNING): Detects Notion OAuth tokens (`ntn_...`) which expire and must be refreshed — not suitable for persistent MCP use.
- `gotcha:notion-invalid-token-format` (WARNING): Notion integration tokens must start with `secret_`; other formats indicate a copy/paste error.
- `gotcha:browser-no-sandbox` (WARNING): Fires when puppeteer or playwright is configured with `--no-sandbox`, which disables Chromium security sandboxing.
- `gotcha:stripe-live-key` (WARNING): Detects Stripe live secret keys (`sk_live_...`) to remind users these create real charges.

**Expanded data coverage**
- `REQUIRED_ENV` now covers 14 additional servers: notion, openai, anthropic, jira, confluence, hubspot, stripe, twilio, sendgrid, datadog, pagerduty, zendesk, airtable, mongodb.
- `TOKEN_ESTIMATES` now includes jira (22k), confluence (16k), hubspot (18k), stripe (14k), datadog (12k), mongodb (7k), mysql (7k), playwright (5k), openai (3k).
- `WRITE_ACCESS_SERVERS` expanded to include mongodb, mysql, stripe, hubspot, jira, confluence, airtable.
- `BROAD_SCOPE_SERVERS` expanded to include stripe and hubspot with actionable remediation guidance.
- `NETWORK_SERVERS` expanded to include playwright, browser-use, web, scraper, crawler, curl.
- `SECRET_ARG_PATTERNS` — new data structure with 15 token regex patterns for the `sec:secret-in-args` rule.

**Project infrastructure**
- `CONTRIBUTING.md` with setup guide, checklist for new rules, PR process.
- `.github/ISSUE_TEMPLATE/bug_report.md` for structured bug reports.
- `.github/ISSUE_TEMPLATE/new_check_request.md` for structured rule proposals.
- `.github/PULL_REQUEST_TEMPLATE.md` for consistent PR reviews.

### Changed

- CI workflow badge added to README.
- README rule table updated to reflect all new rules.

---

## [0.1.1] - 2025-11-01

### Changed

- Linked PyPI package to correct GitHub repository URL.

---

## [0.1.0] - 2025-10-15

### Added

- Initial release.
- Structural checks: JSON validity, missing `mcpServers`, empty config.
- Per-server checks: missing command/args, command/runtime mismatch (npx vs uvx), required env vars, placeholder detection.
- Per-server gotchas: filesystem relative paths, postgres:// prefix, GitHub fine-grained PAT, Brave Search quota, Slack scopes, Redis credentials, GDrive relative path, Sentry scopes.
- Security checks: write access, broad token scopes, classic GitHub PAT, AWS key in config, DB credentials in args/env, 0.0.0.0 binding, wildcard CORS, network-capable servers, filesystem root/home paths.
- Token cost estimates for 20+ servers with warn (20k) and danger (50k) thresholds.
- `--strict`, `--json`, `--security-only`, `--max-tokens` flags.
- GitHub Action (`action.yml`) for CI integration.
