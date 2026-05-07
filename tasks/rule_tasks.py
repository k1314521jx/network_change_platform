from models import db, RuleTask
from tasks.celery_app import celery
from services.xlsx_parser import parse_xlsx


def _get_flask_app():
    """在 worker 进程中获取 Flask app 实例"""
    import os, sys
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    import app as app_module
    return app_module.create_app()


@celery.task(bind=True, name="rule_tasks.process_excel")
def process_excel(self, task_id: int, filepath: str, original_filename: str = ""):
    """模块A: 异步处理上传的Excel文件，解析为结构化JSON"""
    flask_app = _get_flask_app()
    with flask_app.app_context():
        task = db.session.get(RuleTask, task_id)
        if not task:
            return {"error": "Task not found"}

        try:
            if not filepath:
                raise ValueError("文件路径为空，无法解析")

            result = parse_xlsx(filepath)
            # 用原始文件名替换从磁盘路径取的UUID名
            if original_filename:
                import os
                result['name'] = os.path.splitext(original_filename)[0]
            task.status = "success"
            task.extracted_json = result
            db.session.commit()
            return {"status": "success", "task_id": task_id}

        except Exception as e:
            task.status = "failed"
            task.extracted_json = {"error": str(e)}
            db.session.commit()
            return {"status": "failed", "error": str(e)}
