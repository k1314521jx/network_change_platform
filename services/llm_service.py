import json
import logging
import time
from datetime import datetime
from httpx import ConnectError, ReadTimeout
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError, RateLimitError, AuthenticationError
from config import MODELS, ACTIVE_MODEL, REDIS_THINKING_CONFIG, LLM_THINKING_TTL
from services.model_service import get_model_config_by_name, get_first_active_model

logger = logging.getLogger("llm_service")

LLM_TIMEOUT = 3600  # 秒

EXCEPTION_MAP = {
    APITimeoutError: "请求超时: LLM API 在 {timeout}s 内未响应, 模型={model}, base_url={base_url}",
    APIConnectionError: "连接失败: 无法连接到 LLM 服务, base_url={base_url}, 原因={detail}",
    AuthenticationError: "认证失败: API Key 无效或已过期, 模型={model}, base_url={base_url}",
    RateLimitError: "限流: LLM API 请求频率超限, 模型={model}",
    ConnectError: "连接被拒: LLM 服务不可达, base_url={base_url}",
    ReadTimeout: "读取超时: LLM 响应超时({timeout}s), 模型={model}",
}


def get_active_model_config():
    """优先从数据库获取启用模型，fallback 到 config.py"""
    m = get_first_active_model()
    if m:
        return {"api_key": m.api_key, "base_url": m.base_url, "model": m.model}
    return MODELS.get(ACTIVE_MODEL, MODELS["deepseek"])


def _get_thinking_redis():
    """获取 Redis DB3 连接（LLM思考过程专用）"""
    import redis as redis_lib
    return redis_lib.Redis(
        host=REDIS_THINKING_CONFIG["host"],
        port=REDIS_THINKING_CONFIG["port"],
        db=REDIS_THINKING_CONFIG["db"],
        password=REDIS_THINKING_CONFIG["password"] or None,
        decode_responses=True,
    )


def save_thinking_to_redis(task_id: int, model: str, thinking_content: str) -> None:
    """将 LLM 思考过程存入 Redis DB3，设置 24h 过期"""
    if not thinking_content:
        return
    try:
        r = _get_thinking_redis()
        key = f"triple_thinking:{task_id}"
        data = {
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "thinking": thinking_content,
        }
        r.setex(key, LLM_THINKING_TTL, json.dumps(data, ensure_ascii=False))
        logger.info(f"[LLM] 思考过程已缓存 | key={key} | 长度={len(thinking_content)} | TTL={LLM_THINKING_TTL}s")
    except Exception as e:
        logger.warning(f"[LLM] 思考过程缓存失败（不影响主流程）: {e}")


def get_thinking_from_redis(task_id: int) -> dict | None:
    """从 Redis DB3 读取思考过程数据"""
    try:
        r = _get_thinking_redis()
        key = f"triple_thinking:{task_id}"
        raw = r.get(key)
        if raw:
            return json.loads(raw)
        return None
    except Exception as e:
        logger.warning(f"[LLM] 读取思考过程失败: {e}")
        return None


def save_ai_review_thinking(review_id: int, model: str, thinking_content: str) -> None:
    """将 AI 审核 LLM 思考过程存入 Redis DB3"""
    if not thinking_content:
        return
    try:
        r = _get_thinking_redis()
        key = f"ai_review_thinking:{review_id}"
        data = {
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "thinking": thinking_content,
        }
        r.setex(key, LLM_THINKING_TTL, json.dumps(data, ensure_ascii=False))
        logger.info(f"[AI-Review] 思考过程已缓存 | key={key} | 长度={len(thinking_content)}")
    except Exception as e:
        logger.warning(f"[AI-Review] 思考过程缓存失败: {e}")


def get_ai_review_thinking(review_id: int) -> dict | None:
    """从 Redis DB3 读取 AI 审核思考过程数据"""
    try:
        r = _get_thinking_redis()
        key = f"ai_review_thinking:{review_id}"
        raw = r.get(key)
        if raw:
            return json.loads(raw)
        return None
    except Exception as e:
        logger.warning(f"[AI-Review] 读取思考过程失败: {e}")
        return None


def call_llm(system_prompt: str, user_message: str, model_name: str = None, task_id: int = None, thinking_prefix: str = "triple_thinking", scene: str = "") -> str:
    """调用 LLM，使用流式请求 + 总耗时硬限制。
    非流式请求的 read timeout 在流式响应中会被每个 chunk 重置，
    导致推理模型（如 DeepSeek）总耗时可能远超设定值。
    改用流式请求手动累积内容，严格限制总耗时。
    """
    scene_tag = f"[{scene}] " if scene else ""
    # 优先从数据库查模型配置，fallback 到 config.py
    cfg = None
    if model_name:
        db_model = get_model_config_by_name(model_name)
        if db_model:
            cfg = {"api_key": db_model.api_key, "base_url": db_model.base_url, "model": db_model.model}
    if not cfg and model_name and model_name in MODELS:
        cfg = MODELS[model_name]
    if not cfg:
        cfg = get_active_model_config()

    model_id = cfg["model"]
    base_url = cfg["base_url"]

    logger.info(f"[LLM] {scene_tag}请求开始(流式) | 模型: {model_id} | base_url: {base_url} | 超时: {LLM_TIMEOUT}s")
    logger.info(f"[LLM] {scene_tag}system_prompt: {len(system_prompt)} 字符 | user_message: {len(user_message)} 字符")

    client = OpenAI(api_key=cfg["api_key"], base_url=base_url, timeout=300.0)

    start_time = time.time()
    try:
        stream = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            stream=True,
        )
    except Exception as e:
        _handle_exception(e, start_time, model_id, base_url, scene_tag)
        raise

    # 手动累积流式内容，严格检测总耗时
    content_chunks = []
    thinking_chunks = []
    finish_reason = None
    usage = None

    try:
        for chunk in stream:
            elapsed = time.time() - start_time
            if elapsed > LLM_TIMEOUT:
                logger.error(f"[LLM] {scene_tag}总耗时超限({round(elapsed)}s > {LLM_TIMEOUT}s)，强制中断")
                raise TimeoutError(f"LLM 总耗时超限({LLM_TIMEOUT}s)")

            if not chunk.choices:
                # 最后一个 chunk 可能只有 usage，没有 choices
                if hasattr(chunk, 'usage') and chunk.usage:
                    usage = chunk.usage
                continue

            delta = chunk.choices[0].delta
            if delta.content:
                content_chunks.append(delta.content)

            # 捕获思考过程流式 chunk
            thinking_delta = getattr(delta, 'reasoning_content', None) or getattr(delta, 'thinking', None)
            if thinking_delta:
                thinking_chunks.append(thinking_delta)

            if chunk.choices[0].finish_reason:
                finish_reason = chunk.choices[0].finish_reason

            # 部分 SDK 在流式最后一个 chunk 带有 usage
            if hasattr(chunk, 'usage') and chunk.usage:
                usage = chunk.usage
    except TimeoutError:
        raise
    except Exception as e:
        _handle_exception(e, start_time, model_id, base_url, scene_tag)
        raise

    elapsed = round(time.time() - start_time, 2)
    content = "".join(content_chunks)

    # 合并思考过程
    thinking_content = "".join(thinking_chunks) if thinking_chunks else None
    if not thinking_content:
        thinking_content = None
    if thinking_content and task_id is not None:
        if thinking_prefix == "ai_review_thinking":
            save_ai_review_thinking(task_id, model_id, thinking_content)
        else:
            save_thinking_to_redis(task_id, model_id, thinking_content)

    logger.info(
        f"[LLM] {scene_tag}请求成功 | 模型: {model_id} | 耗时: {elapsed}s | "
        f"finish_reason: {finish_reason} | "
        f"prompt_tokens: {usage.prompt_tokens if usage else 'N/A'} | "
        f"completion_tokens: {usage.completion_tokens if usage else 'N/A'} | "
        f"响应长度: {len(content)} | "
        f"思考过程: {'有(' + str(len(thinking_content)) + '字符)' if thinking_content else '无'}"
    )

    if finish_reason == "length":
        logger.warning(f"[LLM] {scene_tag}输出被截断，可能不完整")

    if not content:
        logger.error(f"[LLM] {scene_tag}返回空内容! finish_reason={finish_reason}")
        raise ValueError(f"LLM 返回空内容 (finish_reason={finish_reason})")

    return content


def _handle_exception(e: Exception, start_time: float, model_id: str, base_url: str, scene_tag: str = "") -> None:
    """统一处理 LLM 调用异常，记录详细日志"""
    elapsed = round(time.time() - start_time, 2)
    exc_type = type(e)

    for known_exc, msg_template in EXCEPTION_MAP.items():
        if isinstance(e, known_exc):
            error_msg = msg_template.format(
                timeout=LLM_TIMEOUT, model=model_id, base_url=base_url, detail=str(e)
            )
            logger.error(f"[LLM] {scene_tag}{error_msg} | 耗时: {elapsed}s")
            break
    else:
        error_msg = f"未知异常: {exc_type.__module__}.{exc_type.__qualname__} | 详情: {e}"
        logger.error(f"[LLM] {scene_tag}{error_msg} | 模型: {model_id} | base_url: {base_url} | 耗时: {elapsed}s")

    if isinstance(e, APIError):
        status_code = getattr(e, 'status_code', None)
        body = getattr(e, 'body', None)
        logger.error(f"[LLM] {scene_tag}HTTP状态码: {status_code} | 响应体: {body}")


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
