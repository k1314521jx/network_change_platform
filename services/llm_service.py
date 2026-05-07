import json
import logging
import time
from datetime import datetime
from httpx import ConnectError, ReadTimeout
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError, RateLimitError, AuthenticationError
from config import MODELS, ACTIVE_MODEL

logger = logging.getLogger("llm_service")

LLM_TIMEOUT = 600  # 秒

EXCEPTION_MAP = {
    APITimeoutError: "请求超时: LLM API 在 {timeout}s 内未响应, 模型={model}, base_url={base_url}",
    APIConnectionError: "连接失败: 无法连接到 LLM 服务, base_url={base_url}, 原因={detail}",
    AuthenticationError: "认证失败: API Key 无效或已过期, 模型={model}, base_url={base_url}",
    RateLimitError: "限流: LLM API 请求频率超限, 模型={model}",
    ConnectError: "连接被拒: LLM 服务不可达, base_url={base_url}",
    ReadTimeout: "读取超时: LLM 响应超时({timeout}s), 模型={model}",
}


def get_active_model_config():
    return MODELS.get(ACTIVE_MODEL, MODELS["deepseek"])


def call_llm(system_prompt: str, user_message: str, model_name: str = None) -> str:
    """调用 LLM，使用 response_format 强制输出 JSON"""
    if model_name and model_name in MODELS:
        cfg = MODELS[model_name]
    else:
        cfg = get_active_model_config()

    model_id = cfg["model"]
    base_url = cfg["base_url"]

    logger.info(f"[LLM] 请求开始 | 模型: {model_id} | base_url: {base_url}")
    logger.info(f"[LLM] system_prompt: {len(system_prompt)} 字符 | user_message: {len(user_message)} 字符")

    client = OpenAI(api_key=cfg["api_key"], base_url=base_url, timeout=LLM_TIMEOUT)

    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        exc_type = type(e)

        # 按异常类型匹配详细错误信息
        for known_exc, msg_template in EXCEPTION_MAP.items():
            if isinstance(e, known_exc):
                error_msg = msg_template.format(
                    timeout=LLM_TIMEOUT, model=model_id, base_url=base_url, detail=str(e)
                )
                logger.error(f"[LLM] {error_msg} | 耗时: {elapsed}s")
                break
        else:
            # 未知异常，记录完整类型和信息
            error_msg = f"未知异常: {exc_type.__module__}.{exc_type.__qualname__} | 详情: {e}"
            logger.error(f"[LLM] {error_msg} | 模型: {model_id} | base_url: {base_url} | 耗时: {elapsed}s")

        # 有响应体时记录（部分 APIError 包含 HTTP 响应信息）
        if isinstance(e, APIError):
            status_code = getattr(e, 'status_code', None)
            body = getattr(e, 'body', None)
            logger.error(f"[LLM] HTTP状态码: {status_code} | 响应体: {body}")
        raise

    elapsed = round(time.time() - start_time, 2)

    finish_reason = response.choices[0].finish_reason
    content = response.choices[0].message.content
    usage = response.usage

    logger.info(
        f"[LLM] 请求成功 | 模型: {model_id} | 耗时: {elapsed}s | "
        f"finish_reason: {finish_reason} | "
        f"prompt_tokens: {usage.prompt_tokens if usage else 'N/A'} | "
        f"completion_tokens: {usage.completion_tokens if usage else 'N/A'} | "
        f"响应长度: {len(content) if content else 0}"
    )

    if finish_reason == "length":
        logger.warning("[LLM] 输出被截断，可能不完整")

    if not content:
        logger.error(f"[LLM] 返回空内容! finish_reason={finish_reason}")
        raise ValueError(f"LLM 返回空内容 (finish_reason={finish_reason})")

    # 保存原始响应用于调试
    _save_response_log(cfg["model"], content, finish_reason, usage)

    return content


def _save_response_log(model: str, content: str, finish_reason: str, usage) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"llm_response_{timestamp}.txt"
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"模型: {model}\n时间: {timestamp}\nfinish_reason: {finish_reason}\n")
            if usage:
                f.write(f"tokens: prompt={usage.prompt_tokens}, completion={usage.completion_tokens}\n")
            f.write(f"\n=== 原始响应 ===\n{content}")
        logger.info(f"[LLM] 原始响应已保存: {log_path}")
    except Exception:
        pass


def parse_and_validate(raw_response: str) -> dict:
    """解析 LLM 返回的 JSON 并校验结构"""
    # 直接解析（response_format 保证是合法 JSON）
    try:
        result = json.loads(raw_response)
    except json.JSONDecodeError:
        logger.error(f"[JSON] 解析失败，原始响应:\n{raw_response[:1000]}")
        raise ValueError(f"LLM 返回非法 JSON，前1000字符:\n{raw_response[:1000]}")

    # 结构校验
    from services.schema_validator import validate_output
    try:
        validate_output(result)
    except ValueError:
        logger.error(f"[JSON] 结构校验失败，原始响应:\n{raw_response[:1000]}")
        raise

    logger.info(f"[JSON] 解析+校验通过 | Table1: {len(result.get('Table1_Alignment', []))} 行, "
                f"Table2: {len(result.get('Table2_Entities_Attributes', []))} 节点, "
                f"Table3: {len(result.get('Table3_Relations', []))} 关系")
    return result
