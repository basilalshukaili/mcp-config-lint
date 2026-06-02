"""
Tests for mcp_lint.checks — the core audit engine.
"""
import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest

from mcp_lint.checks import (
    Finding,
    Level,
    check_security,
    check_server,
    check_structure,
    check_token_cost,
    run_all_checks,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _codes(findings):
    return {f.code for f in findings}


def _has_level(findings, level):
    return any(f.level == level for f in findings)


def _errors(findings):
    return [f for f in findings if f.is_error()]


def _warnings(findings):
    return [f for f in findings if f.is_warning()]


# ---------------------------------------------------------------------------
# check_structure
# ---------------------------------------------------------------------------

class TestCheckStructure:
    def test_valid_config_no_findings(self):
        config = {"mcpServers": {"github": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"], "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_realtoken"}}}}
        findings = check_structure(config)
        assert not _errors(findings)

    def test_not_object(self):
        findings = check_structure([1, 2, 3])
        assert "structure:not-object" in _codes(findings)

    def test_missing_mcp_servers(self):
        findings = check_structure({"foo": "bar"})
        assert "structure:missing-mcp-servers" in _codes(findings)

    def test_mcp_servers_not_object(self):
        findings = check_structure({"mcpServers": ["bad"]})
        assert "structure:mcp-servers-not-object" in _codes(findings)

    def test_empty_mcp_servers_is_warning(self):
        findings = check_structure({"mcpServers": {}})
        assert _has_level(findings, Level.WARNING)
        assert "structure:empty" in _codes(findings)

    def test_scalar_root(self):
        findings = check_structure("just a string")
        assert _errors(findings)


# ---------------------------------------------------------------------------
# check_server — command / args
# ---------------------------------------------------------------------------

class TestCheckServerBasics:
    def test_missing_command(self):
        cfg = {"args": ["-y", "@modelcontextprotocol/server-github"],
               "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_real"}}
        findings = check_server("github", cfg)
        assert "server:missing-command" in _codes(findings)

    def test_missing_args(self):
        cfg = {"command": "npx", "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_real"}}
        findings = check_server("github", cfg)
        assert "server:missing-args" in _codes(findings)

    def test_empty_args(self):
        cfg = {"command": "npx", "args": [],
               "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_real"}}
        findings = check_server("github", cfg)
        assert "server:missing-args" in _codes(findings)

    def test_server_not_object(self):
        findings = check_server("foo", "bad")
        assert "server:not-object" in _codes(findings)


# ---------------------------------------------------------------------------
# check_server — command/runtime mismatch
# ---------------------------------------------------------------------------

class TestCommandMismatch:
    def test_uvx_for_npm_package(self):
        cfg = {"command": "uvx",
               "args": ["-y", "@modelcontextprotocol/server-github"],
               "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_real"}}
        findings = check_server("github", cfg)
        assert "server:cmd-mismatch-uvx-for-npm" in _codes(findings)

    def test_npx_for_uv_package(self):
        cfg = {"command": "npx",
               "args": ["mcp-server-git"]}
        findings = check_server("git", cfg)
        assert "server:cmd-mismatch-npx-for-uv" in _codes(findings)

    def test_correct_npx(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-github"],
               "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_real"}}
        findings = check_server("github", cfg)
        mismatch = [f for f in findings if "mismatch" in f.code]
        assert not mismatch

    def test_correct_uvx(self):
        cfg = {"command": "uvx",
               "args": ["mcp-server-git"]}
        findings = check_server("git", cfg)
        mismatch = [f for f in findings if "mismatch" in f.code]
        assert not mismatch


# ---------------------------------------------------------------------------
# check_server — required env vars
# ---------------------------------------------------------------------------

class TestRequiredEnv:
    def test_missing_github_token(self):
        # env key present but token not in it -> server:missing-env-var
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-github"],
               "env": {"SOME_OTHER_KEY": "val"}}
        findings = check_server("github", cfg)
        assert "server:missing-env-var" in _codes(findings)

    def test_missing_env_object(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-github"]}
        findings = check_server("github", cfg)
        assert "server:missing-env-object" in _codes(findings)

    def test_placeholder_env_var(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-github"],
               "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"}}
        findings = check_server("github", cfg)
        assert "server:placeholder-env-var" in _codes(findings)

    def test_valid_token(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-github"],
               "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_realtoken123"}}
        findings = check_server("github", cfg)
        env_errors = [f for f in findings if "env" in f.code and f.is_error()]
        assert not env_errors

    def test_slack_requires_two_vars(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-slack"],
               "env": {"SLACK_BOT_TOKEN": "xoxb-real", "SLACK_TEAM_ID": "T0XXXXXXXXX"}}
        findings = check_server("slack", cfg)
        # SLACK_TEAM_ID still has a placeholder
        assert any(f.code == "server:placeholder-env-var" for f in findings)

    def test_aws_requires_three_vars(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-aws-kb-retrieval"],
               "env": {"AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
                       "AWS_SECRET_ACCESS_KEY": "realkey",
                       "AWS_REGION": "us-east-1"}}
        findings = check_server("aws-kb-retrieval", cfg)
        env_errors = [f for f in findings if "env" in f.code and f.is_error()]
        assert not env_errors


# ---------------------------------------------------------------------------
# check_server — placeholder args
# ---------------------------------------------------------------------------

class TestPlaceholderArgs:
    def test_path_placeholder_in_args(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-filesystem",
                        "/path/to/allowed/dir"]}
        findings = check_server("filesystem", cfg)
        assert "server:placeholder-arg" in _codes(findings)

    def test_valid_path_no_finding(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-filesystem",
                        "/home/user/projects"]}
        findings = check_server("filesystem", cfg)
        placeholder_arg = [f for f in findings if f.code == "server:placeholder-arg"]
        assert not placeholder_arg


# ---------------------------------------------------------------------------
# Per-server gotchas
# ---------------------------------------------------------------------------

class TestPerServerGotchas:
    def test_filesystem_relative_path(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-filesystem", "projects/"]}
        findings = check_server("filesystem", cfg)
        assert "gotcha:filesystem-relative-path" in _codes(findings)

    def test_postgres_wrong_prefix(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-postgres",
                        "postgres://user:realpass@localhost/mydb"]}
        findings = check_server("postgres", cfg)
        assert "gotcha:postgres-prefix" in _codes(findings)

    def test_postgres_creds_in_args(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-postgres",
                        "postgresql://admin:s3cr3t@prod.db.example.com/mydb"]}
        findings = check_server("postgres", cfg)
        assert "gotcha:postgres-creds-in-args" in _codes(findings)

    def test_github_fine_grained_pat_warning(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-github"],
               "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "github_pat_ABCDEFG"}}
        findings = check_server("github", cfg)
        assert "gotcha:github-fine-grained-pat" in _codes(findings)

    def test_brave_quota_info(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-brave-search"],
               "env": {"BRAVE_API_KEY": "BSA-real-abc123"}}
        findings = check_server("brave-search", cfg)
        assert "gotcha:brave-search-quota" in _codes(findings)


# ---------------------------------------------------------------------------
# Security checks
# ---------------------------------------------------------------------------

class TestSecurityChecks:
    def test_write_access_flagged(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-github"],
               "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_real"}}
        findings = check_security("github", cfg)
        assert "sec:write-access" in _codes(findings)

    def test_broad_scope_flagged(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-github"],
               "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_real"}}
        findings = check_security("github", cfg)
        assert "sec:broad-scope" in _codes(findings)

    def test_classic_github_pat(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-github"],
               "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_realtoken"}}
        findings = check_security("github", cfg)
        assert "sec:classic-github-pat" in _codes(findings)

    def test_aws_key_in_config(self):
        cfg = {"command": "uvx",
               "args": ["mcp-server-aws"],
               "env": {"AWS_ACCESS_KEY_ID": "AKIAREALKEY123456"}}
        findings = check_security("aws-kb-retrieval", cfg)
        assert "sec:aws-key-in-config" in _codes(findings)

    def test_bind_all_interfaces(self):
        cfg = {"command": "uvx",
               "args": ["mcp-server-custom", "--host=0.0.0.0"]}
        findings = check_security("custom", cfg)
        assert "sec:bind-all-interfaces" in _codes(findings)

    def test_wildcard_cors(self):
        cfg = {"command": "uvx",
               "args": ["mcp-server-custom", "cors=*"]}
        findings = check_security("custom", cfg)
        assert "sec:wildcard-cors" in _codes(findings)

    def test_filesystem_root_path(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-filesystem", "/"]}
        findings = check_security("filesystem", cfg)
        assert "sec:filesystem-root-path" in _codes(findings)

    def test_filesystem_home_directory(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/basil"]}
        findings = check_security("filesystem", cfg)
        assert "sec:filesystem-home-path" in _codes(findings)

    def test_network_capable_server(self):
        cfg = {"command": "uvx", "args": ["mcp-server-fetch"]}
        findings = check_security("fetch", cfg)
        assert "sec:network-capable" in _codes(findings)

    def test_db_creds_in_args(self):
        cfg = {"command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-postgres",
                        "postgresql://admin:s3cr3t@prod.db.example.com/mydb"]}
        findings = check_security("postgres", cfg)
        assert "sec:db-creds-in-args" in _codes(findings)

    def test_clean_server_no_write_access(self):
        cfg = {"command": "uvx",
               "args": ["mcp-server-time"]}
        findings = check_security("time", cfg)
        assert "sec:write-access" not in _codes(findings)


# ---------------------------------------------------------------------------
# Token cost checks
# ---------------------------------------------------------------------------

class TestTokenCost:
    def test_heavy_server_detected(self):
        servers = {"github": {"command": "npx",
                              "args": ["-y", "@modelcontextprotocol/server-github"],
                              "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_real"}}}
        findings = check_token_cost(servers, max_tokens=None)
        # Should have at least one token estimate INFO
        token_infos = [f for f in findings if f.code.startswith("token:estimate")]
        assert token_infos

    def test_max_tokens_exceeded(self):
        servers = {
            "github": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"],
                       "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_real"}},
            "linear": {"command": "npx", "args": ["-y"], "env": {"LINEAR_API_KEY": "lin_real"}},
        }
        findings = check_token_cost(servers, max_tokens=10_000)
        assert "token:exceeds-max" in _codes(findings)
        assert any(f.is_error() for f in findings if f.code == "token:exceeds-max")

    def test_max_tokens_not_exceeded(self):
        servers = {"time": {"command": "uvx", "args": ["mcp-server-time"]}}
        findings = check_token_cost(servers, max_tokens=100_000)
        assert "token:exceeds-max" not in _codes(findings)

    def test_danger_threshold_warning(self):
        # github(50k) + linear(32k) > 50k threshold -> high context tax
        servers = {
            "github": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"],
                       "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_real"}},
            "linear": {"command": "npx", "args": [], "env": {"LINEAR_API_KEY": "lin_real"}},
        }
        findings = check_token_cost(servers, max_tokens=None)
        assert "token:high-context-tax" in _codes(findings)


# ---------------------------------------------------------------------------
# run_all_checks integration
# ---------------------------------------------------------------------------

class TestRunAllChecks:
    def test_bad_config_returns_errors(self):
        bad = {
            "mcpServers": {
                "github": {
                    "command": "uvx",  # wrong - should be npx
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"},  # placeholder
                }
            }
        }
        findings = run_all_checks(bad)
        assert _errors(findings) or _warnings(findings)

    def test_good_config_no_errors(self):
        good = {
            "mcpServers": {
                "time": {
                    "command": "uvx",
                    "args": ["mcp-server-time"],
                }
            }
        }
        findings = run_all_checks(good)
        assert not _errors(findings)

    def test_security_only_skips_structural_checks(self):
        config = {
            "mcpServers": {
                "github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_real"},
                }
            }
        }
        findings = run_all_checks(config, security_only=True)
        # No server:missing-args etc — only security codes
        non_sec = [f for f in findings if not f.is_security() and f.server is not None]
        assert not non_sec

    def test_invalid_structure_stops_early(self):
        findings = run_all_checks({"notMcpServers": {}})
        # Should get structure error, nothing else
        assert any(f.code == "structure:missing-mcp-servers" for f in findings)

    def test_max_tokens_triggers_error(self):
        config = {
            "mcpServers": {
                "github": {"command": "npx",
                           "args": ["-y", "@modelcontextprotocol/server-github"],
                           "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_real"}},
            }
        }
        findings = run_all_checks(config, max_tokens=100)
        assert "token:exceeds-max" in _codes(findings)


# ---------------------------------------------------------------------------
# CLI integration tests (subprocess)
# ---------------------------------------------------------------------------

class TestCLIIntegration:
    def _run(self, config_dict, *extra_args):
        """Run mcp-lint on a JSON string and return (returncode, stdout, stderr)."""
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_dict, f)
            fname = f.name
        try:
            result = subprocess.run(
                [sys.executable, "-m", "mcp_lint.cli", fname] + list(extra_args),
                capture_output=True, text=True,
            )
            return result.returncode, result.stdout, result.stderr
        finally:
            os.unlink(fname)

    def test_good_config_exits_zero(self):
        good = {"mcpServers": {"time": {"command": "uvx", "args": ["mcp-server-time"]}}}
        rc, out, _ = self._run(good)
        assert rc == 0

    def test_bad_config_exits_nonzero(self):
        bad = {
            "mcpServers": {
                "github": {
                    "command": "uvx",  # mismatch
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"},
                }
            }
        }
        rc, out, _ = self._run(bad)
        assert rc != 0

    def test_json_output_is_valid_json(self):
        good = {"mcpServers": {"time": {"command": "uvx", "args": ["mcp-server-time"]}}}
        rc, out, _ = self._run(good, "--json")
        data = json.loads(out)
        assert "findings" in data
        assert "summary" in data
        assert "exit_code" in data

    def test_strict_makes_warnings_fail(self):
        # A config with only warnings (placeholder token)
        config = {
            "mcpServers": {
                "github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"},
                }
            }
        }
        rc_normal, _, _ = self._run(config)
        rc_strict, _, _ = self._run(config, "--strict")
        # Without strict: warnings don't fail (errors might still fail)
        # With strict: should definitely fail (has warnings + errors)
        assert rc_strict != 0

    def test_security_only_flag(self):
        config = {
            "mcpServers": {
                "github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_real"},
                }
            }
        }
        rc, out, _ = self._run(config, "--security-only", "--json")
        data = json.loads(out)
        findings = data["findings"]
        # Should only have security findings (plus global structure OK)
        non_sec_server = [f for f in findings if f["server"] is not None
                          and not f["code"].startswith("sec:")]
        assert not non_sec_server

    def test_invalid_json_file_exits_nonzero(self):
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{this is not valid json,,,}")
            fname = f.name
        try:
            result = subprocess.run(
                [sys.executable, "-m", "mcp_lint.cli", fname],
                capture_output=True, text=True,
            )
            assert result.returncode != 0
        finally:
            os.unlink(fname)

    def test_nonexistent_file_exits_nonzero(self):
        result = subprocess.run(
            [sys.executable, "-m", "mcp_lint.cli", "/nonexistent/path/config.json"],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
