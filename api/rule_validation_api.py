from flask import Blueprint, request, jsonify, Response
from models import db, TripleTask, RuleValidation
from services.xlsx_handler import export_triple_to_xlsx, import_xlsx_to_triple
from datetime import datetime
from sqlalchemy.orm import joinedload

rule_validation_bp = Blueprint("rule_validation", __name__)


@rule_validation_bp.route("/api/rule-validation/list", methods=["GET"])
def list_rule_validations():
    """规则审核列表：展示三元组转换成功的数据及其验证状态"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 15, type=int)

    # 查询所有成功的 TripleTask，LEFT JOIN RuleValidation，预加载 rule_task 消除 N+1
    query = db.session.query(TripleTask, RuleValidation).outerjoin(
        RuleValidation, TripleTask.id == RuleValidation.triple_task_id
    ).filter(TripleTask.status == "success").options(
        joinedload(TripleTask.rule_task)
    ).order_by(TripleTask.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for task, rv in pagination.items:
        items.append({
            "id": task.id,
            "rule_task_id": task.rule_task_id,
            "rule_filename": task.rule_task.filename if task.rule_task else "",
            "model": task.model,
            "status": rv.status if rv else "pending",
            "has_first_validation": bool(rv and rv.first_validation_result),
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
            "first_validation_result": rv.first_validation_result if rv else None,
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


@rule_validation_bp.route("/api/rule-validation/<int:triple_task_id>/export-xlsx", methods=["GET"])
def export_triple_xlsx(triple_task_id):
    """导出三元组数据为 xlsx 文件（3个sheet页）"""
    task = db.session.get(TripleTask, triple_task_id)
    if not task:
        return jsonify({"code": -1, "message": "任务不存在"}), 404

    if not task.triple_json:
        return jsonify({"code": -1, "message": "该任务没有三元组数据"}), 400

    try:
        # 生成 xlsx 文件
        xlsx_bytes = export_triple_to_xlsx(task.triple_json)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rule_validation_{triple_task_id}_{timestamp}.xlsx"

        return Response(
            xlsx_bytes.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        return jsonify({"code": -1, "message": f"导出失败: {str(e)}"}), 500


@rule_validation_bp.route("/api/rule-validation/<int:triple_task_id>/import-xlsx", methods=["POST"])
def import_triple_xlsx(triple_task_id):
    """导入 xlsx 文件，解析并返回 JSON 数据"""
    task = db.session.get(TripleTask, triple_task_id)
    if not task:
        return jsonify({"code": -1, "message": "任务不存在"}), 404

    # 检查文件
    if "file" not in request.files:
        return jsonify({"code": -1, "message": "未找到上传文件"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"code": -1, "message": "文件名为空"}), 400

    # 验证文件扩展名
    if not file.filename.lower().endswith(".xlsx"):
        return jsonify({"code": -1, "message": "只支持 .xlsx 格式文件"}), 400

    try:
        # 解析 xlsx 文件
        triple_data = import_xlsx_to_triple(file.stream)

        return jsonify({
            "code": 0,
            "message": "导入成功",
            "data": triple_data,
        })
    except ValueError as e:
        # 验证错误（格式不符合要求）
        return jsonify({"code": -1, "message": str(e)}), 400
    except Exception as e:
        # 其他错误
        return jsonify({"code": -1, "message": f"导入失败: {str(e)}"}), 500
