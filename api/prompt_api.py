from flask import Blueprint, request, jsonify
from services.prompt_service import (
    list_prompts,
    get_prompt_detail,
    create_prompt,
    update_prompt,
    delete_prompt,
    get_prompt_history,
    get_prompt_options,
    activate_prompt,
)

prompt_bp = Blueprint("prompt", __name__)


@prompt_bp.route("/api/prompt/list", methods=["GET"])
def list_prompt_configs():
    ptype = request.args.get("type", "extraction")
    if ptype not in ("extraction", "review"):
        return jsonify({"code": -1, "message": "type 参数无效"}), 400
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 15, type=int)
    search = request.args.get("search", "").strip()

    pagination = list_prompts(ptype, page, per_page, search)
    items = [
        {
            "id": p.id,
            "name": p.name,
            "type": p.type,
            "version": p.version,
            "is_builtin": p.is_builtin,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in pagination.items
    ]
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


@prompt_bp.route("/api/prompt/detail/<int:prompt_id>", methods=["GET"])
def get_prompt_config(prompt_id):
    prompt = get_prompt_detail(prompt_id)
    if not prompt or prompt.is_deleted:
        return jsonify({"code": -1, "message": "提示词不存在"}), 404
    return jsonify({
        "code": 0,
        "data": {
            "id": prompt.id,
            "name": prompt.name,
            "type": prompt.type,
            "content": prompt.content,
            "version": prompt.version,
            "is_builtin": prompt.is_builtin,
            "is_current": prompt.is_current,
            "changelog": prompt.changelog,
            "created_at": prompt.created_at.isoformat() if prompt.created_at else None,
            "updated_at": prompt.updated_at.isoformat() if prompt.updated_at else None,
        },
    })


@prompt_bp.route("/api/prompt/create", methods=["POST"])
def create_prompt_config():
    data = request.get_json()
    if not data or not data.get("name") or not data.get("type") or not data.get("content"):
        return jsonify({"code": -1, "message": "名称、类型和内容不能为空"}), 400
    ptype = data["type"]
    if ptype not in ("extraction", "review"):
        return jsonify({"code": -1, "message": "type 参数无效"}), 400

    # 检查同名
    from models import PromptConfig
    exists = PromptConfig.query.filter_by(
        name=data["name"], type=ptype, is_deleted=False, is_current=True
    ).first()
    if exists:
        return jsonify({"code": -1, "message": "该类型下已存在同名提示词"}), 400

    prompt = create_prompt(data["name"], ptype, data["content"], changelog=data.get("changelog"))
    return jsonify({
        "code": 0,
        "message": "创建成功",
        "data": {"id": prompt.id},
    })


@prompt_bp.route("/api/prompt/update/<int:prompt_id>", methods=["PUT"])
def update_prompt_config(prompt_id):
    data = request.get_json()
    if not data or not data.get("content"):
        return jsonify({"code": -1, "message": "内容不能为空"}), 400

    prompt = update_prompt(prompt_id, data["content"], changelog=data.get("changelog"))
    if not prompt:
        return jsonify({"code": -1, "message": "提示词不存在或已删除"}), 404
    return jsonify({
        "code": 0,
        "message": "更新成功（已创建新版本）",
        "data": {"id": prompt.id, "version": prompt.version},
    })


@prompt_bp.route("/api/prompt/delete/<int:prompt_id>", methods=["DELETE"])
def delete_prompt_config(prompt_id):
    if delete_prompt(prompt_id):
        return jsonify({"code": 0, "message": "删除成功"})
    return jsonify({"code": -1, "message": "提示词不存在"}), 404


@prompt_bp.route("/api/prompt/history/<name>", methods=["GET"])
def get_prompt_history_configs(name):
    ptype = request.args.get("type", "extraction")
    records = get_prompt_history(name, ptype)
    items = [
        {
            "id": r.id,
            "name": r.name,
            "type": r.type,
            "content": r.content,
            "version": r.version,
            "is_current": r.is_current,
            "is_builtin": r.is_builtin,
            "changelog": r.changelog,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in records
    ]
    return jsonify({"code": 0, "data": items})


@prompt_bp.route("/api/prompt/options", methods=["GET"])
def get_prompt_option_list():
    ptype = request.args.get("type", "extraction")
    if ptype not in ("extraction", "review"):
        return jsonify({"code": -1, "message": "type 参数无效"}), 400
    records = get_prompt_options(ptype)
    items = [{"id": r.id, "name": r.name} for r in records]
    return jsonify({"code": 0, "data": items})


@prompt_bp.route("/api/prompt/activate/<int:prompt_id>", methods=["POST"])
def activate_prompt_config(prompt_id):
    prompt = activate_prompt(prompt_id)
    if not prompt:
        return jsonify({"code": -1, "message": "提示词不存在或已删除"}), 404
    return jsonify({
        "code": 0,
        "message": f"已启用版本 v{prompt.version}",
        "data": {"id": prompt.id, "version": prompt.version},
    })
