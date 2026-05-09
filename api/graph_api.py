from flask import Blueprint, request, jsonify
from services.graph_service import (
    get_all_labels,
    get_all_relationship_types,
    get_graph_data,
    get_shortest_path,
    search_nodes,
)

graph_bp = Blueprint("graph", __name__)


def _validate_list(param: str, allowed: list[str]) -> list[str]:
    """校验逗号分隔的参数是否在白名单内"""
    if not param:
        return []
    values = [v.strip() for v in param.split(",") if v.strip()]
    valid = [v for v in values if v in allowed]
    return valid


@graph_bp.route("/api/graph/labels", methods=["GET"])
def list_labels():
    """获取所有节点标签及数量"""
    labels = get_all_labels()
    return jsonify({"code": 0, "data": labels})


@graph_bp.route("/api/graph/relationship-types", methods=["GET"])
def list_rel_types():
    """获取所有关系类型及数量"""
    types = get_all_relationship_types()
    return jsonify({"code": 0, "data": types})


@graph_bp.route("/api/graph/graph", methods=["GET"])
def get_graph():
    """按标签和关系类型获取图谱数据"""
    labels_param = request.args.get("labels", "")
    rel_types_param = request.args.get("rel_types", "")
    limit = request.args.get("limit", 300, type=int)

    # 白名单校验
    allowed_labels = [l["label"] for l in get_all_labels()]
    allowed_types = [t["type"] for t in get_all_relationship_types()]

    labels = _validate_list(labels_param, allowed_labels)
    rel_types = _validate_list(rel_types_param, allowed_types)

    if not labels:
        return jsonify({"code": -1, "message": "请至少选择一个标签"}), 400

    data = get_graph_data(labels, rel_types, limit)
    return jsonify({"code": 0, "data": data})


@graph_bp.route("/api/graph/shortest-path", methods=["GET"])
def shortest_path():
    """查找最短路径"""
    start_label = request.args.get("start_label", "").strip()
    start_id = request.args.get("start_id", "").strip()
    end_label = request.args.get("end_label", "").strip()
    end_id = request.args.get("end_id", "").strip()

    if not all([start_label, start_id, end_label, end_id]):
        return jsonify({"code": -1, "message": "请指定完整的起始和目标节点"}), 400

    data = get_shortest_path(start_label, start_id, end_label, end_id)
    if not data:
        return jsonify({"code": 0, "data": None, "message": "未找到路径"})

    return jsonify({"code": 0, "data": data})


@graph_bp.route("/api/graph/search-nodes", methods=["GET"])
def search():
    """模糊搜索节点"""
    keyword = request.args.get("keyword", "").strip()
    limit = request.args.get("limit", 20, type=int)

    if not keyword:
        return jsonify({"code": 0, "data": []})

    data = search_nodes(keyword, limit)
    return jsonify({"code": 0, "data": data})
