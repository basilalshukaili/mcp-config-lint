"""
Check engine for mcp-lint.
Each check returns a list of Finding objects.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .data import (
    BROAD_SCOPE_SERVERS,
    NETWORK_SERVERS,
    NPX_PACKAGES,
    PATH_PLACEHOLDER_VALUES,
    PLACEHOLDER_VALUES,
    REQUIRED_ENV,
    SECRET_ARG_PATTERNS,
    TOKEN_DEFAULT_UNKNOWN,
    TOKEN_ESTIMATES,
    TOKEN_WARN_THRESHOLD,
    TOKEN_DANGER_THRESHOLD,
    UVX_PACKAGES,
    WRITE_ACCESS_SERVERS,
)


# ---------------------------------------------------------------------------
# Finding model
# ---------------------------------------------------------------------------
class Level:
    ERROR   = "error"    # Blocks CI (always)
    WARNING = "warning"  # Blocks CI in --strict mode
    INFO    = "info"     # Never blocks CI
    SECURITY_HIGH = "security:high"    # Blocks CI
    SECURITY_MED  = "security:medium"  # Blocks CI in --strict
    SECURITY_LOW  = "security:low"     # Never blocks CI


@dataclass
class Finding:
    level:   str
    server:  str | None   # None = global / structural
    code:    str           # short machine-readable ID
    message: str
    fix:     str = ""

    def is_error(self) -> bool:
        return self.level in (Level.ERROR, Level.SECURITY_HIGH)

    def is_warning(self) -> bool:
        return self.level in (Level.WARNING, Level.SECURITY_MED)

    def is_security(self) -> bool:
        return self.level.startswith("security:")


# ---------------------------------------------------------------------------
# Placeholder helpers
# ---------------------------------------------------------------------------
def _is_placeholder(val: str) -> bool:
    if not val:
        return False
    if val in PLACEHOLDER_VALUES:
        return True
    low = val.lower()
    if low.startswith("your_") or low.startswith("your-"):
        return True
    if val.endswith("_here") or val.endswith("-here"):
        return True
    if "placeholder" in low:
        return True
    if val.startswith("<") and val.endswith(">"):
        return True
    return False


def _is_path_placeholder(val: str) -> bool:
    if not val:
        return False
    if val in PATH_PLACEHOLDER_VALUES:
        return True
    if re.match(r"^/path/to/", val, re.IGNORECASE):
        return True
    if re.search(r"\bpath[/\\]to\b", val, re.IGNORECASE):
        return True
    return False


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------
def _get_token_data(name: str, cfg: dict) -> dict:
    n = name.lower()
    if n in TOKEN_ESTIMATES:
        return TOKEN_ESTIMATES[n]
    # Fuzzy match on partial name
    for key, val in TOKEN_ESTIMATES.items():
        if key in n or n in key:
            return val
    # Try args
    args = cfg.get("args", [])
    for arg in args:
        a = str(arg)
        for key, val in TOKEN_ESTIMATES.items():
            if key in a:
                return val
    return TOKEN_DEFAULT_UNKNOWN


# ---------------------------------------------------------------------------
# Structural checks (global)
# ---------------------------------------------------------------------------
def check_structure(config: Any) -> list[Finding]:
    findings: list[Finding] = []

    if not isinstance(config, dict):
        findings.append(Finding(
            level=Level.ERROR, server=None, code="structure:not-object",
            message="Config root must be a JSON object.",
            fix='The file must start with { and contain a "mcpServers" key.',
        ))
        return findings

    if "mcpServers" not in config:
        findings.append(Finding(
            level=Level.ERROR, server=None, code="structure:missing-mcp-servers",
            message='"mcpServers" key missing from config root.',
            fix='Add "mcpServers": {} at the top level.',
        ))
        return findings

    mcp = config["mcpServers"]
    if not isinstance(mcp, dict):
        findings.append(Finding(
            level=Level.ERROR, server=None, code="structure:mcp-servers-not-object",
            message='"mcpServers" must be a JSON object, not an array or scalar.',
        ))
        return findings

    if len(mcp) == 0:
        findings.append(Finding(
            level=Level.WARNING, server=None, code="structure:empty",
            message="mcpServers is empty - no servers configured.",
            fix='Add at least one server entry.',
        ))

    return findings


# ---------------------------------------------------------------------------
# Per-server checks
# ---------------------------------------------------------------------------
def check_server(name: str, cfg: Any) -> list[Finding]:
    if not isinstance(cfg, dict):
        return [Finding(
            level=Level.ERROR, server=name, code="server:not-object",
            message=f'Server "{name}" config must be a JSON object.',
        )]

    findings: list[Finding] = []
    cmd  = cfg.get("command", "")
    args = cfg.get("args", [])
    env  = cfg.get("env", {}) or {}
    args_str = " ".join(str(a) for a in (args or []))
    n = name.lower()

    # --- command present ---
    if not cmd:
        findings.append(Finding(
            level=Level.ERROR, server=name, code="server:missing-command",
            message=f'"{name}" is missing "command".',
            fix='Add "command": "npx" (for npm packages) or "command": "uvx" (for Python/uv packages).',
        ))
    # --- args present ---
    if not args or not isinstance(args, list) or len(args) == 0:
        findings.append(Finding(
            level=Level.ERROR, server=name, code="server:missing-args",
            message=f'"{name}" has missing or empty "args".',
            fix='Add "args": ["-y", "@modelcontextprotocol/server-name"] for npx, or ["mcp-server-name"] for uvx.',
        ))

    # --- command/runtime mismatch ---
    if cmd and args:
        for pkg in NPX_PACKAGES:
            if pkg in args_str and cmd == "uvx":
                findings.append(Finding(
                    level=Level.ERROR, server=name, code="server:cmd-mismatch-uvx-for-npm",
                    message=f'command is "uvx" but "{pkg}" is an npm package.',
                    fix='Change command to "npx". Add "-y" as the first arg.',
                ))
        for pkg in UVX_PACKAGES:
            if pkg in args_str and cmd == "npx":
                findings.append(Finding(
                    level=Level.ERROR, server=name, code="server:cmd-mismatch-npx-for-uv",
                    message=f'command is "npx" but "{pkg}" is a Python/uv package.',
                    fix='Change command to "uvx". Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh',
                ))

    # --- required env vars ---
    req_vars = REQUIRED_ENV.get(n, [])
    # "env" key missing entirely vs empty dict vs populated dict
    env_key_present = "env" in cfg
    for var in req_vars:
        val = env.get(var, "")
        if not val:
            # No env key at all (not even an empty object)
            if not env_key_present:
                findings.append(Finding(
                    level=Level.ERROR, server=name, code="server:missing-env-object",
                    message=f'"{name}" has no "env" object; required vars are missing: {", ".join(req_vars)}.',
                    fix=f'Add an "env" object containing your credentials.',
                ))
                break
            findings.append(Finding(
                level=Level.ERROR, server=name, code="server:missing-env-var",
                message=f'"{name}" is missing required env var {var}.',
                fix=f'Add "{var}": "<your-real-value>" to the env object for {name}.',
            ))
        elif _is_placeholder(val):
            findings.append(Finding(
                level=Level.WARNING, server=name, code="server:placeholder-env-var",
                message=f'"{name}" env var {var} still has a placeholder: "{val}".',
                fix="Replace with your real API key or token.",
            ))

    # --- extra env vars that are placeholders ---
    for ek, ev in env.items():
        if ek in req_vars:
            continue
        if _is_placeholder(str(ev)):
            findings.append(Finding(
                level=Level.WARNING, server=name, code="server:placeholder-extra-env",
                message=f'"{name}" env var {ek} has an unfilled placeholder: "{ev}".',
                fix="Replace with your real value.",
            ))

    # --- path placeholders in args ---
    for arg in (args or []):
        if _is_path_placeholder(str(arg)):
            findings.append(Finding(
                level=Level.WARNING, server=name, code="server:placeholder-arg",
                message=f'"{name}" arg "{arg}" looks like an unfilled placeholder.',
                fix="Replace with your real path or connection string.",
            ))

    # --- per-server gotchas ---
    findings.extend(_per_server_gotchas(name, cfg))

    return findings


def _per_server_gotchas(name: str, cfg: dict) -> list[Finding]:
    findings: list[Finding] = []
    args = cfg.get("args", []) or []
    env  = cfg.get("env", {}) or {}
    n    = name.lower()

    if n == "filesystem":
        for arg in args:
            a = str(arg)
            # Skip flags and npm package names
            if a.startswith("-") or a.startswith("@") or "server-filesystem" in a:
                continue
            if a and not a.startswith("/") and not re.match(r"^[A-Za-z]:[/\\]", a) and not a.startswith("~"):
                findings.append(Finding(
                    level=Level.WARNING, server=name, code="gotcha:filesystem-relative-path",
                    message=f'Filesystem path "{a}" appears to be relative.',
                    fix="Use an absolute path (e.g. /Users/you/projects). Relative paths break when Claude spawns the server from a different working directory.",
                ))
            # Check for Docker socket mount - a common and serious mistake
            if "/var/run/docker.sock" in a:
                findings.append(Finding(
                    level=Level.WARNING, server=name, code="gotcha:filesystem-docker-socket",
                    message='Filesystem path includes the Docker socket (/var/run/docker.sock).',
                    fix="Granting Claude access to the Docker socket allows container escape to the host. Remove this path unless you specifically need Docker management.",
                ))
        findings.append(Finding(
            level=Level.INFO, server=name, code="gotcha:filesystem-write-access",
            message="filesystem gives Claude READ + WRITE access to all listed paths.",
            fix="Review each path. Only include directories you are comfortable with Claude modifying.",
        ))

    if n == "github":
        tok = env.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
        if tok and not _is_placeholder(tok):
            if tok.startswith("github_pat_"):
                findings.append(Finding(
                    level=Level.WARNING, server=name, code="gotcha:github-fine-grained-pat",
                    message="Fine-grained PAT detected (github_pat_...). Needs explicit per-repo permissions.",
                    fix="Required scopes: Contents (read/write), Issues, Pull requests.",
                ))
        findings.append(Finding(
            level=Level.INFO, server=name, code="gotcha:github-write",
            message="github server can push commits and merge PRs.",
            fix="Ensure your PAT only has access to the repos you intend.",
        ))

    if n in ("postgres", "postgresql"):
        for arg in args:
            a = str(arg)
            if a.startswith("postgres://"):
                findings.append(Finding(
                    level=Level.WARNING, server=name, code="gotcha:postgres-prefix",
                    message=f'Connection string uses "postgres://" prefix.',
                    fix='Some drivers require "postgresql://". If you see connection errors, change the prefix.',
                ))
            # Check for real credentials: match user:password@ and exclude placeholder passwords
            m = re.search(r"postgres(ql)?://([^:@/]+):([^@]+)@", a)
            if m:
                password = m.group(3)
                if not re.search(r"^(your|pass|password|test|changeme|placeholder)$", password, re.I):
                    findings.append(Finding(
                        level=Level.WARNING, server=name, code="gotcha:postgres-creds-in-args",
                        message="Database credentials are visible in config args.",
                        fix='Consider moving the connection string to a POSTGRES_URL env var.',
                    ))

    if n == "brave-search":
        findings.append(Finding(
            level=Level.INFO, server=name, code="gotcha:brave-search-quota",
            message="Brave Search free tier: 2,000 queries/month.",
            fix="Monitor usage at https://api.search.brave.com/ - heavy Claude use can burn through quickly.",
        ))

    if n == "slack":
        findings.append(Finding(
            level=Level.INFO, server=name, code="gotcha:slack-scopes",
            message="Slack server can send messages and read channel history.",
            fix="Keep bot token scopes minimal: channels:history, chat:write, channels:read.",
        ))

    if n == "redis":
        url = env.get("REDIS_URL", "")
        if re.search(r"redis://(:[^@]+@|[^:]+:[^@]+@)", url) and not re.search(r"your|pass|test|example", url, re.I):
            findings.append(Finding(
                level=Level.WARNING, server=name, code="gotcha:redis-creds-in-url",
                message="Redis password visible in REDIS_URL.",
                fix="Fine for local use. Avoid sharing or committing this config file.",
            ))

    if n == "gdrive":
        cp = env.get("GDRIVE_CREDENTIALS_PATH", "")
        if cp and not _is_path_placeholder(cp):
            if not cp.startswith("/") and not re.match(r"^[A-Za-z]:[/\\]", cp):
                findings.append(Finding(
                    level=Level.WARNING, server=name, code="gotcha:gdrive-relative-path",
                    message=f'GDRIVE_CREDENTIALS_PATH appears to be relative: "{cp}".',
                    fix="Use an absolute path to the credentials JSON file.",
                ))

    if n == "sentry":
        findings.append(Finding(
            level=Level.INFO, server=name, code="gotcha:sentry-scopes",
            message="Sentry auth token needs org:read and project:read scopes.",
            fix="Create tokens at: https://sentry.io/settings/account/api/auth-tokens/",
        ))

    if n == "notion":
        api_key = env.get("NOTION_API_KEY", "")
        if api_key and not _is_placeholder(api_key):
            # Notion integration tokens start with secret_; OAuth tokens start with ntn_
            if api_key.startswith("ntn_"):
                findings.append(Finding(
                    level=Level.WARNING, server=name, code="gotcha:notion-oauth-token",
                    message='Notion OAuth token detected (ntn_...). OAuth tokens expire and must be refreshed.',
                    fix="For persistent MCP access, create a Notion integration token (starts with secret_) at https://www.notion.so/my-integrations",
                ))
            elif not api_key.startswith("secret_"):
                findings.append(Finding(
                    level=Level.WARNING, server=name, code="gotcha:notion-invalid-token-format",
                    message="NOTION_API_KEY does not match the expected format (should start with secret_).",
                    fix="Create an internal integration token at https://www.notion.so/my-integrations",
                ))

    if n in ("puppeteer", "playwright"):
        # Check if running in a context that might expose screenshots or sensitive data
        for arg in args:
            a = str(arg)
            if "--no-sandbox" in a:
                findings.append(Finding(
                    level=Level.WARNING, server=name, code="gotcha:browser-no-sandbox",
                    message=f'"{name}" is configured with --no-sandbox, disabling Chromium security sandboxing.',
                    fix="Only use --no-sandbox if required by your environment (e.g. inside Docker). It weakens browser isolation.",
                ))

    if n == "stripe":
        sk = env.get("STRIPE_SECRET_KEY", "")
        if sk and not _is_placeholder(sk) and sk.startswith("sk_live_"):
            findings.append(Finding(
                level=Level.WARNING, server=name, code="gotcha:stripe-live-key",
                message="Stripe LIVE secret key detected. This key can create real charges.",
                fix="Consider using a restricted key with only the permissions needed. Test with sk_test_ keys during development.",
            ))

    return findings


# ---------------------------------------------------------------------------
# Security checks
# ---------------------------------------------------------------------------
def check_security(name: str, cfg: dict) -> list[Finding]:
    findings: list[Finding] = []
    n    = name.lower()
    env  = cfg.get("env", {}) or {}
    args = cfg.get("args", []) or []

    # 1. Write access
    if n in WRITE_ACCESS_SERVERS:
        findings.append(Finding(
            level=Level.SECURITY_HIGH, server=name, code="sec:write-access",
            message=f'"{name}" can modify files, data, or send messages on your behalf.',
            fix="Review what paths/repos/channels are in scope. Only include this server if you actively need write operations.",
        ))

    # 2. Broad token scope
    if n in BROAD_SCOPE_SERVERS:
        findings.append(Finding(
            level=Level.SECURITY_MED, server=name, code="sec:broad-scope",
            message=f'"{name}" uses a potentially broad-scoped token.',
            fix=BROAD_SCOPE_SERVERS[n],
        ))

    # 3. High-privilege token patterns
    gh_tok = env.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    if gh_tok and not _is_placeholder(gh_tok) and gh_tok.startswith("ghp_"):
        findings.append(Finding(
            level=Level.SECURITY_MED, server=name, code="sec:classic-github-pat",
            message='Classic GitHub PAT (ghp_...) grants repo-wide read+write by default.',
            fix="Consider migrating to a fine-grained PAT: github.com/settings/tokens?type=beta",
        ))

    aws_key = env.get("AWS_ACCESS_KEY_ID", "")
    if aws_key and not _is_placeholder(aws_key):
        findings.append(Finding(
            level=Level.SECURITY_HIGH, server=name, code="sec:aws-key-in-config",
            message="AWS access key present in config. If this file is committed or shared, the key is exposed.",
            fix="Store AWS credentials in ~/.aws/credentials or environment variables, not in MCP config.",
        ))

    # 4. DB credentials in env vars
    for ek, ev in env.items():
        ev_str = str(ev)
        if any(kw in ek for kw in ("DATABASE_URL", "POSTGRES", "MYSQL", "REDIS_URL")):
            if re.search(r":[^@]+@", ev_str) and not _is_placeholder(ev_str):
                findings.append(Finding(
                    level=Level.SECURITY_MED, server=name, code="sec:db-creds-in-env",
                    message=f"Database connection string with credentials in env var: {ek}.",
                    fix="Acceptable for local dev. If this config is shared or committed, credentials will be exposed.",
                ))

    # 5. DB credentials in args
    for arg in args:
        a = str(arg)
        m = re.search(r"postgres(ql)?://([^:@/]+):([^@]+)@", a)
        if m:
            password = m.group(3)
            if not re.search(r"^(your|pass|password|test|changeme|placeholder)$", password, re.I):
                findings.append(Finding(
                    level=Level.SECURITY_HIGH, server=name, code="sec:db-creds-in-args",
                    message="Database credentials visible in args array.",
                    fix="Arguments are plaintext and exposed in process lists. Move the connection string to an env var.",
                ))

    # 6. Network binding: 0.0.0.0
    for arg in args:
        a = str(arg)
        if a == "0.0.0.0" or "--host=0.0.0.0" in a or "--bind=0.0.0.0" in a:
            findings.append(Finding(
                level=Level.SECURITY_HIGH, server=name, code="sec:bind-all-interfaces",
                message=f'"{name}" bound to 0.0.0.0 - listens on all network interfaces.',
                fix="Bind to 127.0.0.1 unless you specifically need LAN access.",
            ))
        if a in ("cors", "--cors") or "cors=*" in a or 'cors="*"' in a:
            findings.append(Finding(
                level=Level.SECURITY_MED, server=name, code="sec:wildcard-cors",
                message=f'"{name}" has wildcard CORS enabled - any origin can reach this server.',
                fix="Restrict CORS to specific origins if the server is accessible from a browser context.",
            ))

    # 7. Network-capable servers
    for net_kw in NETWORK_SERVERS:
        if net_kw in n:
            findings.append(Finding(
                level=Level.SECURITY_LOW, server=name, code="sec:network-capable",
                message=f'"{name}" can make outbound requests on your behalf.',
                fix="Review what URLs/domains this server is allowed to reach. Unconstrained fetch can be leveraged in prompt-injection attacks.",
            ))
            break

    # 8. Broad filesystem paths
    if n == "filesystem":
        for arg in args:
            a = str(arg)
            if a in ("/", "~", "/Users", "/home", "C:\\", "C:/"):
                findings.append(Finding(
                    level=Level.SECURITY_HIGH, server=name, code="sec:filesystem-root-path",
                    message=f'filesystem path "{a}" grants access to the entire drive root.',
                    fix="Scope to specific project directories only.",
                ))
            elif a.startswith("/Users/") and len(a.split("/")) <= 3:
                findings.append(Finding(
                    level=Level.SECURITY_MED, server=name, code="sec:filesystem-home-path",
                    message=f'filesystem path "{a}" covers a full home directory.',
                    fix="This includes dotfiles, SSH keys, ~/.aws credentials, browser profiles. Scope to a specific subdirectory.",
                ))

    # 9. Secrets detected directly in args (should be in env vars instead)
    for arg in args:
        a = str(arg)
        for pattern, description in SECRET_ARG_PATTERNS:
            if re.search(pattern, a):
                findings.append(Finding(
                    level=Level.SECURITY_HIGH, server=name, code="sec:secret-in-args",
                    message=f'Possible {description} found directly in args array.',
                    fix="Move credentials to the env object. Args are visible in process lists (ps aux) and shell history.",
                ))
                break  # Only report once per arg

    # 10. Private key content in env vars
    for ek, ev in env.items():
        ev_str = str(ev)
        if "-----BEGIN" in ev_str and ("PRIVATE KEY" in ev_str or "CERTIFICATE" in ev_str):
            findings.append(Finding(
                level=Level.SECURITY_HIGH, server=name, code="sec:private-key-in-env",
                message=f'env var "{ek}" appears to contain a raw private key or certificate.',
                fix="Store private keys as files on disk (chmod 600) and reference them by path. Never embed key material in config files.",
            ))

    return findings


# ---------------------------------------------------------------------------
# Token cost check
# ---------------------------------------------------------------------------
def check_token_cost(servers: dict[str, dict], max_tokens: int | None) -> list[Finding]:
    findings: list[Finding] = []
    total = 0
    server_data = []

    for name, cfg in servers.items():
        td = _get_token_data(name, cfg)
        total += td["tokens"]
        server_data.append((name, td["tokens"], td["tier"], td["note"]))

    pct = round(total / 200_000 * 100)
    tier_label = "high" if total >= TOKEN_DANGER_THRESHOLD else "moderate" if total >= TOKEN_WARN_THRESHOLD else "low"

    if total >= TOKEN_DANGER_THRESHOLD:
        findings.append(Finding(
            level=Level.WARNING, server=None, code="token:high-context-tax",
            message=f"High context tax: ~{total:,} tokens ({pct}% of 200k window) consumed by tool definitions before any conversation.",
            fix="Remove servers you rarely use, or replace heavy multi-purpose servers with focused single-purpose ones.",
        ))
    elif total >= TOKEN_WARN_THRESHOLD:
        findings.append(Finding(
            level=Level.INFO, server=None, code="token:moderate-context-tax",
            message=f"Moderate context tax: ~{total:,} tokens ({pct}% of 200k window). Performance can degrade as you add more servers.",
        ))

    # Per-server breakdown as INFO
    for name, tokens, tier, note in sorted(server_data, key=lambda x: -x[1]):
        findings.append(Finding(
            level=Level.INFO, server=name, code=f"token:estimate:{tier}",
            message=f"~{tokens:,} tokens ({tier}). {note}",
        ))

    # --max-tokens override
    if max_tokens is not None and total > max_tokens:
        findings.append(Finding(
            level=Level.ERROR, server=None, code="token:exceeds-max",
            message=f"Total token cost ~{total:,} exceeds --max-tokens {max_tokens:,}.",
            fix=f"Reduce servers or raise --max-tokens.",
        ))

    return findings


# ---------------------------------------------------------------------------
# Top-level runner
# ---------------------------------------------------------------------------
def run_all_checks(
    config: Any,
    *,
    security_only: bool = False,
    max_tokens: int | None = None,
) -> list[Finding]:
    findings: list[Finding] = []

    # Structural checks always run
    struct = check_structure(config)
    findings.extend(struct)
    if any(f.is_error() for f in struct):
        return findings  # Can't proceed without valid structure

    servers: dict[str, dict] = config.get("mcpServers", {})

    if not security_only:
        for name, cfg in servers.items():
            findings.extend(check_server(name, cfg))
        findings.extend(check_token_cost(servers, max_tokens))

    for name, cfg in servers.items():
        findings.extend(check_security(name, cfg))

    return findings
