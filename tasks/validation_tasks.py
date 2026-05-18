import json
from models import db, TripleTask, RuleValidation, AiReview
from tasks.celery_app import celery
from services.triple_validator import validate_triple


def _get_flask_app():
    import os, sys
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    import app as app_module
    return app_module.create_app()


@celery.task(bind=True, name="validation_tasks.validate_triple_task")
def validate_triple_task(self, triple_task_id: int):
    """异步规则验证：pending → validating → passed/unqualified"""
    flask_app = _get_flask_app()
    with flask_app.app_context():
        task = db.session.get(TripleTask, triple_task_id)
        rv = RuleValidation.query.filter_by(triple_task_id=triple_task_id).first()
        if not task or not rv:
            return {"error": "not found"}

        try:
            validation = validate_triple(task.triple_json)
            rv.validation_result = validation
            if validation["passed"]:
                rv.status = "passed"

                # 自动创建 AI 审核记录（如果不存在）
                existing_ai_review = AiReview.query.filter_by(triple_task_id=triple_task_id).first()
                if not existing_ai_review:
                    # 使用默认模型创建 AI 审核记录
                    ai_review = AiReview(
                        triple_task_id=triple_task_id,
                        model="deepseek",  # 默认模型
                        status="pending"
                    )
                    db.session.add(ai_review)
            else:
                rv.status = "unqualified"
                # 仅保留第一次验证不合格的结果
                if rv.first_validation_result is None:
                    rv.first_validation_result = validation
            db.session.commit()
            return {"status": rv.status, "triple_task_id": triple_task_id}
        except Exception as e:
            rv.status = "pending"
            db.session.commit()
            return {"error": str(e)}
