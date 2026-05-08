from flask import Blueprint, request, jsonify
from services.model_service import (
    list_models,
    get_model_detail,
    create_model,
    update_model,
    delete_model,
    get_model_options,
    test_model_connection,
)

model_bp = Blueprint("model", __name__)


@model_bp.route("/api/model/list", methods=["GET"])
def list_model_configs():
    records = list_models()
    items = [
        {
            "id": r.id,
            "name": r.name,
            "api_key": r.api_key[:8] + "..." if r.api_key else "",
            "base_url": r.base_url,
            "model": r.model,
            "is_active": r.is_active,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in records
    ]
    return jsonify({"code": 0, "data": items})


@model_bp.route("/api/model/detail/<int:model_id>", methods=["GET"])
def get_model_config(model_id):
    m = get_model_detail(model_id)
    if not m or m.is_deleted:
        return jsonify({"code": -1, "message": "模型不存在"}), 404
    return jsonify({
        "code": 0,
        "data": {
            "id": m.id,
            "name": m.name,
            "api_key": m.api_key,
            "base_url": m.base_url,
            "model": m.model,
            "is_active": m.is_active,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None,
        },
    })


@model_bp.route("/api/model/create", methods=["POST"])
def create_model_config():
    data = request.get_json()
    if not data or not all(data.get(k) for k in ("name", "api_key", "base_url", "model")):
        return jsonify({"code": -1, "message": "名称、API Key、Base URL、模型ID 不能为空"}), 400

    m = create_model(data["name"], data["api_key"], data["base_url"], data["model"])
    if not m:
        return jsonify({"code": -1, "message": "模型名称已存在"}), 400
    return jsonify({"code": 0, "message": "创建成功", "data": {"id": m.id}})


@model_bp.route("/api/model/update/<int:model_id>", methods=["PUT"])
def update_model_config(model_id):
    data = request.get_json()
    if not data:
        return jsonify({"code": -1, "message": "缺少参数"}), 400

    m = update_model(model_id, **data)
    if not m:
        return jsonify({"code": -1, "message": "模型不存在或名称冲突"}), 400
    return jsonify({"code": 0, "message": "更新成功", "data": {"id": m.id}})


@model_bp.route("/api/model/delete/<int:model_id>", methods=["DELETE"])
def delete_model_config(model_id):
    if delete_model(model_id):
        return jsonify({"code": 0, "message": "删除成功"})
    return jsonify({"code": -1, "message": "模型不存在"}), 404


@model_bp.route("/api/model/options", methods=["GET"])
def get_model_option_list():
    records = get_model_options()
    items = [{"id": r.id, "name": r.name, "model": r.model} for r in records]
    return jsonify({"code": 0, "data": items})


@model_bp.route("/api/model/test", methods=["POST"])
def test_connection():
    data = request.get_json()
    if not data or not all(data.get(k) for k in ("api_key", "base_url", "model")):
        return jsonify({"code": -1, "message": "API Key、Base URL、模型ID 不能为空"}), 400

    ok, msg = test_model_connection(data["api_key"], data["base_url"], data["model"])
    if ok:
        return jsonify({"code": 0, "message": msg})
    return jsonify({"code": -1, "message": f"连接失败: {msg}"})
