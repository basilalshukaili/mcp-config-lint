"""
mcp-lint CLI entry point.

Usage:
    mcp-lint <config.json> [--json] [--strict] [--security-only] [--max-tokens N]
"""
from __future__ import annotations

import json
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from . import __version__
from .checks import Finding, Level, run_all_checks

# ANSI colour helpers (disabled when not a tty or on --json)
_RESET  = "\033[0m"
_RED    = "\033[31m"
_YELLOW = "\033[33m"
_GREEN  = "\033[32m"
_CYAN   = "\033[36m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"

_USE_COLOR = sys.stdout.isatty()


def _col(s: str, code: str) -> str:
    return f"{code}{s}{_RESET}" if _USE_COLOR else s


def _icon(level: str) -> str:
    mapping = {
        Level.ERROR:        _col("[ERROR]",    _RED),
        Level.WARNING:      _col("[WARN] ",    _YELLOW),
        Level.INFO:         _col("[INFO] ",    _CYAN),
        Level.SECURITY_HIGH:_col("[SEC:HIGH]", _RED),
        Level.SECURITY_MED: _col("[SEC:MED] ", _YELLOW),
        Level.SECURITY_LOW: _col("[SEC:LOW] ", _GREEN),
    }
    return mapping.get(level, f"[{level}]")


def _build_parser() -> ArgumentParser:
    p = ArgumentParser(
        prog="mcp-lint",
        description=(
            "Validate and security-check a claude_desktop_config.json. "
            "Exits non-zero if errors (or warnings in --strict mode) are found."
        ),
    )
    p.add_argument("config", nargs="?", help="Path to claude_desktop_config.json (default: stdin)")
    p.add_argument("--json",           action="store_true", help="Output machine-readable JSON")
    p.add_argument("--strict",         action="store_true", help="Treat warnings as failures")
    p.add_argument("--security-only",  action="store_true", help="Run security checks only")
    p.add_argument("--max-tokens",     type=int,  metavar="N",
                   help="Fail if estimated total token cost exceeds N")
    p.add_argument("--version",        action="version", version=f"mcp-lint {__version__}")
    return p


def _load_config(path_str: str | None) -> tuple[Any, str]:
    """Return (parsed_config, source_label). Raises SystemExit on failure."""
    if path_str:
        p = Path(path_str)
        if not p.exists():
            _die(f"File not found: {path_str}")
        source = str(p)
        raw = p.read_text(encoding="utf-8")
    else:
        if sys.stdin.isatty():
            _die("No config file specified and stdin is a terminal. Pass a file path or pipe JSON.")
        source = "<stdin>"
        raw = sys.stdin.read()

    try:
        return json.loads(raw), source
    except json.JSONDecodeError as exc:
        # Return a sentinel so downstream can emit a proper Finding
        return exc, source


def _die(msg: str, code: int = 1) -> None:
    print(f"mcp-lint: {msg}", file=sys.stderr)
    sys.exit(code)


def _print_human(findings: list[Finding], source: str, strict: bool) -> None:
    global _USE_COLOR

    print()
    print(_col(f"  mcp-lint  {source}", _BOLD))
    print()

    current_server: str | None = "__global__"
    for f in findings:
        server_label = f.server or "(global)"
        if server_label != current_server:
            current_server = server_label
            print(_col(f"  {current_server}", _BOLD + _CYAN))

        icon = _icon(f.level)
        print(f"    {icon}  {f.message}")
        if f.fix:
            print(_col(f"              Fix: {f.fix}", _DIM))

    print()
    errors   = [f for f in findings if f.is_error()]
    warnings = [f for f in findings if f.is_warning()]
    infos    = [f for f in findings if not f.is_error() and not f.is_warning()]

    if not errors and not warnings:
        print(_col("  All checks passed.", _GREEN + _BOLD))
    else:
        parts = []
        if errors:
            parts.append(_col(f"{len(errors)} error(s)", _RED + _BOLD))
        if warnings:
            warn_suffix = " (will fail in --strict mode)" if not strict else ""
            parts.append(_col(f"{len(warnings)} warning(s)", _YELLOW) + warn_suffix)
        print("  " + ", ".join(parts))
    print()


def _print_json(findings: list[Finding], source: str, exit_code: int) -> None:
    out = {
        "source": source,
        "exit_code": exit_code,
        "findings": [
            {
                "level":   f.level,
                "server":  f.server,
                "code":    f.code,
                "message": f.message,
                "fix":     f.fix,
            }
            for f in findings
        ],
        "summary": {
            "errors":   sum(1 for f in findings if f.is_error()),
            "warnings": sum(1 for f in findings if f.is_warning()),
            "info":     sum(1 for f in findings if not f.is_error() and not f.is_warning()),
        },
    }
    print(json.dumps(out, indent=2))


def main() -> None:
    global _USE_COLOR

    parser = _build_parser()
    args = parser.parse_args()

    if args.json:
        _USE_COLOR = False

    # --- Load & parse ---
    config_or_exc, source = _load_config(args.config)

    if isinstance(config_or_exc, Exception):
        exc = config_or_exc
        findings: list[Finding] = [Finding(
            level=Level.ERROR, server=None, code="json:parse-error",
            message=f"Invalid JSON: {exc}",
            fix=(
                "Validate at https://jsonlint.com/. Common causes: trailing comma, "
                "missing closing brace, unescaped backslash in Windows paths (use \\\\ or /)."
            ),
        )]
        exit_code = 1
    else:
        findings = run_all_checks(
            config_or_exc,
            security_only=args.security_only,
            max_tokens=args.max_tokens,
        )
        errors   = sum(1 for f in findings if f.is_error())
        warnings = sum(1 for f in findings if f.is_warning())
        exit_code = 0
        if errors > 0:
            exit_code = 1
        elif warnings > 0 and args.strict:
            exit_code = 1

    if args.json:
        _print_json(findings, source, exit_code)
    else:
        _print_human(findings, source, strict=args.strict)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
