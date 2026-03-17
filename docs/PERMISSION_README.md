# 工具权限系统

类似 Claude Code 的工具确认机制，让你完全掌控 AI 的操作。

## ✨ 特性

- 🔒 **安全第一** - 敏感操作需要用户确认
- 🎯 **智能判断** - 安全的只读操作自动批准
- ⚙️ **灵活配置** - 通过 Skill 配置默认规则
- 💾 **记住选择** - 支持 "always" 选项避免重复确认

## 🚀 快速开始

```bash
uv run bub chat
```

尝试执行需要权限的操作：

```
bub > write a file, output hello world
```

你会看到权限提示：

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

输入 `y` 批准，`n` 拒绝，`always` 总是批准，`never` 总是拒绝。

## 📋 需要确认的工具

- `fs.write` - 写入文件
- `fs.edit` - 编辑文件
- `bash` - 执行 shell 命令
- `bash.kill` - 终止后台进程
- `tape.reset` - 重置对话历史
- `tape.handoff` - 添加交接点

## ✅ 自动批准的工具

- `fs.read` - 读取文件
- `tape.info` - 查看对话信息
- `tape.search` - 搜索对话历史
- `help` - 显示帮助

## ⚙️ 配置

编辑 `.agents/skills/tool-permission/SKILL.md` 来自定义规则：

```yaml
---
name: tool-permission
description: Tool permission configuration
metadata:
  auto_approved:
    - fs.read
    - fs.write  # 添加到这里来自动批准
  always_ask:
    - bash
---
```

## 📚 文档

- [完整使用指南](docs/PERMISSION_COMPLETE.md) - 详细的使用说明和示例
- [技术文档](docs/PERMISSION_SYSTEM.md) - 架构设计和实现细节
- [配置指南](docs/CONFIGURATION.md) - 环境变量和模型配置

## 🎯 实现细节

### 核心文件

- `src/bub/permissions.py` - 权限管理器
- `src/bub/permission_decorator.py` - 工具装饰器
- `src/bub/builtin/agent.py` - Agent 集成
- `.agents/skills/tool-permission/SKILL.md` - Skill 配置

### 工作原理

1. AI 决定调用工具
2. 权限管理器检查是否需要确认
3. 如果需要，显示权限提示并等待用户输入
4. 根据用户选择执行或拒绝操作
5. 返回结果给 AI

## 💡 使用技巧

- **首次使用 `always`** - 对于信任的工具，第一次选择 `always` 可以避免重复确认
- **配置默认规则** - 编辑 Skill 配置来设置默认的自动批准工具
- **会话级别** - 权限设置只在当前会话有效，重启后重置

## 🎉 完成

现在你的 Bub 已经有了完整的工具权限系统！享受更安全、更可控的 AI 助手体验。
