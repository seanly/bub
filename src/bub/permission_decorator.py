"""Permission-aware tool decorator."""

import inspect
from dataclasses import replace
from typing import Callable

from republic import Tool, ToolContext

from bub.permissions import PermissionManager, ToolCallRequest, prompt_user_cli


def add_permission_check(tool_instance: Tool) -> Tool:
    """
    为 Tool 实例添加权限检查.

    权限管理器从 ToolContext.state["_permission_manager"] 获取。
    """
    if tool_instance.handler is None:
        return tool_instance

    original_handler = tool_instance.handler

    async def permission_wrapper(*args, **kwargs):
        # 获取 context
        context = kwargs.get("context") if tool_instance.context else None

        # 如果没有 context 或没有权限管理器，直接执行
        if context is None or "_permission_manager" not in context.state:
            result = original_handler(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result
            return result

        permission_manager: PermissionManager = context.state["_permission_manager"]

        # 移除 context 参数用于显示
        call_kwargs = kwargs.copy()
        if tool_instance.context:
            call_kwargs.pop("context", None)

        # 创建权限请求
        request = ToolCallRequest(
            tool_name=tool_instance.name,
            args=args,
            kwargs=call_kwargs,
        )

        # 请求权限
        approved, action = await permission_manager.request_permission(
            request, prompt_user_cli
        )

        if not approved:
            return f"❌ Permission denied: User rejected {tool_instance.name}"

        # 更新权限设置
        if action in ["always", "never"]:
            permission_manager.update_permission(tool_instance.name, action)

        # 执行原函数
        result = original_handler(*args, **kwargs)
        if inspect.isawaitable(result):
            result = await result
        return result

    return replace(tool_instance, handler=permission_wrapper)
