from flask import Blueprint, request, jsonify, Response
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
    prompt_id = data.get("prompt_id")

    triple_task = TripleTask(rule_task_id=rule_task_id, status="pending", model=model)
    db.session.add(triple_task)
    db.session.commit()

    from tasks.triple_tasks import convert_to_triple as convert_task
    convert_task.delay(triple_task.id, rule_task_id, model, prompt_id=prompt_id)

    return jsonify({
        "code": 0,
        "message": "转换任务已创建",
        "data": {"id": triple_task.id, "status": "pending"}
    })


@triple_bp.route("/api/triple/batch-convert", methods=["POST"])
def batch_convert_to_triple():
    """批量选择规则数据，触发LLM三元组转换"""
    data = request.get_json()
    if not data or "rule_task_ids" not in data:
        return jsonify({"code": -1, "message": "请选择规则任务"}), 400

    rule_task_ids = data["rule_task_ids"]
    if not rule_task_ids or not isinstance(rule_task_ids, list):
        return jsonify({"code": -1, "message": "请选择至少一条规则数据"}), 400

    model = data.get("model", "deepseek")
    prompt_id = data.get("prompt_id")
    created = []
    skipped = []

    for rule_task_id in rule_task_ids:
        rule_task = db.session.get(RuleTask, rule_task_id)
        if not rule_task or rule_task.status != "success":
            skipped.append({"id": rule_task_id, "reason": "规则任务不存在或未成功"})
            continue

        existing = TripleTask.query.filter_by(rule_task_id=rule_task_id, status="pending").first()
        if existing:
            skipped.append({"id": rule_task_id, "reason": "已有转换任务进行中"})
            continue

        triple_task = TripleTask(rule_task_id=rule_task_id, status="pending", model=model)
        db.session.add(triple_task)
        db.session.commit()

        from tasks.triple_tasks import convert_to_triple as convert_task
        convert_task.delay(triple_task.id, rule_task_id, model, prompt_id=prompt_id)
        created.append(triple_task.id)

    return jsonify({
        "code": 0,
        "message": f"已创建 {len(created)} 个转换任务" + (f"，跳过 {len(skipped)} 个" if skipped else ""),
        "data": {"created": created, "skipped": skipped}
    })


@triple_bp.route("/api/triple/tasks", methods=["GET"])
def list_triple_tasks():
    """获取三元组任务列表（支持分页和规则文件名模糊搜索）"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 15, type=int)
    filename = request.args.get("filename", "").strip()
    status = request.args.get("status", "").strip()
    model = request.args.get("model", "").strip()

    query = TripleTask.query
    if model:
        query = query.filter(TripleTask.model.like(f"%{model}%"))
    if status:
        statuses = [s.strip() for s in status.split(",") if s.strip()]
        if len(statuses) == 1:
            query = query.filter(TripleTask.status == statuses[0])
        elif statuses:
            query = query.filter(TripleTask.status.in_(statuses))
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
    """重试失败的三元组转换任务"""
    task = db.session.get(TripleTask, task_id)
    if not task:
        return jsonify({"code": -1, "message": "任务不存在"}), 404
    if task.status != "failed":
        return jsonify({"code": -1, "message": "只能重试失败的任务"}), 400

    rule_task = db.session.get(RuleTask, task.rule_task_id)
    if not rule_task or rule_task.status != "success":
        return jsonify({"code": -1, "message": "关联的规则任务不可用"}), 400

    task.status = "pending"
    task.error_message = None
    model = task.model or "deepseek"
    db.session.commit()

    from tasks.triple_tasks import convert_to_triple as convert_task
    convert_task.delay(task.id, task.rule_task_id, model)

    return jsonify({"code": 0, "message": "重试已触发"})


@triple_bp.route("/api/triple/tasks/<int:task_id>/thinking", methods=["GET"])
def export_thinking(task_id):
    """导出 LLM 思考过程为 txt 文件"""
    task = db.session.get(TripleTask, task_id)
    if not task:
        return jsonify({"code": -1, "message": "任务不存在"}), 404

    from services.llm_service import get_thinking_from_redis
    data = get_thinking_from_redis(task_id)
    if not data:
        return jsonify({"code": -1, "message": "数据过期或数据未生成"}), 404

    model = data.get("model", "unknown")
    timestamp = data.get("timestamp", "")
    thinking = data.get("thinking", "")

    txt_content = (
        f"=== LLM 思考过程 ===\n"
        f"任务ID: {task_id}\n"
        f"模型: {model}\n"
        f"生成时间: {timestamp}\n"
        f"{'=' * 40}\n\n"
        f"{thinking}"
    )

    filename = f"thinking_task_{task_id}.txt"
    return Response(
        txt_content,
        mimetype="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@triple_bp.route("/api/triple/tasks/<int:task_id>/validate", methods=["POST"])
def validate_triple_task(task_id):
    """触发单条规则验证（异步 Celery 任务）"""
    task = db.session.get(TripleTask, task_id)
    if not task:
        return jsonify({"code": -1, "message": "任务不存在"}), 404
    if task.status != "success":
        return jsonify({"code": -1, "message": "只能验证成功的任务"}), 400

    from models import RuleValidation
    rv = RuleValidation.query.filter_by(triple_task_id=task_id).first()
    if not rv:
        rv = RuleValidation(triple_task_id=task_id, status="pending")
        db.session.add(rv)
        db.session.commit()

    if rv.status == "validating":
        return jsonify({"code": -1, "message": "该任务正在验证中"}), 400

    rv.status = "validating"
    db.session.commit()

    from tasks.validation_tasks import validate_triple_task as do_validate
    do_validate.delay(task_id)
    return jsonify({"code": 0, "message": "验证已触发"})


@triple_bp.route("/api/triple/tasks/batch-validate", methods=["POST"])
def batch_validate_triple_tasks():
    """批量触发规则验证（异步 Celery 任务）"""
    data = request.get_json()
    ids = data.get("ids", []) if data else []
    if not ids:
        return jsonify({"code": -1, "message": "请选择要验证的任务"}), 400

    from models import RuleValidation
    from tasks.validation_tasks import validate_triple_task as do_validate
    triggered = 0
    for tid in ids:
        task = db.session.get(TripleTask, tid)
        if not task or task.status != "success":
            continue
        rv = RuleValidation.query.filter_by(triple_task_id=tid).first()
        if not rv:
            rv = RuleValidation(triple_task_id=tid, status="pending")
            db.session.add(rv)
        if rv.status == "validating":
            continue
        rv.status = "validating"
        db.session.commit()
        do_validate.delay(tid)
        triggered += 1

    return jsonify({"code": 0, "message": f"已触发 {triggered} 条验证任务"})


@triple_bp.route("/api/triple/tasks/<int:task_id>/update-and-validate", methods=["POST"])
def update_and_validate(task_id):
    """更新三元组JSON并触发重新验证（供不合格数据修正后使用）"""
    task = db.session.get(TripleTask, task_id)
    if not task:
        return jsonify({"code": -1, "message": "任务不存在"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"code": -1, "message": "缺少数据"}), 400

    task.triple_json = {
        "Table1_Alignment": data.get("table1", []),
        "Table2_Entities_Attributes": data.get("table2", []),
        "Table3_Relations": data.get("table3", []),
    }
    db.session.commit()

    from models import RuleValidation
    rv = RuleValidation.query.filter_by(triple_task_id=task_id).first()
    if rv:
        rv.status = "validating"
        rv.validation_result = None
        db.session.commit()
        from tasks.validation_tasks import validate_triple_task as do_validate
        do_validate.delay(task_id)

    return jsonify({"code": 0, "message": "已更新并触发重新验证"})
