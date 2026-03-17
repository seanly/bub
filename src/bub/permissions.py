"""Tool permission management system."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Awaitable

import yaml


class StopRequestException(BaseException):
    """Raised when user wants to stop the current request but keep the conversation.

    Inherits from BaseException (not Exception) to avoid being caught by
    generic exception handlers in the tool execution chain.
    """
    pass


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
        self._request_stopped = False  # 标记用户是否停止了当前请求
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
        # 如果用户已经停止了请求，直接抛出异常
        if self._request_stopped:
            raise StopRequestException("Request already stopped by user")

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
        try:
            result = await prompt_user(request)
            return result
        except StopRequestException:
            # 用户选择停止，设置标志并重新抛出
            self._request_stopped = True
            raise

    def reset_stop_flag(self) -> None:
        """重置停止标志，用于新的用户请求."""
        self._request_stopped = False

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
    CLI 用户确认界面 (使用 Questionary).

    使用 Questionary 提供美观的交互式选择界面。
    """
    import sys
    import questionary
    from questionary import Style

    # 构建参数显示
    params_lines = []
    # 从环境变量读取最大宽度，默认 0（不截断）
    max_width = int(os.getenv("BUB_LOG_MAX_WIDTH", "0"))
    if request.kwargs:
        for key, value in request.kwargs.items():
            if max_width > 0:
                params_lines.append(f"  {key} = {_format_value(value, max_length=max_width)}")
            else:
                params_lines.append(f"  {key} = {_format_value(value, max_length=None)}")

    params_text = "\n".join(params_lines) if params_lines else "  (no parameters)"

    # 显示权限请求信息
    print()
    print("=" * 60)
    print("🔧 Tool Permission Request")
    print("=" * 60)
    print(f"Tool: {request.tool_name}")
    print("\nParameters:")
    print(params_text)
    print("=" * 60)
    print()

    # 自定义样式
    custom_style = Style([
        ('qmark', 'fg:#673ab7 bold'),       # 问号
        ('question', 'bold'),                # 问题文本
        ('answer', 'fg:#f44336 bold'),       # 答案
        ('pointer', 'fg:#673ab7 bold'),      # 指针
        ('highlighted', 'fg:#673ab7 bold'),  # 高亮选项
        ('selected', 'fg:#cc5454'),          # 已选择
        ('separator', 'fg:#cc5454'),         # 分隔符
        ('instruction', ''),                 # 指令
        ('text', ''),                        # 普通文本
    ])

    try:
        # 使用 Questionary 的 select 创建选择菜单
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: questionary.select(
                "Do you want to approve this tool call?",
                choices=[
                    questionary.Choice("Yes - Approve this time", value="approve"),
                    questionary.Choice("No - Deny this time", value="deny"),
                    questionary.Choice("Stop - End current request", value="stop"),
                ],
                default="approve",
                style=custom_style,
                use_shortcuts=True,
                use_arrow_keys=True,
            ).ask()
        )

        if result == "approve":
            print("✓ Approved\n")
            return True, "approve"
        elif result == "deny":
            print("✗ Denied\n")
            return False, "deny"
        elif result == "stop":
            print("\n✗ Request stopped by user\n")
            # 抛出特殊异常来停止当前请求
            import sys
            print(f"DEBUG: Raising StopRequestException", file=sys.stderr)
            raise StopRequestException("User stopped the current request")
        else:
            # 用户取消（Ctrl+C 或 result 为 None）
            print("\n✗ Cancelled\n")
            raise KeyboardInterrupt("User cancelled")

    except StopRequestException:
        # 重新抛出，让上层处理
        raise
    except KeyboardInterrupt:
        # 重新抛出，让上层处理
        raise
    except (EOFError, Exception) as e:
        # 捕获其他异常
        print(f"\n✗ Cancelled ({type(e).__name__})\n")
        raise KeyboardInterrupt("Permission prompt failed")


def _format_value(value: Any, max_length: int | None = 100) -> str:
    """格式化参数值用于显示."""
    s = str(value)
    if max_length is not None and max_length > 0 and len(s) > max_length:
        return s[:max_length] + "..."
    return s
