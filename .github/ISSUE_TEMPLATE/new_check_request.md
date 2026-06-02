---
name: New check request
about: Propose a new lint rule or server-specific check
title: ''
labels: enhancement
assignees: ''
---

**What server or error class does this cover?**

e.g. "Supabase", "filesystem", "any server with a database URL"

**What config mistake does it catch?**

Describe the real-world misconfiguration. Include an example config snippet.

```json
{
  "mcpServers": {
    "example": {
      "command": "...",
      "args": ["..."],
      "env": {}
    }
  }
}
```

**What goes wrong when this mistake is present?**

e.g. "server silently fails to start", "credentials are exposed in process list", "Claude gets write access it shouldn't have"

**Suggested fix message**

What should the `fix:` field say to help users resolve the issue?

**Suggested level**

- `ERROR` — always fails CI (definite breakage)
- `WARNING` — fails CI in `--strict` mode (likely wrong)
- `INFO` — advisory only
- `SECURITY_HIGH` / `SECURITY_MED` / `SECURITY_LOW`

**Sources / references**

Link to MCP server docs, GitHub issues, community discussions, or personal experience.
