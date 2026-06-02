"""
Static reference data for mcp-lint checks.
Ported from:
  - /opt/ai-company/web/driftwatch/tools/mcp-audit/index.html  (JS audit engine v2)
  - /opt/ai-company/products/mcp-pack/build/scripts/doctor.sh
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Token-cost estimates
# Sources: community benchmarks, MCP server READMEs, GitHub Copilot public
# announcement (cut 40 tools to 13; benchmark scores went up).
# ---------------------------------------------------------------------------
TOKEN_ESTIMATES: dict[str, dict] = {
    "github":              {"tokens": 50000, "tier": "heavy",
                            "note": "~50k tokens observed. GitHub Copilot cut their toolset from 40 to 13 and benchmark scores went up."},
    "linear":              {"tokens": 32000, "tier": "heavy",
                            "note": "Linear exposes many issue/project/team management tools."},
    "notion":              {"tokens": 28000, "tier": "heavy",
                            "note": "Notion schema-rich API results in large tool definitions."},
    "jira":                {"tokens": 22000, "tier": "heavy",
                            "note": "Jira project/issue management - large schema."},
    "slack":               {"tokens": 22000, "tier": "heavy",
                            "note": "Slack exposes channel, message, and user management tools."},
    "confluence":          {"tokens": 16000, "tier": "heavy",
                            "note": "Confluence pages and spaces management."},
    "hubspot":             {"tokens": 18000, "tier": "heavy",
                            "note": "CRM contacts, deals, companies toolset."},
    "sentry":              {"tokens": 18000, "tier": "heavy",
                            "note": "Sentry surfaces many issue, project, and org management tools."},
    "stripe":              {"tokens": 14000, "tier": "heavy",
                            "note": "Payments, subscriptions, customers - many tools."},
    "supabase":            {"tokens": 16000, "tier": "heavy",
                            "note": "Supabase MCP exposes database, auth, and storage management tools."},
    "datadog":             {"tokens": 12000, "tier": "medium",
                            "note": "Metrics, monitors, and dashboards toolset."},
    "postgres":            {"tokens": 8000,  "tier": "medium",
                            "note": "SQL execution + schema introspection. Relatively lean."},
    "postgresql":          {"tokens": 8000,  "tier": "medium",
                            "note": "SQL execution + schema introspection. Relatively lean."},
    "mongodb":             {"tokens": 7000,  "tier": "medium",
                            "note": "CRUD operations on collections."},
    "mysql":               {"tokens": 7000,  "tier": "medium",
                            "note": "SQL operations, similar to postgres."},
    "gdrive":              {"tokens": 7000,  "tier": "medium",
                            "note": "File list, read, and search tools."},
    "aws-kb-retrieval":    {"tokens": 6000,  "tier": "medium",
                            "note": "AWS Bedrock Knowledge Base retrieval - focused toolset."},
    "redis":               {"tokens": 5000,  "tier": "medium",
                            "note": "Key/value get, set, delete, list operations."},
    "playwright":          {"tokens": 5000,  "tier": "medium",
                            "note": "Browser automation similar to puppeteer."},
    "brave-search":        {"tokens": 4000,  "tier": "medium",
                            "note": "Search + local results. Well-scoped."},
    "google-maps":         {"tokens": 4500,  "tier": "medium",
                            "note": "Places, directions, geocoding tools."},
    "filesystem":          {"tokens": 3500,  "tier": "medium",
                            "note": "Read, write, list, search. Token cost scales with exposed paths."},
    "puppeteer":           {"tokens": 4000,  "tier": "medium",
                            "note": "Browser automation: navigate, click, screenshot, evaluate."},
    "memory":              {"tokens": 3000,  "tier": "light",
                            "note": "Knowledge graph tools - entity/relation create, search, read."},
    "sequential-thinking": {"tokens": 2000,  "tier": "light",
                            "note": "Single tool. Minimal context overhead."},
    "git":                 {"tokens": 3000,  "tier": "light",
                            "note": "Git log, diff, status, commit tools."},
    "fetch":               {"tokens": 1500,  "tier": "light",
                            "note": "Single fetch tool. Very lean."},
    "time":                {"tokens": 1000,  "tier": "light",
                            "note": "get_current_time tool. Minimal overhead."},
    "openai":              {"tokens": 3000,  "tier": "light",
                            "note": "Thin wrapper around OpenAI API."},
    "sqlite":              {"tokens": 3500,  "tier": "light",
                            "note": "SQL read/write on a local SQLite file."},
    "mcp-server-git":      {"tokens": 3000,  "tier": "light",
                            "note": "Git operations. Lean."},
    "mcp-server-fetch":    {"tokens": 1500,  "tier": "light",
                            "note": "Single fetch tool. Very lean."},
    "mcp-server-time":     {"tokens": 1000,  "tier": "light",
                            "note": "get_current_time tool. Minimal overhead."},
    "mcp-server-sqlite":   {"tokens": 3500,  "tier": "light",
                            "note": "SQL read/write on a local SQLite file."},
    "mcp-server-redis":    {"tokens": 5000,  "tier": "medium",
                            "note": "Key/value operations."},
}

TOKEN_DEFAULT_UNKNOWN: dict = {
    "tokens": 5000,
    "tier": "unknown",
    "note": "No data for this server. Using 5k token estimate (typical for ~10 tools).",
}
TOKEN_WARN_THRESHOLD   = 20_000
TOKEN_DANGER_THRESHOLD = 50_000
CONTEXT_WINDOW_200K    = 200_000

# ---------------------------------------------------------------------------
# Required env vars per server key
# ---------------------------------------------------------------------------
REQUIRED_ENV: dict[str, list[str]] = {
    "github":            ["GITHUB_PERSONAL_ACCESS_TOKEN"],
    "supabase":          ["SUPABASE_ACCESS_TOKEN"],
    "redis":             ["REDIS_URL"],
    "brave-search":      ["BRAVE_API_KEY"],
    "google-maps":       ["GOOGLE_MAPS_API_KEY"],
    "gdrive":            ["GDRIVE_CREDENTIALS_PATH"],
    "slack":             ["SLACK_BOT_TOKEN", "SLACK_TEAM_ID"],
    "linear":            ["LINEAR_API_KEY"],
    "sentry":            ["SENTRY_AUTH_TOKEN"],
    "aws-kb-retrieval":  ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"],
    "notion":            ["NOTION_API_KEY"],
    "openai":            ["OPENAI_API_KEY"],
    "anthropic":         ["ANTHROPIC_API_KEY"],
    "jira":              ["JIRA_API_TOKEN"],
    "confluence":        ["CONFLUENCE_API_TOKEN"],
    "hubspot":           ["HUBSPOT_ACCESS_TOKEN"],
    "stripe":            ["STRIPE_SECRET_KEY"],
    "twilio":            ["TWILIO_AUTH_TOKEN"],
    "sendgrid":          ["SENDGRID_API_KEY"],
    "datadog":           ["DD_API_KEY"],
    "pagerduty":         ["PAGERDUTY_API_KEY"],
    "zendesk":           ["ZENDESK_API_TOKEN"],
    "airtable":          ["AIRTABLE_API_KEY"],
    "mongodb":           ["MONGODB_URI"],
}

# ---------------------------------------------------------------------------
# Placeholder detection
# ---------------------------------------------------------------------------
PLACEHOLDER_VALUES: frozenset[str] = frozenset({
    "your_token_here", "your_brave_api_key", "your_api_key_here",
    "xoxb-your-token", "T0XXXXXXXXX", "your_supabase_access_token",
    "your_linear_api_key", "your_sentry_auth_token",
    "your_access_key", "your_secret_key", "/path/to/credentials.json",
    "YOUR_TOKEN", "YOUR_API_KEY", "INSERT_API_KEY_HERE", "<YOUR_TOKEN>",
    "PLACEHOLDER", "placeholder", "changeme", "your-token-here",
    "your-api-key", "your-slack-bot-token", "your-slack-team-id",
    "sk-your-openai-api-key", "sk-proj-placeholder",
    "your_notion_api_key", "secret_placeholder",
})

PATH_PLACEHOLDER_VALUES: frozenset[str] = frozenset({
    "/path/to/allowed/dir", "/path/to/your/repo", "/path/to/your.db",
    "/path/to/database.db", "/path/to/your/project",
    "postgresql://user:pass@localhost/dbname",
    "postgres://user:pass@localhost/dbname",
    "/path/to/credentials.json", "/path/to/your/dir",
})

# ---------------------------------------------------------------------------
# npx packages (npm) vs uvx packages (Python/uv)
# ---------------------------------------------------------------------------
NPX_PACKAGES: list[str] = [
    "@modelcontextprotocol/server-filesystem",
    "@modelcontextprotocol/server-github",
    "@modelcontextprotocol/server-brave-search",
    "@modelcontextprotocol/server-slack",
    "@modelcontextprotocol/server-google-maps",
    "@modelcontextprotocol/server-gdrive",
    "@modelcontextprotocol/server-postgres",
    "@modelcontextprotocol/server-memory",
    "@modelcontextprotocol/server-sequential-thinking",
    "@modelcontextprotocol/server-puppeteer",
    "@modelcontextprotocol/server-aws-kb-retrieval",
]

UVX_PACKAGES: list[str] = [
    "mcp-server-git", "mcp-server-sqlite", "mcp-server-redis",
    "mcp-server-fetch", "mcp-server-time", "mcp-server-sentry",
    "mcp-server-linear", "mcp-server-supabase",
]

# ---------------------------------------------------------------------------
# Security: write-access servers
# ---------------------------------------------------------------------------
WRITE_ACCESS_SERVERS: frozenset[str] = frozenset({
    "filesystem", "github", "slack", "gdrive", "postgres",
    "postgresql", "redis", "linear", "sentry", "notion", "memory",
    "sqlite", "mcp-server-sqlite", "mcp-server-git", "git", "supabase",
    "mongodb", "mysql", "stripe", "hubspot", "jira", "confluence",
    "airtable",
})

# ---------------------------------------------------------------------------
# Security: servers with potentially broad token scopes
# ---------------------------------------------------------------------------
BROAD_SCOPE_SERVERS: dict[str, str] = {
    "github":   ("GITHUB_PERSONAL_ACCESS_TOKEN - classic PAT with repo scope grants "
                 "read+write to all repos. Consider fine-grained PATs scoped to specific repos."),
    "slack":    ("SLACK_BOT_TOKEN - verify your app OAuth scopes are minimal: "
                 "channels:read, chat:write, channels:history only."),
    "gdrive":   ("GDRIVE_CREDENTIALS_PATH - OAuth credentials may include broad Drive "
                 "access. Review scopes in Google Cloud Console."),
    "linear":   ("LINEAR_API_KEY - grants access to all teams and issues in your workspace. "
                 "No per-team scoping currently available."),
    "notion":   ("Notion integration token - grants access to all pages/databases shared "
                 "with it. Limit in Notion integration settings."),
    "supabase": ("SUPABASE_ACCESS_TOKEN - management API token grants access to all your "
                 "Supabase projects."),
    "stripe":   ("STRIPE_SECRET_KEY - grants full account access. Use restricted keys "
                 "with only the resources/permissions your MCP server needs."),
    "hubspot":  ("HUBSPOT_ACCESS_TOKEN - private app token grants access to all CRM data "
                 "for the scopes selected during setup."),
}

# ---------------------------------------------------------------------------
# Security: network-capable servers (can make outbound requests)
# ---------------------------------------------------------------------------
NETWORK_SERVERS: tuple[str, ...] = (
    "puppeteer", "playwright", "browser", "fetch", "mcp-server-fetch",
    "selenium", "webdriver", "http", "proxy", "browser-use",
    "web", "scraper", "crawler", "curl",
)

# ---------------------------------------------------------------------------
# Secret patterns: high-entropy / format-specific tokens that should never
# appear directly in args (rather than env vars).
# Each entry: (regex_pattern, human_readable_description)
# ---------------------------------------------------------------------------
SECRET_ARG_PATTERNS: list[tuple[str, str]] = [
    (r"ghp_[A-Za-z0-9]{36,}", "GitHub classic PAT"),
    (r"github_pat_[A-Za-z0-9_]{82,}", "GitHub fine-grained PAT"),
    (r"ghs_[A-Za-z0-9]{36,}", "GitHub Actions token"),
    (r"sk-[A-Za-z0-9]{48,}", "OpenAI API key"),
    (r"sk-proj-[A-Za-z0-9\-_]{50,}", "OpenAI project key"),
    (r"xoxb-[0-9]+-[A-Za-z0-9\-]+", "Slack bot token"),
    (r"xoxp-[0-9]+-[A-Za-z0-9\-]+", "Slack user token"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key ID"),
    (r"AIza[A-Za-z0-9\-_]{35}", "Google API key"),
    (r"ya29\.[A-Za-z0-9\-_]{50,}", "Google OAuth token"),
    (r"pypi-[A-Za-z0-9\-_]{50,}", "PyPI upload token"),
    (r"glpat-[A-Za-z0-9\-_]{20,}", "GitLab PAT"),
    (r"lin_api_[A-Za-z0-9]{40,}", "Linear API key"),
    (r"secret_[A-Za-z0-9]{43,}", "Notion integration token"),
    (r"dp\.pt\.[A-Za-z0-9\-_]{43,}", "DigitalOcean PAT"),
]
