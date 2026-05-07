from flask import Blueprint, request, jsonify
from models import db, RuleTask, TripleTask, TripleReview

triple_bp = Blueprint("triple", __name__)


@triple_bp.route("/api/triple/convert", methods=["POST"])
def convert_to_triple():
    """选择规则数据，触发LLM三元组转换"""
    data = request.get_json()
    if not data or "rule_task_id" not in data:
        return jsonify({"code": -1, "message": "请选择规则任务"}), 400

    rule_task_id = data["rule_task_id"]
    rule_task = db.session.get(RuleTask, rule_task_id)
    if not rule_task or rule_task.status != "success":
        return jsonify({"code": -1, "message": "规则任务不存在或未成功"}), 400

    # 检查是否已有进行中或成功的三元组任务
    existing = TripleTask.query.filter_by(rule_task_id=rule_task_id, status="pending").first()
    if existing:
        return jsonify({"code": -1, "message": "该规则数据已有转换任务进行中"}), 400

    model = data.get("model", "deepseek")

    triple_task = TripleTask(rule_task_id=rule_task_id, status="pending", model=model)
    db.session.add(triple_task)
    db.session.commit()

    from tasks.triple_tasks import convert_to_triple as convert_task
    convert_task.delay(triple_task.id, rule_task_id, model)

    return jsonify({
        "code": 0,
        "message": "转换任务已创建",
        "data": {"id": triple_task.id, "status": "pending"}
    })


@triple_bp.route("/api/triple/tasks", methods=["GET"])
def list_triple_tasks():
    """获取三元组任务列表（支持分页和规则文件名模糊搜索）"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 15, type=int)
    filename = request.args.get("filename", "").strip()

    query = TripleTask.query
    if filename:
        query = query.join(RuleTask, TripleTask.rule_task_id == RuleTask.id).filter(
            RuleTask.filename.like(f"%{filename}%")
        )
    query = query.order_by(TripleTask.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for t in pagination.items:
        item = {
            "id": t.id,
            "rule_task_id": t.rule_task_id,
            "rule_filename": t.rule_task.filename if t.rule_task else "",
            "model": t.model,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        items.append(item)

    return jsonify({
        "code": 0,
        "data": {
            "items": items,
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "total_pages": pagination.pages,
        }
    })


@triple_bp.route("/api/triple/tasks/<int:task_id>", methods=["GET"])
def get_triple_task(task_id):
    """获取单个三元组任务详情"""
    task = db.session.get(TripleTask, task_id)
    if not task:
        return jsonify({"code": -1, "message": "任务不存在"}), 404

    return jsonify({
        "code": 0,
        "data": {
            "id": task.id,
            "rule_task_id": task.rule_task_id,
            "model": task.model,
            "status": task.status,
            "triple_json": task.triple_json,
            "error_message": task.error_message,
            "validation_result": task.validation_result,
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }
    })


@triple_bp.route("/api/triple/tasks/<int:task_id>/retry", methods=["POST"])
def retry_triple_task(task_id):
    """重试失败或不合格的三元组转换任务"""
    task = db.session.get(TripleTask, task_id)
    if not task:
        return jsonify({"code": -1, "message": "任务不存在"}), 404
    if task.status not in ("failed", "unqualified"):
        return jsonify({"code": -1, "message": "只能重试失败或不合格的任务"}), 400

    rule_task = db.session.get(RuleTask, task.rule_task_id)
    if not rule_task or rule_task.status != "success":
        return jsonify({"code": -1, "message": "关联的规则任务不可用"}), 400

    task.status = "pending"
    task.error_message = None
    task.validation_result = None
    model = task.model or "deepseek"
    db.session.commit()

    from tasks.triple_tasks import convert_to_triple as convert_task
    convert_task.delay(task.id, task.rule_task_id, model)

    return jsonify({"code": 0, "message": "重试已触发"})
