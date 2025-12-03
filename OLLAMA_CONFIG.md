# Ollama 集成配置指南 (v0.6)

## 概述

GitHubSentinel v0.6 支持使用 Ollama 私有化部署的大模型服务，替代 OpenAI API。Ollama 提供了兼容 OpenAI API 的接口，可以无缝切换。

## 配置方式

### 方式 1: 通过 config.json 配置（推荐）

在 `config.json` 中添加 `llm` 配置项：

```json
{
    "github_token": "your_github_token",
    "email": {
        "smtp_server": "smtp.exmail.qq.com",
        "smtp_port": 465,
        "from": "from_email@example.com",
        "password": "your_email_password",
        "to": "to_email@example.com"
    },
    "subscriptions_file": "subscriptions.json",
    "github_progress_frequency_days": 1,
    "github_progress_execution_time": "08:00",
    "hacker_news_execution_time": "09:00",
    "llm": {
        "type": "ollama",
        "ollama_base_url": "http://localhost:11434/v1",
        "ollama_model": "llama3.2",
        "openai_model": "gpt-4o-mini"
    }
}
```

### 方式 2: 通过环境变量配置

```bash
# 设置 LLM 类型
export LLM_TYPE="ollama"

# 设置 Ollama 服务地址（默认: http://localhost:11434/v1）
export OLLAMA_BASE_URL="http://localhost:11434/v1"

# 设置 Ollama 模型名称（默认: llama3.2）
export OLLAMA_MODEL="llama3.2"

# 设置 OpenAI 模型（当 type=openai 时使用，默认: gpt-4o-mini）
export OPENAI_MODEL="gpt-4o-mini"
```

## 配置参数说明

| 参数 | 说明 | 默认值 | 必需 |
|------|------|--------|------|
| `type` | LLM 类型：`"openai"` 或 `"ollama"` | `"openai"` | 否 |
| `ollama_base_url` | Ollama API 服务地址 | `"http://localhost:11434/v1"` | 否 |
| `ollama_model` | Ollama 模型名称 | `"llama3.2"` | 否 |
| `openai_model` | OpenAI 模型名称 | `"gpt-4o-mini"` | 否 |

## 使用示例

### 使用 Ollama

```json
{
    "llm": {
        "type": "ollama",
        "ollama_base_url": "http://localhost:11434/v1",
        "ollama_model": "llama3.2"
    }
}
```

### 使用 OpenAI（默认）

```json
{
    "llm": {
        "type": "openai",
        "openai_model": "gpt-4o-mini"
    }
}
```

或者不配置 `llm` 项，默认使用 OpenAI。

## 功能支持

Ollama 集成支持所有使用 LLM 的功能：

- ✅ GitHub 仓库进展报告生成
- ✅ Hacker News 趋势报告生成
- ✅ Daemon 模式
- ✅ Gradio Web 界面
- ✅ Command 命令行工具

## 安装 Ollama

### Linux/macOS

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows

下载安装包：https://ollama.com/download

### 启动 Ollama 服务

```bash
ollama serve
```

### 下载模型

```bash
ollama pull llama3.2
```

## 测试配置

运行以下命令测试 Ollama 连接：

```bash
curl http://localhost:11434/api/tags
```

如果返回模型列表，说明 Ollama 服务正常运行。

## 注意事项

1. **兼容性**：Ollama 使用 OpenAI 兼容的 API 格式，代码无需修改即可切换
2. **性能**：本地部署的 Ollama 可能比云端 API 慢，但数据更安全
3. **模型选择**：根据硬件配置选择合适的模型，较大模型需要更多内存
4. **网络**：如果 Ollama 部署在远程服务器，修改 `ollama_base_url` 为服务器地址

## 故障排查

### 连接失败

- 检查 Ollama 服务是否运行：`ollama list`
- 检查端口是否正确（默认 11434）
- 检查防火墙设置

### 模型不存在

- 使用 `ollama list` 查看已安装的模型
- 使用 `ollama pull <model_name>` 下载模型

### 内存不足

- 选择较小的模型（如 `llama3.2:1b`）
- 增加系统内存
- 关闭其他占用内存的程序

