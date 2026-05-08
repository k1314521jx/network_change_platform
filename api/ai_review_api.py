from flask import Blueprint, request, jsonify, Response
from models import db, TripleTask, AiReview, RuleValidation

ai_review_bp = Blueprint("ai_review", __name__)


@ai_review_bp.route("/api/ai-review/create", methods=["POST"])
def create_ai_review():
    """触发AI审核"""
    data = request.get_json()
    if not data or "triple_task_id" not in data:
        return jsonify({"code": -1, "message": "请选择三元组任务"}), 400

    triple_task_id = data["triple_task_id"]
    triple_task = db.session.get(TripleTask, triple_task_id)
    if not triple_task or triple_task.status != "success":
        return jsonify({"code": -1, "message": "三元组任务不存在或未成功"}), 400

    # 检查规则验证是否通过
    rv = RuleValidation.query.filter_by(triple_task_id=triple_task_id).first()
    if not rv or rv.status != "passed":
        return jsonify({"code": -1, "message": "该任务尚未通过规则验证"}), 400

    # 检查是否已有审核中或已审核的记录
    existing = AiReview.query.filter(
        AiReview.triple_task_id == triple_task_id,
        AiReview.status.in_(["pending", "reviewing", "reviewed"]),
    ).first()
    if existing:
        return jsonify({"code": -1, "message": "该任务已有进行中或已完成的AI审核"}), 400

    model = data.get("model", "deepseek")
    prompt_id = data.get("prompt_id")

    ai_review = AiReview(triple_task_id=triple_task_id, model=model, status="pending")
    db.session.add(ai_review)
    db.session.commit()

    from tasks.ai_review_tasks import run_ai_review
    run_ai_review.delay(ai_review.id, triple_task_id, model, prompt_id=prompt_id)

    return jsonify({
        "code": 0,
        "message": "AI审核任务已创建",
        "data": {"id": ai_review.id, "status": "pending"},
    })


@ai_review_bp.route("/api/ai-review/list", methods=["GET"])
def list_ai_reviews():
    """AI审核列表（分页）"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 15, type=int)
    status_filter = request.args.get("status", "").strip()

    query = AiReview.query
    if status_filter:
        query = query.filter(AiReview.status == status_filter)
    query = query.order_by(AiReview.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for r in pagination.items:
        triple_task = r.triple_task
        item = {
            "id": r.id,
            "triple_task_id": r.triple_task_id,
            "rule_filename": triple_task.rule_task.filename if triple_task and triple_task.rule_task else "",
            "model": r.model,
            "status": r.status,
            "score": r.score,
            "error_message": r.error_message,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
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
        },
    })


@ai_review_bp.route("/api/ai-review/<int:review_id>", methods=["GET"])
def get_ai_review(review_id):
    """AI审核详情"""
    ai_review = db.session.get(AiReview, review_id)
    if not ai_review:
        return jsonify({"code": -1, "message": "审核记录不存在"}), 404

    triple_task = ai_review.triple_task

    return jsonify({
        "code": 0,
        "data": {
            "id": ai_review.id,
            "triple_task_id": ai_review.triple_task_id,
            "model": ai_review.model,
            "status": ai_review.status,
            "score": ai_review.score,
            "dimensions": ai_review.dimensions,
            "suggestions": ai_review.suggestions,
            "summary": ai_review.summary,
            "error_message": ai_review.error_message,
            "triple_json": triple_task.triple_json if triple_task else None,
            "created_at": ai_review.created_at.isoformat() if ai_review.created_at else None,
            "reviewed_at": ai_review.reviewed_at.isoformat() if ai_review.reviewed_at else None,
        },
    })


@ai_review_bp.route("/api/ai-review/<int:review_id>/thinking", methods=["GET"])
def export_ai_review_thinking(review_id):
    """导出AI审核思考过程"""
    ai_review = db.session.get(AiReview, review_id)
    if not ai_review:
        return jsonify({"code": -1, "message": "审核记录不存在"}), 404

    from services.llm_service import get_ai_review_thinking
    data = get_ai_review_thinking(review_id)
    if not data:
        return jsonify({"code": -1, "message": "数据过期或数据未生成"}), 404

    model = data.get("model", "unknown")
    timestamp = data.get("timestamp", "")
    thinking = data.get("thinking", "")

    txt_content = (
        f"=== AI审核思考过程 ===\n"
        f"审核ID: {review_id}\n"
        f"模型: {model}\n"
        f"生成时间: {timestamp}\n"
        f"{'=' * 40}\n\n"
        f"{thinking}"
    )

    filename = f"ai_review_thinking_{review_id}.txt"
    return Response(
        txt_content,
        mimetype="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@ai_review_bp.route("/api/ai-review/<int:review_id>/retry", methods=["POST"])
def retry_ai_review(review_id):
    """重试失败的AI审核"""
    ai_review = db.session.get(AiReview, review_id)
    if not ai_review:
        return jsonify({"code": -1, "message": "审核记录不存在"}), 404
    if ai_review.status != "failed":
        return jsonify({"code": -1, "message": "只能重试失败的审核"}), 400

    ai_review.status = "pending"
    ai_review.error_message = None
    model = ai_review.model or "deepseek"
    db.session.commit()

    from tasks.ai_review_tasks import run_ai_review
    run_ai_review.delay(ai_review.id, ai_review.triple_task_id, model)

    return jsonify({"code": 0, "message": "重试已触发"})
