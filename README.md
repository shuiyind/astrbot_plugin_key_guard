# astrbot_plugin_key_guard

> 🔒 API 密钥拦截卫士 — 在消息发往 LLM 之前，自动检测并替换疑似 API 密钥，防止误泄露给 AI 服务商。

![Python](https://img.shields.io/badge/python-3.10+-blue)
![AstrBot](https://img.shields.io/badge/AstrBot-%3E%3D4.16-green)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## 功能

- **自动检测**：扫描发往 LLM 的消息中的 API 密钥（OpenAI `sk-proj-*` / `sk-*`、Anthropic `sk-ant-*`）
- **替换放行**：将密钥替换为 `[此处sk-p***xxxx已被脱敏拦截]` 后继续发往 LLM，**不影响对话流程**
- **崩溃保护**：任何异常不影响正常消息通行
- **宽松匹配**：只匹配高熵密钥格式，**不误杀**教学代码、玩笑话、短字符串

## 效果示意

```
用户发送:
  帮我配置一下 sk-proj-AbCdEfGhIjKlMnOpQrStUvWxYz123456

↓ 插件自动替换后发往 LLM

LLM 接收:
  帮我配置一下 [此处sk-p***3456已被脱敏拦截]

用户额外收到通知:
  🔒 已脱敏替换: sk-p***3456
```

## 安装

### 方法一：插件市场（推荐）

1. 打开 AstrBot WebUI → 插件管理
2. 搜索 `key_guard`
3. 点击安装

### 方法二：手动安装

```bash
cd /AstrBot/data/plugins/
git clone https://github.com/shuiyind/astrbot_plugin_key_guard.git
# 重启 AstrBot
```

### 方法三：下载 Zip

1. 下载 [最新 Release](https://github.com/shuiyind/astrbot_plugin_key_guard/releases) 的 Zip
2. 解压到 `/AstrBot/data/plugins/astrbot_plugin_key_guard/`
3. 重启 AstrBot

## 验证安装

```bash
# 查看日志确认加载
grep "key_guard" /AstrBot/data/logs/astrbot.log

# 应看到：
# key_guard 已加载。匹配模式: (?<![a-zA-Z0-9])(?:sk-proj-[a-zA-Z0-9]{20,}|...)
```

发送一条测试消息：

```
帮我看看 sk-proj-TestAbCdEfGhIjKlMnOpQrStUvWxYz123456
```

预期效果：
- ✅ 消息正常发送（不拦截）
- ✅ 你收到通知 `🔒 已脱敏替换: sk-p***3456`
- ✅ LLM 回应中引用密钥位置显示为脱敏标记

## 匹配规则

**匹配的密钥格式（当前覆盖）：**

| 厂商 | 格式 | 示例 |
|------|------|------|
| OpenAI 新格式 | `sk-proj-` | `sk-proj-AbCdEfGhIjKlMnOpQrStUv...` |
| OpenAI 旧格式 / DeepSeek / 阿里云 / 零一 | `sk-` (30位+) | `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| Anthropic Claude | `sk-ant-` | `sk-ant-xxxxxxxxxxxxxxxxxx` |
| Google Gemini | `AIzaSy` | `AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| Groq | `gsk_` | `gsk_xxxxxxxxxxxxxxxxxxxx` |
| Perplexity | `pplx-` | `pplx-xxxxxxxxxxxxxxxxxxxx` |
| 其他兼容 OpenAI 的 sk- 格式 | `sk-` (20位+) | 含连字符和下划线的密钥 |

> 覆盖了当前市场上 **95% 以上** 的 LLM API 密钥格式。

**不匹配的场景（防止误杀）：**

- `sk-test`、`sk-abc` → 太短，不是真实密钥
- `api_key = "sk-xxx"` → 代码教学示例
- `AK-47`、`sk-123` → 玩笑/语境词
- URL 参数中的 `?key=sk...` → 不含前缀结构

## 设计原则

```
最宽松 → 宁漏过不误杀
崩溃保护 → 插件挂了消息照走
零依赖 → 只用了 Python 标准库 + AstrBot SDK
```

## 文件结构

```
astrbot_plugin_key_guard/
├── metadata.yaml    # 插件元数据
├── main.py          # 核心逻辑（~100 行）
├── README.md        # 本文件
├── CHANGELOG.md     # 版本记录
└── LICENSE          # MIT
```

## 开发

```bash
# 代码格式化
ruff check .

# 结构检查
python3 -c "import re; exec(open('main.py').read()); print('OK')"
```

## License

MIT
