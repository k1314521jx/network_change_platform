from flask import Blueprint, request, jsonify
from models import db, TripleTask, RuleValidation

rule_validation_bp = Blueprint("rule_validation", __name__)


@rule_validation_bp.route("/api/rule-validation/list", methods=["GET"])
def list_rule_validations():
    """规则审核列表：展示三元组转换成功的数据及其验证状态"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 15, type=int)

    # 查询所有成功的 TripleTask，LEFT JOIN RuleValidation
    query = db.session.query(TripleTask, RuleValidation).outerjoin(
        RuleValidation, TripleTask.id == RuleValidation.triple_task_id
    ).filter(TripleTask.status == "success").order_by(TripleTask.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for task, rv in pagination.items:
        items.append({
            "id": task.id,
            "rule_task_id": task.rule_task_id,
            "rule_filename": task.rule_task.filename if task.rule_task else "",
            "model": task.model,
            "status": rv.status if rv else "pending",
            "created_at": task.created_at.isoformat() if task.created_at else None,
        })

    return jsonify({
        "code": 0,
        "data": {
            "items": items,
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
        },
    })


@rule_validation_bp.route("/api/rule-validation/detail/<int:triple_task_id>", methods=["GET"])
def get_rule_validation_detail(triple_task_id):
    """获取验证详情（含违规信息）"""
    task = db.session.get(TripleTask, triple_task_id)
    if not task:
        return jsonify({"code": -1, "message": "任务不存在"}), 404

    rv = RuleValidation.query.filter_by(triple_task_id=triple_task_id).first()

    return jsonify({
        "code": 0,
        "data": {
            "id": task.id,
            "rule_task_id": task.rule_task_id,
            "model": task.model,
            "status": task.status,
            "triple_json": task.triple_json,
            "validation_status": rv.status if rv else "pending",
            "validation_result": rv.validation_result if rv else None,
            "created_at": task.created_at.isoformat() if task.created_at else None,
        },
    })


@rule_validation_bp.route("/api/rule-validation/passed-tasks", methods=["GET"])
def list_passed_tasks():
    """获取规则验证通过的任务列表（供 AI 审核下拉框使用）"""
    tasks = (
        db.session.query(TripleTask)
        .join(RuleValidation, TripleTask.id == RuleValidation.triple_task_id)
        .filter(TripleTask.status == "success", RuleValidation.status == "passed")
        .order_by(TripleTask.created_at.desc())
        .all()
    )
    items = [
        {
            "id": t.id,
            "rule_filename": t.rule_task.filename if t.rule_task else "",
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tasks
    ]
    return jsonify({"code": 0, "data": items})
