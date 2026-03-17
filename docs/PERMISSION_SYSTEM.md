# 工具权限系统

这个目录包含了为 Bub 实现类似 Claude Code 的工具权限确认系统。

## 核心思想

**双层设计：Skill 配置 + 代码拦截**

1. **Skill 层** (`.agents/skills/tool-permission/SKILL.md`)
   - 定义哪些工具是安全的(自动批准)
   - 定义哪些工具需要确认
   - 为 LLM 提供行为指导

2. **代码层** (`src/bub/permissions.py`)
   - 真正拦截工具执行
   - 请求用户确认
   - 记住用户的选择

## 为什么不能只用 Skill？

Skill 只是**提示文本**，无法强制执行：
- ❌ LLM 可能忽略提示
- ❌ 无法技术上阻止工具执行
- ❌ 不能记住用户的权限选择

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                    LLM 决定调用工具                        │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              PermissionManager.request_permission        │
│  1. 检查 Skill 配置(是否在 auto_approved 列表)            │
│  2. 检查工具类型(read/write/delete 等)                   │
│  3. 如果需要确认 → 调用 prompt_user()                     │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   用户确认界面                            │
│  - CLI: input()                                         │
│  - Web: WebSocket                                       │
│  - Telegram: Bot message                                │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              批准 → 执行工具                              │
│              拒绝 → 返回错误消息                          │
└─────────────────────────────────────────────────────────┘
```

## 使用方法

### 1. 配置 Skill

编辑 `.agents/skills/tool-permission/SKILL.md`:

```yaml
---
name: tool-permission
description: Tool permission configuration
metadata:
  auto_approved:
    - read
    - search
    - list
  always_ask:
    - write
    - delete
    - bash
---
```

### 2. 在 Agent 中集成

```python
from bub.permissions import PermissionManager, PermissionMode
from bub.permission_decorator import add_permission_check
from bub.tools import REGISTRY

# 创建权限管理器
permission_manager = PermissionManager(
    mode=PermissionMode.SKILL_BASED,
    workspace=Path.cwd()
)

# 为所有工具添加权限检查
for tool_name, tool in REGISTRY.items():
    if not permission_manager._is_safe_tool(tool_name):
        REGISTRY[tool_name] = add_permission_check(
            tool,
            permission_manager,
            your_prompt_user_function
        )
```

### 3. 实现用户确认界面

```python
async def prompt_user(request: ToolCallRequest) -> tuple[bool, str]:
    """根据你的 UI 实现用户确认."""
    # CLI 版本
    print(f"Tool: {request.tool_name}")
    print(f"Args: {request.args}")
    response = input("Approve? [y/n/always/never]: ")

    if response == "y":
        return True, "approve"
    elif response == "always":
        return True, "always"
    else:
        return False, "deny"
```

## 权限模式

- `AUTO`: 自动批准所有工具(开发模式)
- `ASK`: 每次都询问用户
- `SKILL_BASED`: 根据 Skill 配置决定(推荐)

## 集成到现有代码

在 `src/bub/builtin/agent.py` 的 `Agent.__init__()` 中：

```python
def __init__(self, framework: BubFramework) -> None:
    self.settings = _load_runtime_settings()
    self.framework = framework

    # 添加权限系统
    self.permission_manager = PermissionManager(
        mode=PermissionMode.SKILL_BASED,
        workspace=Path.cwd()
    )
    self._wrap_tools_with_permission()

def _wrap_tools_with_permission(self):
    """为工具添加权限检查."""
    from bub.permission_decorator import add_permission_check

    for tool_name, tool in REGISTRY.items():
        if not self.permission_manager._is_safe_tool(tool_name):
            REGISTRY[tool_name] = add_permission_check(
                tool,
                self.permission_manager,
                self._prompt_user_for_permission
            )
```

## 示例

查看 `examples/` 目录中的完整示例：
- `permission_example.py` - 基础用法
- `permission_agent_example.py` - 完整集成示例

## 优势

✅ **灵活**: 通过 Skill 配置，无需修改代码
✅ **安全**: 代码层面强制执行，LLM 无法绕过
✅ **用户友好**: 记住用户选择，减少重复确认
✅ **可扩展**: 支持不同的 UI 实现(CLI/Web/Bot)
