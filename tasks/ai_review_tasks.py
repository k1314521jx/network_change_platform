import json
from openai import APITimeoutError, APIConnectionError, RateLimitError, AuthenticationError
from models import db, TripleTask, AiReview, now_cn
from tasks.celery_app import celery
from services.llm_service import call_llm
from services.prompt_templates import AI_REVIEW_SYSTEM_PROMPT
from services.ai_review_service import parse_ai_review_response


def _friendly_error(exc: Exception) -> str:
    if isinstance(exc, APITimeoutError):
        return "LLM 请求超时，请稍后重试"
    if isinstance(exc, APIConnectionError):
        return "LLM 服务连接失败，请检查网络或稍后重试"
    if isinstance(exc, AuthenticationError):
        return "LLM 认证失败，请检查 API Key 配置"
    if isinstance(exc, RateLimitError):
        return "LLM 请求频率超限，请稍后重试"
    if isinstance(exc, ValueError) and "非法 JSON" in str(exc):
        return "LLM 返回格式异常，请重试或更换模型"
    if isinstance(exc, ValueError):
        return str(exc)
    return "服务异常，请稍后重试"


def _get_flask_app():
    import os, sys
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    import app as app_module
    return app_module.create_app()


@celery.task(bind=True, name="ai_review_tasks.run_ai_review")
def run_ai_review(self, review_id: int, triple_task_id: int, model: str = "deepseek", prompt_id: int = None):
    """AI审核: 调用LLM对三元组数据进行多维度评估"""
    flask_app = _get_flask_app()
    with flask_app.app_context():
        ai_review = db.session.get(AiReview, review_id)
        triple_task = db.session.get(TripleTask, triple_task_id)

        if not ai_review or not triple_task:
            return {"error": "Record not found"}

        try:
            ai_review.status = "reviewing"
            db.session.commit()

            triple_data = triple_task.triple_json
            if not triple_data:
                raise ValueError("三元组任务没有可用的triple_json数据")

            # 加载提示词：优先使用数据库配置，否则使用硬编码默认
            review_prompt = AI_REVIEW_SYSTEM_PROMPT
            if prompt_id:
                from services.prompt_service import get_prompt_content_by_id
                db_content = get_prompt_content_by_id(prompt_id)
                if db_content:
                    review_prompt = db_content

            user_message = json.dumps(triple_data, ensure_ascii=False, indent=2)

            response_text = call_llm(
                review_prompt,
                user_message,
                model_name=model,
                task_id=review_id,
                thinking_prefix="ai_review_thinking",
            )

            review_result = parse_ai_review_response(response_text)

            ai_review.status = "reviewed"
            ai_review.score = review_result["score"]
            ai_review.dimensions = review_result["dimensions"]
            ai_review.suggestions = review_result["suggestions"]
            ai_review.summary = review_result["summary"]
            ai_review.reviewed_at = now_cn()
            db.session.commit()

            return {"status": "reviewed", "review_id": review_id}

        except Exception as e:
            ai_review.status = "failed"
            ai_review.error_message = _friendly_error(e)
            db.session.commit()
            return {"status": "failed", "error": str(e)}
