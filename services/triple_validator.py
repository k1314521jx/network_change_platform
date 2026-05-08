"""
三元组数据校验服务

5条规则检查LLM输出的三元组数据质量，返回结构化的校验结果。
"""

RISK_CRITICAL = "严重缺陷"
RISK_HIGH = "业务高危"
RISK_CORE = "核心失真"

COLOR_CRITICAL = "#F56C6C"
COLOR_HIGH = "#FF0000"
COLOR_CORE = "#FF9800"

# role 字段规范化映射：LLM 可能输出 "验证"/"[验证]" 等不同格式
_ROLE_NORMALIZE = {
    "验证": "验证", "[验证]": "验证",
    "执行": "执行", "[执行]": "执行",
    "预检查": "预检查", "[预检查]": "预检查",
    "回退": "回退", "[回退]": "回退",
}


def _normalize_role(role: str) -> str:
    """将 role 字段规范化，兼容带/不带方括号的格式"""
    return _ROLE_NORMALIZE.get(role, role)


def validate_triple(data: dict) -> dict:
    """校验三元组数据，返回校验结果"""
    violations = []

    _check_rule1(data, violations)
    _check_rule2(data, violations)
    _check_rule3(data, violations)
    _check_rule4(data, violations)
    _check_rule5(data, violations)

    return {
        "passed": len(violations) == 0,
        "violations": violations,
    }


def _check_rule1(data, violations):
    """规则1: 必须包含三大基础数组"""
    required_tables = ["Table1_Alignment", "Table2_Entities_Attributes", "Table3_Relations"]
    missing = [t for t in required_tables if t not in data or not isinstance(data[t], list)]
    if missing:
        violations.append({
            "rule": 1,
            "level": RISK_CRITICAL,
            "color": COLOR_CRITICAL,
            "message": f"缺少基础数组: {', '.join(missing)}",
            "locations": [],
        })


def _check_rule2(data, violations):
    """规则2: Table3的实体必须在Table2中存在"""
    table2 = data.get("Table2_Entities_Attributes", [])
    table3 = data.get("Table3_Relations", [])
    if not table2 or not table3:
        return

    # 构建 Table2 实体集合 "label:name"
    entities_set = set()
    for item in table2:
        label = item.get("label", "")
        name = item.get("name", "")
        if label and name:
            entities_set.add(f"{label}:{name}")

    locations = []
    for i, rel in enumerate(table3):
        for field in ("source_entity", "target_entity"):
            val = rel.get(field, "")
            if val and val not in entities_set:
                locations.append({
                    "table": "Table3_Relations",
                    "row_index": rel.get("row_index", i + 1),
                    "field": field,
                    "value": val,
                })

    if locations:
        missing_entities = sorted(set(loc["value"] for loc in locations))
        entity_list = "、".join(missing_entities)
        violations.append({
            "rule": 2,
            "level": RISK_CORE,
            "color": COLOR_CORE,
            "message": f"Table3_Relations 中有 {len(locations)} 个实体未在 Table2_Entities_Attributes 中定义: {entity_list}",
            "locations": locations,
        })


def _check_rule3(data, violations):
    """规则3: Table1的parameters key必须在Table2的properties中被{key}引用"""
    table1 = data.get("Table1_Alignment", [])
    table2 = data.get("Table2_Entities_Attributes", [])
    if not table1 or not table2:
        return

    # 收集 Table2 properties 中所有 {key} 引用
    referenced_keys = set()
    for item in table2:
        props = item.get("properties", {})
        if isinstance(props, dict):
            for v in props.values():
                if isinstance(v, str):
                    import re
                    for m in re.finditer(r'\{(\w+)\}', v):
                        referenced_keys.add(m.group(1))

    # 检查 Table1 parameters 中的 key 是否被引用
    locations = []
    unreferenced_keys = set()
    for i, item in enumerate(table1):
        params = item.get("parameters", {})
        if not params or not isinstance(params, dict):
            continue
        for key in params:
            if key not in referenced_keys:
                unreferenced_keys.add(key)
                locations.append({
                    "table": "Table1_Alignment",
                    "row_index": item.get("row_index", i + 1),
                    "field": "parameters",
                    "value": key,
                })

    if locations:
        key_list = "、".join(sorted(unreferenced_keys))
        violations.append({
            "rule": 3,
            "level": RISK_CORE,
            "color": COLOR_CORE,
            "message": f"Table1_Alignment 中有 {len(locations)} 个参数未在 Table2_Entities_Attributes 的 properties 中被引用: {key_list}",
            "locations": locations,
        })


def _check_rule4(data, violations):
    """规则4: raw_cmd 包含 display 的行 role 必须是验证"""
    table1 = data.get("Table1_Alignment", [])
    if not table1:
        return

    locations = []
    for i, item in enumerate(table1):
        raw_cmd = item.get("raw_cmd", "")
        role = item.get("role", "")
        if isinstance(raw_cmd, str) and "display" in raw_cmd.lower():
            if _normalize_role(role) != "验证":
                locations.append({
                    "table": "Table1_Alignment",
                    "row_index": item.get("row_index", i + 1),
                    "field": "role",
                    "value": role,
                    "expected": "验证",
                    "raw_cmd": raw_cmd,
                })

    if locations:
        violations.append({
            "rule": 4,
            "level": RISK_CORE,
            "color": COLOR_CORE,
            "message": f"Table1_Alignment 中有 {len(locations)} 条 display 命令的 role 不是验证",
            "locations": locations,
        })


def _check_rule5(data, violations):
    """规则5: role=[执行] 且 parameters 含 PRE_STATE_ 前缀变量时，source_verify_au 必须存在且非空"""
    table1 = data.get("Table1_Alignment", [])
    if not table1:
        return

    critical_locations = []
    high_locations = []

    for i, item in enumerate(table1):
        role = item.get("role", "")
        if _normalize_role(role) != "执行":
            continue
        params = item.get("parameters", {})
        if not isinstance(params, dict):
            continue

        pre_state_keys = [k for k in params if k.startswith("PRE_STATE_")]
        if not pre_state_keys:
            continue

        loc_base = {
            "table": "Table1_Alignment",
            "row_index": item.get("row_index", i + 1),
            "field": "parameters",
            "sub_key": "source_verify_au",
            "PRE_STATE_keys": pre_state_keys,
        }

        if "source_verify_au" not in params:
            loc_base["value"] = None
            loc_base["issue"] = "缺少 source_verify_au 属性"
            critical_locations.append(loc_base)
        else:
            val = params["source_verify_au"]
            if not val or val == "MISSING_OBSERVER":
                loc_base["value"] = val
                loc_base["issue"] = f"source_verify_au 值无效: {val}"
                high_locations.append(loc_base)

    if critical_locations:
        violations.append({
            "rule": 5,
            "level": RISK_CRITICAL,
            "color": COLOR_CRITICAL,
            "message": f"Table1_Alignment 中有 {len(critical_locations)} 条 [执行] 记录含 PRE_STATE_desc 但缺少 source_verify_au",
            "locations": critical_locations,
        })
    if high_locations:
        violations.append({
            "rule": 5,
            "level": RISK_HIGH,
            "color": COLOR_HIGH,
            "message": f"Table1_Alignment 中有 {len(high_locations)} 条 [执行] 记录的 source_verify_au 值为空或 MISSING_OBSERVER",
            "locations": high_locations,
        })
