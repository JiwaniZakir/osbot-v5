from __future__ import annotations

import asyncio
import json
from typing import Any

from osbot.log import get_logger
from osbot.types import CLIResult

logger = get_logger(__name__)


class GitHubCLI:
    async def run_cmd(self, cmd: list[str], cwd: str | None = None, timeout: float = 60.0) -> CLIResult:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            result = CLIResult(
                returncode=proc.returncode or 0,
                stdout=stdout_bytes.decode("utf-8", errors="replace").strip(),
                stderr=stderr_bytes.decode("utf-8", errors="replace").strip(),
            )
        except TimeoutError:
            logger.warning("cmd_timeout", cmd=cmd[:3], timeout=timeout)
            result = CLIResult(returncode=1, stdout="", stderr="timeout")
        except Exception as exc:
            logger.error("cmd_error", cmd=cmd[:3], error=str(exc))
            result = CLIResult(returncode=1, stdout="", stderr=str(exc))
        return result

    async def run_gh(self, args: list[str], cwd: str | None = None) -> CLIResult:
        return await self.run_cmd(["gh", *args], cwd=cwd)

    async def run_git(self, args: list[str], cwd: str | None = None) -> CLIResult:
        return await self.run_cmd(["git", *args], cwd=cwd)

    async def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"query": query}
        if variables:
            body["variables"] = variables
        result = await self.run_gh(["api", "graphql", "-f", f"query={query}"] + self._var_args(variables))
        if not result.success:
            logger.error("graphql_error", stderr=result.stderr[:200])
            return {}
        try:
            parsed: dict[str, Any] = json.loads(result.stdout)
            return parsed
        except json.JSONDecodeError:
            logger.error("graphql_json_error", stdout=result.stdout[:200])
            return {}

    @staticmethod
    def _var_args(variables: dict[str, Any] | None) -> list[str]:
        if not variables:
            return []
        args: list[str] = []
        for key, val in variables.items():
            args.extend(["-f", f"{key}={val}"])
        return args
