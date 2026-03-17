"""Simple shell executor that inherits the current process environment.

Executes commands using the user's shell with their configuration loaded.
"""

from __future__ import annotations

import asyncio
import os


_USER_SHELL = os.environ.get("SHELL", "/bin/sh")


async def execute(
    cmd: str,
    cwd: str | None = None,
    timeout: float = 30.0,
) -> tuple[str, int]:
    """Execute a command using the current user's shell, inheriting all env vars.

    Uses interactive shell mode to load user's configuration (.zshrc, .bashrc, etc).

    Returns (output, exit_code).
    """
    # 使用 -i -c 来加载用户的配置文件
    # -i: 交互模式，会加载 .zshrc 或 .bashrc
    # -c: 执行命令后退出
    process = await asyncio.create_subprocess_exec(
        _USER_SHELL, "-i", "-c", cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=cwd,
        env=os.environ.copy(),
    )

    try:
        async with asyncio.timeout(timeout):
            stdout, _ = await process.communicate()
    except TimeoutError:
        process.kill()
        await process.wait()
        return f"Command timed out after {timeout} seconds", -1

    output = stdout.decode("utf-8", errors="replace").strip() if stdout else ""
    return output, process.returncode or 0
