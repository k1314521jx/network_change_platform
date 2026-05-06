import json
import logging
from datetime import datetime
from openai import OpenAI
from config import MODELS, ACTIVE_MODEL

logger = logging.getLogger("llm_service")


def get_active_model_config():
    return MODELS.get(ACTIVE_MODEL, MODELS["deepseek"])


def call_llm(system_prompt: str, user_message: str, model_name: str = None) -> str:
    """调用 LLM，使用 response_format 强制输出 JSON"""
    if model_name and model_name in MODELS:
        cfg = MODELS[model_name]
    else:
        cfg = get_active_model_config()
        model_name = ACTIVE_MODEL

    logger.info(f"[LLM] 模型: {cfg['model']} | base_url: {cfg['base_url']}")
    logger.info(f"[LLM] system_prompt: {len(system_prompt)} 字符")
    logger.info(f"[LLM] user_message: {len(user_message)} 字符")

    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])

    try:
        response = client.chat.completions.create(
            model=cfg["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
    except Exception as e:
        logger.error(f"[LLM] API 请求失败: {e}")
        raise

    finish_reason = response.choices[0].finish_reason
    content = response.choices[0].message.content
    usage = response.usage

    logger.info(
        f"[LLM] finish_reason: {finish_reason} | "
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
