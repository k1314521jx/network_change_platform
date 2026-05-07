import json
from openai import APITimeoutError, APIConnectionError, RateLimitError, AuthenticationError
from models import db, RuleTask, TripleTask
from tasks.celery_app import celery
from services.llm_service import call_llm, parse_and_validate
from services.prompt_templates import SYSTEM_PROMPT, INPUT_SCHEMA_DOC
from services.triple_validator import validate_triple


def _friendly_error(exc: Exception) -> str:
    """将后端异常转换为用户可读的简要错误描述"""
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
    """在 worker 进程中获取 Flask app 实例"""
    import os, sys
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    import app as app_module
    return app_module.create_app()


@celery.task(bind=True, name="triple_tasks.convert_to_triple")
def convert_to_triple(self, triple_task_id: int, rule_task_id: int, model: str = "deepseek"):
    """模块B: 调用LLM将规则化JSON转换为三元组"""
    flask_app = _get_flask_app()
    with flask_app.app_context():
        triple_task = db.session.get(TripleTask, triple_task_id)
        rule_task = db.session.get(RuleTask, rule_task_id)

        if not triple_task or not rule_task:
            return {"error": "Task not found"}

        try:
            input_data = rule_task.extracted_json
            if not input_data:
                raise ValueError("规则任务没有可用的extracted_json数据")

            # 构建 user message：输入数据结构说明 + 实际数据（匹配已验证的方案）
            user_message = INPUT_SCHEMA_DOC + "\n" + json.dumps(
                input_data, ensure_ascii=False, indent=2
            )

            response_text = call_llm(SYSTEM_PROMPT, user_message, model_name=model, task_id=triple_task_id)
            triple_data = parse_and_validate(response_text)

            # 规则校验
            validation = validate_triple(triple_data)
            if not validation["passed"]:
                triple_task.status = "unqualified"
                triple_task.triple_json = triple_data
                triple_task.validation_result = validation
                db.session.commit()
                return {"status": "unqualified", "triple_task_id": triple_task_id}

            triple_task.status = "success"
            triple_task.triple_json = triple_data
            db.session.commit()

            return {"status": "success", "triple_task_id": triple_task_id}

        except Exception as e:
            triple_task.status = "failed"
            triple_task.triple_json = {"error": str(e)}
            triple_task.error_message = _friendly_error(e)
            db.session.commit()
            return {"status": "failed", "error": str(e)}
