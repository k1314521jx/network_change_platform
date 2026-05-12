from flask import Blueprint, request, jsonify
from models import db, TripleReview, Neo4jImportLog
from services.neo4j_service import import_triples_to_neo4j, test_neo4j_connection

neo4j_bp = Blueprint("neo4j", __name__)


@neo4j_bp.route("/api/neo4j/import", methods=["POST"])
def import_to_neo4j():
    """批量将审核通过的三元组数据写入Neo4j（同步操作）"""
    data = request.get_json()
    if not data or "review_ids" not in data:
        return jsonify({"code": -1, "message": "请选择要入库的审核记录"}), 400

    review_ids = data["review_ids"]
    force = data.get("force", False)
    if not isinstance(review_ids, list) or len(review_ids) == 0:
        return jsonify({"code": -1, "message": "请选择至少一条审核记录"}), 400

    # 检查Neo4j连接
    if not test_neo4j_connection():
        return jsonify({"code": -1, "message": "Neo4j 连接失败，请检查服务是否启动"}), 500

    results = []
    for review_id in review_ids:
        review = db.session.get(TripleReview, review_id)
        if not review or review.review_status != "approved":
            results.append({
                "review_id": review_id,
                "status": "failed",
                "error": "审核记录不存在或未通过审核"
            })
            continue

        # 检查是否已成功入库（force 模式跳过此检查）
        if not force:
            existing_log = Neo4jImportLog.query.filter_by(
                triple_review_id=review_id, status="success"
            ).first()
            if existing_log:
                results.append({
                    "review_id": review_id,
                    "status": "failed",
                    "error": "该记录已成功入库，请勿重复导入"
                })
                continue

        try:
            count = import_triples_to_neo4j(review.reviewed_json)
            # force 模式下更新旧日志，否则新建
            existing_log = Neo4jImportLog.query.filter_by(
                triple_review_id=review_id, status="success"
            ).first()
            if existing_log:
                existing_log.status = "success"
                existing_log.error_message = ""
            else:
                log = Neo4jImportLog(
                    triple_review_id=review_id,
                    status="success",
                    error_message="",
                )
                db.session.add(log)
            db.session.commit()
            results.append({
                "review_id": review_id,
                "status": "success",
                "count": count
            })
        except Exception as e:
            log = Neo4jImportLog(
                triple_review_id=review_id,
                status="failed",
                error_message=str(e),
            )
            db.session.add(log)
            db.session.commit()
            results.append({
                "review_id": review_id,
                "status": "failed",
                "error": str(e)
            })

    success_count = sum(1 for r in results if r["status"] == "success")
    fail_count = sum(1 for r in results if r["status"] == "failed")

    return jsonify({
        "code": 0,
        "message": f"入库完成：成功 {success_count} 条，失败 {fail_count} 条",
        "data": results
    })


@neo4j_bp.route("/api/neo4j/logs", methods=["GET"])
def list_import_logs():
    """获取入库日志列表"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = Neo4jImportLog.query.order_by(Neo4jImportLog.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for log in pagination.items:
        items.append({
            "id": log.id,
            "triple_review_id": log.triple_review_id,
            "status": log.status,
            "error_message": log.error_message,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    return jsonify({
        "code": 0,
        "data": {
            "items": items,
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
        }
    })


@neo4j_bp.route("/api/neo4j/status", methods=["GET"])
def neo4j_status():
    """检查Neo4j连接状态"""
    ok = test_neo4j_connection()
    return jsonify({"code": 0, "data": {"connected": ok}})
