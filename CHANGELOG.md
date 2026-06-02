# Changelog

## v1.0.0 (2026-06-02)

### Features
- 初始发布
- 通过 `@filter.on_llm_request()` 钩子在 LLM 请求发往 API 前检测并替换密钥
- 支持检测 OpenAI 新格式 (`sk-proj-*`)、旧格式 (`sk-*`)、Anthropic (`sk-ant-*`)
- 替换后消息继续发往 LLM，不影响对话流程
- 崩溃保护：任何异常不阻塞消息通行
- 宽松匹配：仅匹配高熵密钥格式，不误杀

### Design
- 零外部依赖
- 完整 try/except 容错
- 日志记录每次替换操作
