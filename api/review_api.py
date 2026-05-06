from flask import Blueprint, request, jsonify
from models import db, TripleTask, TripleReview, now_cn

review_bp = Blueprint("review", __name__)


@review_bp.route("/api/review/list", methods=["GET"])
def list_pending_reviews():
    """获取待审核列表：triple_task中status=success且尚未审核通过的"""
    # 查询已审核通过的 triple_task_id
    approved_ids = db.session.query(TripleReview.triple_task_id).filter(
        TripleReview.review_status == "approved"
    ).subquery()

    query = TripleTask.query.filter(
        TripleTask.status == "success",
        ~TripleTask.id.in_(approved_ids)
    ).order_by(TripleTask.created_at.desc())

    tasks = query.all()
    items = []
    for t in tasks:
        # 检查是否有待审核或驳回的记录
        existing_review = TripleReview.query.filter_by(triple_task_id=t.id).order_by(TripleReview.created_at.desc()).first()
        items.append({
            "id": t.id,
            "rule_task_id": t.rule_task_id,
            "rule_filename": t.rule_task.filename if t.rule_task else "",
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "review_status": existing_review.review_status if existing_review else None,
            "review_id": existing_review.id if existing_review else None,
        })

    return jsonify({"code": 0, "data": items})


@review_bp.route("/api/review/<int:triple_task_id>", methods=["GET"])
def get_review_data(triple_task_id):
    """获取三元组三表数据用于展示和编辑"""
    triple_task = db.session.get(TripleTask, triple_task_id)
    if not triple_task:
        return jsonify({"code": -1, "message": "三元组任务不存在"}), 404

    # 检查是否有已保存的审核草稿
    existing_review = TripleReview.query.filter_by(
        triple_task_id=triple_task_id
    ).order_by(TripleReview.created_at.desc()).first()

    if existing_review and existing_review.reviewed_json:
        data = existing_review.reviewed_json
    else:
        data = triple_task.triple_json or {}

    return jsonify({
        "code": 0,
        "data": {
            "triple_task_id": triple_task_id,
            "table1": data.get("Table1_Alignment", []),
            "table2": data.get("Table2_Entities_Attributes", []),
            "table3": data.get("Table3_Relations", []),
            "review_id": existing_review.id if existing_review else None,
            "review_status": existing_review.review_status if existing_review else None,
        }
    })


@review_bp.route("/api/review/<int:triple_task_id>/submit", methods=["POST"])
def submit_review(triple_task_id):
    """提交审核结果"""
    data = request.get_json()
    if not data:
        return jsonify({"code": -1, "message": "缺少审核数据"}), 400

    table1 = data.get("table1", [])
    table2 = data.get("table2", [])
    table3 = data.get("table3", [])
    review_status = data.get("review_status", "approved")
    reviewer = data.get("reviewer", "")

    reviewed_json = {
        "Table1_Alignment": table1,
        "Table2_Entities_Attributes": table2,
        "Table3_Relations": table3,
    }

    # Upsert: 如果已有记录则更新，否则新建
    existing = TripleReview.query.filter_by(triple_task_id=triple_task_id).order_by(TripleReview.created_at.desc()).first()
    if existing:
        existing.reviewed_json = reviewed_json
        existing.review_status = review_status
        existing.reviewer = reviewer
        existing.review_time = now_cn()
        review_id = existing.id
    else:
        review = TripleReview(
            triple_task_id=triple_task_id,
            reviewed_json=reviewed_json,
            review_status=review_status,
            reviewer=reviewer,
            review_time=now_cn(),
        )
        db.session.add(review)
        db.session.flush()
        review_id = review.id

    db.session.commit()

    return jsonify({
        "code": 0,
        "message": "审核提交成功",
        "data": {"review_id": review_id, "review_status": review_status}
    })


@review_bp.route("/api/review/approved", methods=["GET"])
def list_approved_reviews():
    """获取已审核通过的列表（供模块D使用）"""
    reviews = TripleReview.query.filter_by(review_status="approved").order_by(TripleReview.review_time.desc()).all()
    items = []
    for r in reviews:
        items.append({
            "id": r.id,
            "triple_task_id": r.triple_task_id,
            "reviewer": r.reviewer,
            "review_time": r.review_time.isoformat() if r.review_time else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return jsonify({"code": 0, "data": items})


@review_bp.route("/api/review/rejected", methods=["GET"])
def list_rejected_reviews():
    """获取已驳回的审核列表"""
    reviews = TripleReview.query.filter_by(review_status="rejected").order_by(TripleReview.review_time.desc()).all()
    items = []
    for r in reviews:
        items.append({
            "id": r.id,
            "triple_task_id": r.triple_task_id,
            "reviewer": r.reviewer,
            "review_time": r.review_time.isoformat() if r.review_time else None,
            "rule_filename": r.triple_task.rule_task.filename if r.triple_task and r.triple_task.rule_task else "",
        })
    return jsonify({"code": 0, "data": items})
