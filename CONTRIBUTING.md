# Contributing to mcp-config-lint

Thank you for helping make MCP configs safer and more reliable.

## Ways to contribute

- **New server checks**: MCP has a long tail of community servers — real-world gotchas are welcome.
- **Security rules**: Pattern-match bugs, credential leaks, dangerous configurations.
- **Bug reports**: If a check fires incorrectly (false positive) or misses a real issue, open an issue.
- **Token estimates**: Better data on how many tokens specific MCP servers consume.

## Development setup

```bash
git clone https://github.com/basilalshukaili/mcp-config-lint.git
cd mcp-config-lint

# Create a virtual environment and install in editable mode
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"            # or: pip install -e . && pip install pytest
```

Run the tests:

```bash
pytest -v
```

Run the linter on itself:

```bash
mcp-config-lint --help
```

## Adding a new check

All checks live in `src/mcp_lint/checks.py`. Static data (token estimates, required env vars, etc.) lives in `src/mcp_lint/data.py`.

### Checklist for a new rule

1. **Is this a real error class?** It should fire on configs that users actually ship and cause real pain (silent failure, security exposure, incorrect setup).
2. **Add the check** in `checks.py` — either in `check_server`, `_per_server_gotchas`, `check_security`, or `check_structure`.
3. **Choose the right level**:
   - `ERROR` / `SECURITY_HIGH`: Always blocks CI. Use for definite breakage or serious credential exposure.
   - `WARNING` / `SECURITY_MED`: Blocks CI in `--strict` mode. Use for likely-wrong configurations.
   - `INFO` / `SECURITY_LOW`: Never blocks CI. Use for cost/scope awareness.
4. **Use a namespaced code**: `gotcha:<server>-<thing>`, `sec:<thing>`, `server:<thing>`, `structure:<thing>`, `token:<thing>`.
5. **Write a pytest test** in `tests/test_checks.py`. The test should verify the code fires on a config that triggers it and does NOT fire on a clean config.
6. **Run the full test suite** before opening a PR — `pytest -v` must be green.

### Adding a new server to `REQUIRED_ENV`

In `src/mcp_lint/data.py`, add an entry to `REQUIRED_ENV`:

```python
"my-server": ["MY_SERVER_API_KEY"],
```

Then add a test that verifies the check fires when the key is absent.

### Adding a token estimate

In `src/mcp_lint/data.py`, add an entry to `TOKEN_ESTIMATES`:

```python
"my-server": {
    "tokens": 8000,
    "tier": "medium",
    "note": "Brief explanation of what tools this server exposes.",
},
```

Token estimates should be based on actual measurements where possible, or conservative estimates otherwise.

## Code style

- Python 3.9+ compatible (no `match` statements, no `3.10+`-only syntax).
- Zero third-party runtime dependencies — keep it that way.
- Type annotations on all public functions.
- Docstrings are optional but appreciated for non-obvious logic.

## Pull request process

1. Fork the repo, create a feature branch.
2. Run `pytest -v` — all tests must pass.
3. Open a PR with a clear description of what the new check catches and why it matters.
4. Link any relevant MCP server docs or community reports that motivated the check.

## Reporting a false positive

If a check fires on a valid config, please open an issue with:
- The finding code (e.g. `sec:write-access`)
- A minimal config snippet that triggers it
- Why you believe it should not fire

## License

By contributing, you agree that your contributions will be licensed under the MIT license.
