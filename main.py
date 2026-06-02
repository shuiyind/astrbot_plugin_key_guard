"""
API Key Guard — 密钥替换卫士

在 LLM 请求组装后、发往 API 前，检测消息中的疑似 API 密钥并替换为脱敏标记。
替换后的请求继续发往 LLM，不影响对话流程。

使用 @filter.on_llm_request() 钩子，文档参考 AstrBot 开发文档「事件钩子」章节。
"""

import re
import traceback

from astrbot.api.event import filter, AstrMessageEvent, MessageChain
from astrbot.api.star import Context, Star
from astrbot.api import logger

# ---------------------------------------------------------------------------
# 密钥正则 —— 宽入严出原则
# ---------------------------------------------------------------------------
# 只匹配极明确的高熵密钥格式，不匹配短字符串、无前缀字符串、URL 片段等。
_KEY_PATTERN = re.compile(
    r"(?<![a-zA-Z0-9])"
    r"(?:"
    r"sk-proj-[a-zA-Z0-9]{20,}"
    r"|"
    r"sk-[a-zA-Z0-9]{30,}"
    r"|"
    r"sk-ant-[a-zA-Z0-9]{15,}"
    r")"
    r"(?![a-zA-Z0-9])",
    re.ASCII,
)

_MATCH_COUNT = 0


def _mask_key(raw: str) -> str:
    """sk-proj-AbCdEfGhIjKlMnOpQrStUvWxYz123456
       → [此处sk-p***3456已被脱敏拦截]"""
    prefix = raw[:4] if len(raw) > 4 else raw
    suffix = raw[-4:] if len(raw) > 8 else ""
    return f"[此处{prefix}***{suffix}已被脱敏拦截]"


class KeyGuardPlugin(Star):
    """替换 LLM 请求中的疑似 API 密钥，再发往 API。"""

    def __init__(self, context: Context):
        super().__init__(context)
        logger.info("key_guard 已加载。匹配模式: %s", _KEY_PATTERN.pattern)

    @filter.on_llm_request()
    async def on_llm_request(self, event: AstrMessageEvent, req):
        """
        扫描 LLM 请求中的用户消息，替换密钥后放行。
        参考 AstrBot 开发文档：@filter.on_llm_request() 事件钩子。
        """
        global _MATCH_COUNT

        try:
            contexts = getattr(req, "contexts", [])
            prompt = getattr(req, "prompt", None)
            last_masked_raw = None

            # ------------------------------------------------------------ #
            # 扫描 contexts（OpenAI 格式的消息历史列表）                   #
            # ------------------------------------------------------------ #
            for msg in contexts:
                if not isinstance(msg, dict):
                    continue
                content = msg.get("content", "")
                if not isinstance(content, str):
                    continue

                match = _KEY_PATTERN.search(content)
                if not match:
                    continue

                raw = match.group()
                masked = _mask_key(raw)
                msg["content"] = content.replace(raw, masked)
                _MATCH_COUNT += 1
                last_masked_raw = raw

                logger.info(
                    "key_guard 替换 → 会话=%s 用户=%s 原始=%s 替换=%s 累计=%d",
                    event.unified_msg_origin,
                    event.get_sender_id(),
                    raw[:4] + "***" + raw[-4:],
                    masked,
                    _MATCH_COUNT,
                )

            # ------------------------------------------------------------ #
            # 扫描 prompt 字段（部分模式下当前消息在这）                    #
            # ------------------------------------------------------------ #
            if prompt and isinstance(prompt, str):
                match = _KEY_PATTERN.search(prompt)
                if match:
                    raw = match.group()
                    masked = _mask_key(raw)
                    req.prompt = prompt.replace(raw, masked)
                    _MATCH_COUNT += 1
                    last_masked_raw = raw

                    logger.info(
                        "key_guard 替换(prompt) → 会话=%s 原始=%s 替换=%s 累计=%d",
                        event.unified_msg_origin,
                        raw[:4] + "***" + raw[-4:],
                        masked,
                        _MATCH_COUNT,
                    )

            # ------------------------------------------------------------ #
            # 发送通知（使用主动消息 API）                                  #
            # ------------------------------------------------------------ #
            if last_masked_raw:
                try:
                    await self.context.send_message(
                        event.unified_msg_origin,
                        MessageChain().message(
                            f"🔒 已脱敏替换: {last_masked_raw[:4]}***{last_masked_raw[-4:]}"
                        ),
                    )
                except Exception as e2:
                    logger.warning("key_guard 通知发送失败: %s", e2)

        except Exception as e:
            logger.error(
                "key_guard 异常(%s)，已放行原始请求。traceback:\n%s",
                e,
                traceback.format_exc(),
            )
            return

    async def terminate(self):
        logger.info("key_guard 卸载: 累计替换=%d", _MATCH_COUNT)
