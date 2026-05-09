from neo4j import GraphDatabase
from config import NEO4J_CONFIG
from services.neo4j_service import get_driver


def _serialize_node(node) -> dict:
    """将 Neo4j node 序列化为前端可用的 dict"""
    props = dict(node)
    props.pop("id", None)  # id 单独提取
    return {
        "id": node["id"] if "id" in node else node.element_id,
        "labels": list(node.labels),
        "name": node.get("name", ""),
        "properties": props,
    }


def _serialize_rel(rel) -> dict:
    """将 Neo4j relationship 序列化为前端可用的 dict"""
    return {
        "id": rel.element_id,
        "source": rel.start_node["id"] if "id" in rel.start_node else rel.start_node.element_id,
        "target": rel.end_node["id"] if "id" in rel.end_node else rel.end_node.element_id,
        "type": rel.type,
        "properties": dict(rel),
    }


def get_all_labels() -> list[dict]:
    """获取所有节点标签及数量"""
    driver = get_driver()
    try:
        with driver.session(database=NEO4J_CONFIG.get("database", "neo4j")) as session:
            result = session.run("CALL db.labels() YIELD label RETURN label ORDER BY label")
            labels = []
            for record in result:
                label = record["label"]
                count_result = session.run(
                    f"MATCH (n:`{label}`) RETURN count(n) AS cnt"
                )
                cnt = count_result.single()["cnt"]
                labels.append({"label": label, "count": cnt})
            return labels
    finally:
        driver.close()


def get_all_relationship_types() -> list[dict]:
    """获取所有关系类型及数量"""
    driver = get_driver()
    try:
        with driver.session(database=NEO4J_CONFIG.get("database", "neo4j")) as session:
            result = session.run(
                "CALL db.relationshipTypes() YIELD relationshipType "
                "RETURN relationshipType AS type ORDER BY type"
            )
            types = []
            for record in result:
                rel_type = record["type"]
                count_result = session.run(
                    f"MATCH ()-[r:`{rel_type}`]->() RETURN count(r) AS cnt"
                )
                cnt = count_result.single()["cnt"]
                types.append({"type": rel_type, "count": cnt})
            return types
    finally:
        driver.close()


def get_graph_data(labels: list[str], rel_types: list[str], limit: int = 300) -> dict:
    """按标签和关系类型筛选图谱数据（节点+边）"""
    driver = get_driver()
    try:
        with driver.session(database=NEO4J_CONFIG.get("database", "neo4j")) as session:
            label_conditions = " OR ".join([f'"{l}" IN labels(n)' for l in labels])
            type_conditions = ", ".join([f'"{t}"' for t in rel_types])

            query = f"""
                MATCH (n)-[r]->(m)
                WHERE ({label_conditions})
                  AND type(r) IN [{type_conditions}]
                RETURN n, r, m
                LIMIT {int(limit)}
            """
            result = session.run(query)

            nodes_map = {}
            edges = []
            for record in result:
                for node_key in ("n", "m"):
                    node = record[node_key]
                    node_id = node["id"] if "id" in node else node.element_id
                    if node_id not in nodes_map:
                        nodes_map[node_id] = _serialize_node(node)
                rel = record["r"]
                edges.append(_serialize_rel(rel))

            return {"nodes": list(nodes_map.values()), "edges": edges}
    finally:
        driver.close()


def get_shortest_path(start_label: str, start_id: str, end_label: str, end_id: str) -> dict | None:
    """查找两个节点之间的最短路径"""
    driver = get_driver()
    try:
        with driver.session(database=NEO4J_CONFIG.get("database", "neo4j")) as session:
            query = f"""
                MATCH (start:`{start_label}` {{id: $start_id}}),
                      (end:`{end_label}` {{id: $end_id}})
                MATCH p = shortestPath((start)-[*]-(end))
                RETURN p
            """
            result = session.run(query, start_id=start_id, end_id=end_id)
            record = result.single()
            if not record:
                return None

            path = record["p"]
            nodes = []
            for node in path.nodes:
                node_id = node["id"] if "id" in node else node.element_id
                nodes.append(_serialize_node(node))

            edges = []
            for rel in path.relationships:
                edges.append(_serialize_rel(rel))

            return {"nodes": nodes, "edges": edges, "length": len(edges)}
    finally:
        driver.close()


def search_nodes(keyword: str, limit: int = 20) -> list[dict]:
    """模糊搜索节点（按 name 或 id 匹配）"""
    driver = get_driver()
    try:
        with driver.session(database=NEO4J_CONFIG.get("database", "neo4j")) as session:
            query = """
                MATCH (n)
                WHERE n.name CONTAINS $keyword OR n.id CONTAINS $keyword
                RETURN n LIMIT $limit
            """
            result = session.run(query, keyword=keyword, limit=int(limit))
            return [_serialize_node(record["n"]) for record in result]
    finally:
        driver.close()
