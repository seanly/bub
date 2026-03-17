# Bub 配置指南

## 快速开始

### 1. 配置 .env 文件

项目已经为你创建了 [.env](.env) 文件，包含以下配置：

```bash
# AI 模型配置（格式必须是 provider:model）
BUB_MODEL=openai:gemini-3.1-flash-lite-preview

# API 认证
BUB_API_KEY=sk-Ytkl7EOd5McGuiP6a

# API 端点
BUB_API_BASE=https://cliproxyapi.inner.syscube.cn/v1

# API 格式
BUB_API_FORMAT=completion
```

### 2. 验证配置

运行以下命令验证配置是否正确：

```bash
uv run python check_env.py
```

你应该看到所有配置项都显示 ✓。

### 3. 启动 Bub

```bash
# 启动交互式聊天
uv run bub chat

# 或者运行单个命令
uv run bub run "你的问题"
```

## 配置说明

### 模型格式

**重要**: `BUB_MODEL` 必须使用 `provider:model` 格式。

由于你使用的是自定义 API 端点（cliproxyapi），我们使用 `openai` 作为 provider，因为：
- 大多数自定义 API 端点都兼容 OpenAI API 格式
- Republic 库会使用 OpenAI 的 API 调用方式

### 支持的 Provider

根据你的 API 端点，可以使用以下 provider：

- `openai:model-name` - OpenAI 兼容的 API
- `openrouter:provider/model` - OpenRouter
- `anthropic:model-name` - Anthropic Claude
- `gemini:model-name` - Google Gemini（如果直接使用 Google API）

### 环境变量说明

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `BUB_MODEL` | AI 模型名称（必须包含 provider 前缀） | `openai:gemini-3.1-flash-lite-preview` |
| `BUB_API_KEY` | API 认证密钥 | `sk-xxx...` |
| `BUB_API_BASE` | API 端点 URL | `https://api.example.com/v1` |
| `BUB_API_FORMAT` | API 格式 | `completion` / `responses` / `messages` |
| `BUB_MAX_STEPS` | 最大步骤数 | `50` |
| `BUB_MAX_TOKENS` | 最大 token 数 | `1024` |
| `BUB_MODEL_TIMEOUT_SECONDS` | 模型超时时间 | `300` |
| `BUB_FALLBACK_MODEL` | 备用模型 | `openai:gpt-4` |
| `BUB_HOME` | Bub 主目录 | `~/.bub` |

### 多 Provider 配置

如果你需要配置多个 provider，可以使用以下格式：

```bash
# OpenRouter
BUB_OPENROUTER_API_KEY=your-openrouter-key
BUB_OPENROUTER_API_BASE=https://openrouter.ai/api/v1

# Gemini
BUB_GEMINI_API_KEY=your-gemini-key
BUB_GEMINI_API_BASE=https://generativelanguage.googleapis.com/v1

# 然后在模型名称中指定 provider
BUB_MODEL=openrouter:qwen/qwen3-coder-next
```

## 故障排查

### 错误: "Model must be in 'provider:model' format"

**原因**: 模型名称缺少 provider 前缀。

**解决方案**: 确保 `BUB_MODEL` 格式为 `provider:model`，例如：
```bash
BUB_MODEL=openai:gemini-3.1-flash-lite-preview
```

### 错误: API 认证失败

**检查**:
1. `BUB_API_KEY` 是否正确
2. `BUB_API_BASE` 是否可访问
3. API 端点是否需要特殊的认证头

### 错误: 模型不支持

**检查**:
1. 你的 API 端点是否支持该模型
2. 模型名称是否正确
3. 尝试使用 `BUB_FALLBACK_MODEL` 配置备用模型

## 测试工具

项目提供了两个测试脚本：

1. **check_env.py** - 快速检查环境变量
   ```bash
   uv run python check_env.py
   ```

2. **test_config.py** - 完整的配置测试（需要安装依赖）
   ```bash
   uv run python test_config.py
   ```

## 安全提示

⚠️ **重要**:
- `.env` 文件已经在 `.gitignore` 中，不会被提交到 git
- 不要在公开场合分享你的 API key
- 定期更换 API key
- 使用 `.env.example` 作为模板分享配置

## 参考文件

- [.env](.env) - 你的配置文件
- [.env.example](.env.example) - 配置模板
- [src/bub/builtin/settings.py](src/bub/builtin/settings.py) - 配置加载代码
