# 权限系统 - 已完成！

## ✅ 实现完成

工具权限系统已经完全实现并可以正常使用！

## 🎯 功能特性

### 自动权限检查

以下工具在执行前会请求用户确认：
- `fs.write` - 写入文件
- `fs.edit` - 编辑文件
- `bash` - 执行 shell 命令
- `bash.kill` - 终止后台进程
- `tape.reset` - 重置对话历史
- `tape.handoff` - 添加交接点

### 自动批准（安全操作）

以下工具会自动批准，无需确认：
- `fs.read` - 读取文件
- `tape.info` - 查看对话信息
- `tape.search` - 搜索对话历史
- `tape.anchors` - 列出锚点
- `help` - 显示帮助

## 📝 使用方法

### 启动 Bub

```bash
uv run bub chat
```

### 执行需要权限的操作

```
bub > write a file, output hello world
```

### 权限提示界面

```
============================================================
🔧 Tool Permission Request
============================================================
Tool: fs.write

Parameters:
  path = hello.txt
  content = hello world

Options:
  y/yes    → Approve this time
  n/no     → Deny this time
  always   → Always approve this tool
  never    → Always deny this tool
============================================================
Your choice: _
```

### 输入选项

- **y** 或 **yes** - 批准这次操作
- **n** 或 **no** - 拒绝这次操作
- **always** - 以后总是批准这个工具（本次会话）
- **never** - 以后总是拒绝这个工具（本次会话）
- **直接回车** - 默认拒绝

## ⚙️ 配置

### 通过 Skill 配置默认规则

编辑 `.agents/skills/tool-permission/SKILL.md`：

```yaml
---
name: tool-permission
description: Tool permission configuration
metadata:
  # 自动批准的工具
  auto_approved:
    - fs.read
    - tape.info
    - tape.search

  # 总是需要确认的工具
  always_ask:
    - fs.write
    - fs.edit
    - bash
---
```

### 添加更多需要权限的工具

编辑 `src/bub/builtin/agent.py` 中的 `_wrap_tools_with_permission` 方法：

```python
def _wrap_tools_with_permission(self) -> None:
    """为需要权限的工具添加权限检查."""
    from bub.permission_decorator import add_permission_check

    tools_need_permission = [
        "fs.write",
        "fs.edit",
        "bash",
        "bash.kill",
        "tape.reset",
        "tape.handoff",
        # 在这里添加你的工具
    ]

    for tool_name in tools_need_permission:
        if tool_name in REGISTRY:
            REGISTRY[tool_name] = add_permission_check(REGISTRY[tool_name])
```

## 🎨 权限模式

系统支持三种权限模式（在 `src/bub/builtin/agent.py` 中配置）：

1. **SKILL_BASED** (默认) - 根据 skill 配置和工具类型决定
2. **ASK** - 每次都询问用户
3. **AUTO** - 自动批准所有工具（开发模式）

## 📊 工作流程

```
用户输入命令
    ↓
AI 决定调用工具
    ↓
权限管理器检查
    ↓
是否在自动批准列表？
  ├─ 是 → 直接执行
  └─ 否 → 显示权限提示
           ↓
      用户输入选择
      ├─ y/yes → 执行工具
      ├─ n/no → 拒绝执行
      ├─ always → 执行 + 添加到自动批准列表
      └─ never → 拒绝 + 记录
           ↓
      返回结果给 AI
```

## 🚀 示例

### 示例 1: 批准写文件

```
bub > create a test file with content "hello"

============================================================
🔧 Tool Permission Request
============================================================
Tool: fs.write

Parameters:
  path = test.txt
  content = hello

Options:
  y/yes    → Approve this time
  n/no     → Deny this time
  always   → Always approve this tool
  never    → Always deny this tool
============================================================
Your choice: y
✓ Approved

File created: test.txt
```

### 示例 2: 总是批准

```
bub > write another file

============================================================
🔧 Tool Permission Request
============================================================
Tool: fs.write

Parameters:
  path = another.txt
  content = test

Options:
  y/yes    → Approve this time
  n/no     → Deny this time
  always   → Always approve this tool
  never    → Always deny this tool
============================================================
Your choice: always
✓ Will always approve 'fs.write'

File created: another.txt

bub > write one more file
(不再询问，直接执行)
File created: onemore.txt
```

### 示例 3: 拒绝操作

```
bub > delete all files

============================================================
🔧 Tool Permission Request
============================================================
Tool: bash

Parameters:
  cmd = rm -rf *

Options:
  y/yes    → Approve this time
  n/no     → Deny this time
  always   → Always approve this tool
  never    → Always deny this tool
============================================================
Your choice: n
✗ Denied

I cannot proceed with that operation as you denied permission.
```

## 📁 相关文件

- `src/bub/permissions.py` - 权限管理核心
- `src/bub/permission_decorator.py` - 工具装饰器
- `src/bub/builtin/agent.py` - Agent 集成
- `.agents/skills/tool-permission/SKILL.md` - Skill 配置
- `docs/PERMISSION_SYSTEM.md` - 技术文档
- `docs/PERMISSION_USAGE.md` - 使用指南

## 💡 提示

- 如果你信任某个工具，使用 `always` 可以避免重复确认
- 权限设置只在当前会话有效，重启后会重置
- 可以通过修改 skill 配置来调整默认规则
- 安全的只读操作会自动批准，无需确认

## 🎉 完成！

权限系统现在已经完全可用，享受更安全的 AI 助手体验吧！
