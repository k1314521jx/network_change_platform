from neo4j import GraphDatabase
from config import NEO4J_CONFIG


def get_driver():
    return GraphDatabase.driver(
        NEO4J_CONFIG["uri"],
        auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"]),
    )


def import_triples_to_neo4j(reviewed_json: dict) -> int:
    """
    将审核后的三元组数据写入 Neo4j。
    返回创建的节点和关系总数。
    """
    driver = get_driver()
    entities = reviewed_json.get("Table2_Entities_Attributes", [])
    relations = reviewed_json.get("Table3_Relations", [])

    with driver.session(database=NEO4J_CONFIG.get("database", "neo4j")) as session:
        # 创建节点
        for entity in entities:
            label = entity.get("label", "Entity")
            safe_label = label.replace(" ", "_")
            entity_id = entity.get("id", "")
            name = entity.get("name", "")
            props = entity.get("properties", {})

            session.run(
                f"""
                MERGE (n:{safe_label} {{id: $id}})
                SET n.name = $name, n += $props
                """,
                id=entity_id,
                name=name,
                props=props if props else {},
            )

        # 创建关系
        for rel in relations:
            source = rel.get("source_entity", "")
            target = rel.get("target_entity", "")
            rel_type = rel.get("relation_type", "RELATED_TO")
            rel_attrs = rel.get("relation_attributes", "")

            # 解析 source_entity 格式: "Label:ID"
            if ":" in source:
                src_label, src_id = source.split(":", 1)
            else:
                src_label, src_id = "Entity", source

            if ":" in target:
                tgt_label, tgt_id = target.split(":", 1)
            else:
                tgt_label, tgt_id = "Entity", target

            safe_rel_type = rel_type.replace(" ", "_").upper()

            session.run(
                f"""
                MATCH (a:{src_label.replace(' ', '_')} {{id: $src_id}})
                MATCH (b:{tgt_label.replace(' ', '_')} {{id: $tgt_id}})
                MERGE (a)-[r:{safe_rel_type}]->(b)
                SET r.attributes = $attrs
                """,
                src_id=src_id.strip(),
                tgt_id=tgt_id.strip(),
                attrs=rel_attrs,
            )

    driver.close()
    return len(entities) + len(relations)


def test_neo4j_connection() -> bool:
    """测试 Neo4j 连接"""
    try:
        driver = get_driver()
        with driver.session(database=NEO4J_CONFIG.get("database", "neo4j")) as session:
            session.run("RETURN 1")
        driver.close()
        return True
    except Exception:
        return False
