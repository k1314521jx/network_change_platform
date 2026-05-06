import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from models import db, RuleTask

rule_bp = Blueprint("rule", __name__)


@rule_bp.route("/api/rule/upload", methods=["POST"])
def upload_excel():
    """上传Excel文件并触发Celery异步处理"""
    if "file" not in request.files:
        return jsonify({"code": -1, "message": "未找到上传文件"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"code": -1, "message": "文件名为空"}), 400

    original_filename = file.filename  # 保留原始中文文件名
    safe_name = secure_filename(file.filename) or "file"
    # 磁盘文件用 UUID 命名，避免中文路径问题
    _, ext = os.path.splitext(safe_name)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
    filepath = os.path.join(upload_folder, unique_name)
    os.makedirs(upload_folder, exist_ok=True)
    file.save(filepath)

    task = RuleTask(filename=original_filename, status="pending")
    db.session.add(task)
    db.session.commit()

    from tasks.rule_tasks import process_excel
    process_excel.delay(task.id, filepath)

    return jsonify({
        "code": 0,
        "message": "上传成功，任务已创建",
        "data": {"id": task.id, "filename": original_filename, "status": "pending"}
    })


@rule_bp.route("/api/rule/tasks", methods=["GET"])
def list_tasks():
    """获取规则任务列表（支持分页和文件名模糊搜索）"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 15, type=int)
    filename = request.args.get("filename", "").strip()

    query = RuleTask.query.filter_by(is_deleted=False)
    if filename:
        query = query.filter(RuleTask.filename.like(f"%{filename}%"))
    query = query.order_by(RuleTask.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "code": 0,
        "data": {
            "items": [t.to_dict() for t in pagination.items],
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "total_pages": pagination.pages,
        }
    })


@rule_bp.route("/api/rule/tasks/success", methods=["GET"])
def list_success_tasks():
    """获取所有成功的规则任务（供模块B下拉选择）"""
    tasks = RuleTask.query.filter_by(status="success", is_deleted=False).order_by(RuleTask.created_at.desc()).all()
    return jsonify({
        "code": 0,
        "data": [{"id": t.id, "filename": t.filename, "created_at": t.created_at.isoformat() if t.created_at else None} for t in tasks]
    })


@rule_bp.route("/api/rule/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    """获取单个规则任务详情"""
    task = db.session.get(RuleTask, task_id)
    if not task:
        return jsonify({"code": -1, "message": "任务不存在"}), 404
    return jsonify({"code": 0, "data": task.to_dict()})


@rule_bp.route("/api/rule/tasks/<int:task_id>/retry", methods=["POST"])
def retry_task(task_id):
    """重试失败的规则任务"""
    task = db.session.get(RuleTask, task_id)
    if not task:
        return jsonify({"code": -1, "message": "任务不存在"}), 404
    if task.status != "failed":
        return jsonify({"code": -1, "message": "只能重试失败的任务"}), 400

    task.status = "pending"
    db.session.commit()

    from tasks.rule_tasks import process_excel
    process_excel.delay(task.id, "")

    return jsonify({"code": 0, "message": "重试已触发"})


# 为 RuleTask 添加 to_dict 方法
def _rule_task_to_dict(self):
    return {
        "id": self.id,
        "filename": self.filename,
        "status": self.status,
        "extracted_json": self.extracted_json,
        "created_at": self.created_at.isoformat() if self.created_at else None,
        "is_deleted": self.is_deleted,
    }


RuleTask.to_dict = _rule_task_to_dict
