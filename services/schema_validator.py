REQUIRED_TOP_KEYS = [
    "Table1_Alignment",
    "Table2_Entities_Attributes",
    "Table3_Relations",
]

TABLE1_REQUIRED_FIELDS = {"row_index", "raw_cmd", "step_name", "au_name", "role", "entity", "parameters"}
TABLE2_REQUIRED_FIELDS = {"id", "label", "name", "properties"}
TABLE2_LABEL_ENUM = {"Scenario", "LogicalStep", "ActionUnit", "CLITemplate", "NetworkEntity", "Parameter"}
TABLE3_REQUIRED_FIELDS = {"source_entity", "relation_type", "target_entity", "relation_attributes"}


def validate_output(data: dict) -> None:
    for key in REQUIRED_TOP_KEYS:
        if key not in data:
            raise ValueError(f"输出 JSON 缺少必要顶层 key: {key}")

    for key in REQUIRED_TOP_KEYS:
        if not isinstance(data[key], list):
            raise ValueError(f"{key} 必须是 array，实际类型: {type(data[key]).__name__}")

    for i, row in enumerate(data["Table1_Alignment"]):
        missing = TABLE1_REQUIRED_FIELDS - set(row.keys())
        if missing:
            raise ValueError(f"Table1_Alignment[{i}] 缺少必要字段: {missing}")
        if not isinstance(row.get("parameters"), dict):
            raise ValueError(f"Table1_Alignment[{i}].parameters 必须是 object")

    for i, node in enumerate(data["Table2_Entities_Attributes"]):
        missing = TABLE2_REQUIRED_FIELDS - set(node.keys())
        if missing:
            raise ValueError(f"Table2_Entities_Attributes[{i}] 缺少必要字段: {missing}")
        label = node.get("label")
        if label not in TABLE2_LABEL_ENUM:
            raise ValueError(
                f"Table2_Entities_Attributes[{i}].label 非法值: '{label}'，必须是 {TABLE2_LABEL_ENUM}"
            )
        if not isinstance(node.get("properties"), dict):
            raise ValueError(f"Table2_Entities_Attributes[{i}].properties 必须是 object")

    for i, rel in enumerate(data["Table3_Relations"]):
        missing = TABLE3_REQUIRED_FIELDS - set(rel.keys())
        if missing:
            raise ValueError(f"Table3_Relations[{i}] 缺少必要字段: {missing}")
