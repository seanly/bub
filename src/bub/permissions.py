"""Tool permission management system."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Awaitable

import yaml


class PermissionMode(Enum):
    """Permission modes for tool execution."""

    AUTO = "auto"  # 自动批准所有工具
    ASK = "ask"  # 每次都询问
    SKILL_BASED = "skill_based"  # 基于 skill 配置


@dataclass
class ToolCallRequest:
    """Represents a tool call that needs permission."""

    tool_name: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


class PermissionManager:
    """Manages tool execution permissions."""

    def __init__(
        self,
        mode: PermissionMode = PermissionMode.ASK,
        workspace: Path | None = None,
    ):
        self.mode = mode
        self.workspace = workspace
        self.auto_approved_tools: set[str] = set()
        self.always_ask_tools: set[str] = set()
        self._load_skill_config()

    def _load_skill_config(self) -> None:
        """从 skill 配置中加载权限规则."""
        if not self.workspace:
            return

        skill_file = self.workspace / ".agents" / "skills" / "tool-permission" / "SKILL.md"
        if not skill_file.exists():
            return

        try:
            content = skill_file.read_text(encoding="utf-8")
            # 解析 frontmatter 中的配置
            config = self._parse_permission_config(content)
            if config:
                self.auto_approved_tools = set(config.get("auto_approved", []))
                self.always_ask_tools = set(config.get("always_ask", []))
        except Exception:
            pass

    def _parse_permission_config(self, content: str) -> dict[str, Any] | None:
        """解析 SKILL.md 中的权限配置."""
        lines = content.splitlines()
        if not lines or lines[0].strip() != "---":
            return None

        for idx, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                payload = "\n".join(lines[1:idx])
                try:
                    parsed = yaml.safe_load(payload)
                    if isinstance(parsed, dict):
                        return parsed.get("metadata", {})
                except yaml.YAMLError:
                    pass
        return None

    async def request_permission(
        self,
        request: ToolCallRequest,
        prompt_user: Callable[[ToolCallRequest], Awaitable[tuple[bool, str]]],
    ) -> tuple[bool, str]:
        """
        请求执行工具的权限.

        Returns:
            (approved, action) where action is one of: "approve", "deny", "always", "never"
        """
        if self.mode == PermissionMode.AUTO:
            return True, "approve"

        # 检查是否在自动批准列表中
        if request.tool_name in self.auto_approved_tools:
            return True, "approve"

        # 基于 skill 的模式
        if self.mode == PermissionMode.SKILL_BASED:
            if self._is_safe_tool(request.tool_name):
                return True, "approve"

        # 询问用户
        return await prompt_user(request)

    def _is_safe_tool(self, tool_name: str) -> bool:
        """判断工具是否安全(不需要确认)."""
        safe_prefixes = ["read", "search", "list", "get", "find", "fs.read", "tape.info", "tape.search", "help"]
        return any(tool_name.startswith(prefix) or tool_name == prefix for prefix in safe_prefixes)

    def update_permission(self, tool_name: str, action: str) -> None:
        """根据用户的选择更新权限."""
        if action == "always":
            self.auto_approved_tools.add(tool_name)
        elif action == "never":
            # 可以添加到黑名单
            pass


async def prompt_user_cli(request: ToolCallRequest) -> tuple[bool, str]:
    """
    CLI 用户确认界面.

    使用 prompt_toolkit 来获取用户输入，兼容 bub 的 CLI 环境。
    """
    from prompt_toolkit import PromptSession

    # 构建参数显示
    params_lines = []
    if request.kwargs:
        for key, value in request.kwargs.items():
            params_lines.append(f"  {key} = {_format_value(value, max_length=60)}")

    params_text = "\n".join(params_lines) if params_lines else "  (no parameters)"

    # 清晰的权限提示
    print(f"\n{'='*60}")
    print(f"🔧 Tool Permission Request")
    print(f"{'='*60}")
    print(f"Tool: {request.tool_name}")
    print(f"\nParameters:")
    print(params_text)
    print(f"\nOptions:")
    print("  y/yes    → Approve this time")
    print("  n/no     → Deny this time")
    print("  always   → Always approve this tool")
    print("  never    → Always deny this tool")
    print(f"{'='*60}")

    # 使用 prompt_toolkit 获取输入
    session = PromptSession()
    try:
        response = await session.prompt_async("Your choice: ")
        response = response.strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("✗ Cancelled\n")
        return False, "deny"

    if response in ["y", "yes"]:
        print("✓ Approved\n")
        return True, "approve"
    elif response == "always":
        print(f"✓ Will always approve '{request.tool_name}'\n")
        return True, "always"
    elif response == "never":
        print(f"✗ Will always deny '{request.tool_name}'\n")
        return False, "never"
    else:
        print("✗ Denied\n")
        return False, "deny"


def _format_value(value: Any, max_length: int = 100) -> str:
    """格式化参数值用于显示."""
    s = str(value)
    if len(s) > max_length:
        return s[:max_length] + "..."
    return s
