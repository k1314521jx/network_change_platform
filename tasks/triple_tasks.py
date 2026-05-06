import json
from models import db, RuleTask, TripleTask
from tasks.celery_app import celery
from services.llm_service import call_llm, parse_and_validate
from services.prompt_templates import SYSTEM_PROMPT, INPUT_SCHEMA_DOC


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

            response_text = call_llm(SYSTEM_PROMPT, user_message, model_name=model)
            triple_data = parse_and_validate(response_text)

            triple_task.status = "success"
            triple_task.triple_json = triple_data
            db.session.commit()

            return {"status": "success", "triple_task_id": triple_task_id}

        except Exception as e:
            triple_task.status = "failed"
            triple_task.triple_json = {"error": str(e)}
            db.session.commit()
            return {"status": "failed", "error": str(e)}
