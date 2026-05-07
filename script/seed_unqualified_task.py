"""
构造一条违反规则2-5的三元组测试数据，用于验证前端展示效果

规则2: Table3 实体不在 Table2 中 → 核心失真(浅红)
规则3: Table1 参数 key 未在 Table2 properties 中引用 → 核心失真(浅红)
规则4: display 命令 role 不是 [验证] → 核心失真(浅红)
规则5a: [执行]+PRE_STATE_desc 但缺少 source_verify_au → 严重缺陷(红)
规则5b: [执行]+PRE_STATE_desc 且 source_verify_au=MISSING_OBSERVER → 业务高危(黄)
"""

import json
import sys
import os

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import pymysql

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "QPAL624119",
    "database": "act",
}

# 构造违规的三元组数据
triple_json = {
    "Table1_Alignment": [
        {
            "row_index": 1,
            "raw_cmd": "display current-configuration interface {eth_trunk_disp}",
            "raw_rollback": "",
            "step_name": "步骤1-预检查",
            "au_name": "AU_precheck",
            "role": "[执行]",
            "entity": "Device:SW-10.1.1.1",
            "parameters": {
                "eth_trunk_disp": "Eth-Trunk 120",
                "PRE_STATE_desc": "检查接口当前状态"
            }
            # 违规: display命令但role=[执行] → 规则4
            # 违规: eth_trunk_disp 未被 Table2 properties 引用 → 规则3
            # 违规: 有 PRE_STATE_desc 但缺少 source_verify_au → 规则5a(严重缺陷)
        },
        {
            "row_index": 2,
            "raw_cmd": "shutdown Eth-Trunk 120",
            "raw_rollback": "undo shutdown Eth-Trunk 120",
            "step_name": "步骤2-执行",
            "au_name": "AU_exec",
            "role": "[执行]",
            "entity": "Device:SW-10.1.1.1",
            "parameters": {
                "PRE_STATE_desc": "检查邻居状态",
                "source_verify_au": "MISSING_OBSERVER"
            }
            # 违规: source_verify_au = MISSING_OBSERVER → 规则5b(业务高危)
        },
        {
            "row_index": 3,
            "raw_cmd": "display interface brief",
            "raw_rollback": "",
            "step_name": "步骤3-验证",
            "au_name": "AU_verify",
            "role": "[执行]",
            "entity": "Device:SW-10.1.1.1",
            "parameters": {}
            # 违规: display命令但role=[执行] → 规则4
        },
        {
            "row_index": 4,
            "raw_cmd": "ospf 100",
            "raw_rollback": "undo ospf 100",
            "step_name": "步骤4-执行",
            "au_name": "AU_ospf",
            "role": "[执行]",
            "entity": "Device:SW-10.1.1.1",
            "parameters": {
                "PRE_STATE_desc": "检查OSPF邻居",
                "source_verify_au": ""
            }
            # 违规: source_verify_au 为空字符串 → 规则5b(业务高危)
        },
        {
            "row_index": 5,
            "raw_cmd": "vlan 200",
            "raw_rollback": "undo vlan 200",
            "step_name": "步骤5-执行",
            "au_name": "AU_vlan",
            "role": "[执行]",
            "entity": "Device:SW-10.1.1.1",
            "parameters": {
                "PRE_STATE_desc": "检查VLAN状态"
            }
            # 违规: 有 PRE_STATE_desc 但缺少 source_verify_au → 规则5a(严重缺陷)
        }
    ],
    "Table2_Entities_Attributes": [
        {
            "id": "1",
            "label": "Device",
            "name": "SW-10.1.1.1",
            "properties": {
                "ip": "10.1.1.1",
                "vendor": "Huawei"
            }
            # 注意: properties 中没有 {eth_trunk_disp} 引用 → 规则3 触发
        }
    ],
    "Table3_Relations": [
        {
            "row_index": 1,
            "source_entity": "LogicalStep:01预检查配置",
            "target_entity": "Device:SW-10.1.1.1",
            "relation_type": "executes_on",
            "relation_attributes": {}
            # 违规: source_entity "LogicalStep:01预检查配置" 不在 Table2 中 → 规则2
        },
        {
            "row_index": 2,
            "source_entity": "Device:SW-10.1.1.1",
            "target_entity": "NetworkService:FTP服务",
            "relation_type": "depends_on",
            "relation_attributes": {}
            # 违规: target_entity "NetworkService:FTP服务" 不在 Table2 中 → 规则2
        }
    ]
}

# 构造校验结果（与 triple_validator.py 输出一致）
validation_result = {
    "passed": False,
    "violations": [
        {
            "rule": 2,
            "level": "核心失真",
            "color": "#FF9800",
            "message": "Table3_Relations 中有 2 个实体未在 Table2_Entities_Attributes 中定义",
            "locations": [
                {"table": "Table3_Relations", "row_index": 1, "field": "source_entity", "value": "LogicalStep:01预检查配置"},
                {"table": "Table3_Relations", "row_index": 2, "field": "target_entity", "value": "NetworkService:FTP服务"},
            ]
        },
        {
            "rule": 3,
            "level": "核心失真",
            "color": "#FF9800",
            "message": "Table1_Alignment 中有 1 个参数未在 Table2_Entities_Attributes 的 properties 中被引用",
            "locations": [
                {"table": "Table1_Alignment", "row_index": 1, "field": "parameters", "value": "eth_trunk_disp"},
            ]
        },
        {
            "rule": 4,
            "level": "核心失真",
            "color": "#FF9800",
            "message": "Table1_Alignment 中有 2 条 display 命令的 role 不是 [验证]",
            "locations": [
                {"table": "Table1_Alignment", "row_index": 1, "field": "role", "value": "[执行]", "expected": "[验证]", "raw_cmd": "display current-configuration interface {eth_trunk_disp}"},
                {"table": "Table1_Alignment", "row_index": 3, "field": "role", "value": "[执行]", "expected": "[验证]", "raw_cmd": "display interface brief"},
            ]
        },
        {
            "rule": 5,
            "level": "严重缺陷",
            "color": "#F56C6C",
            "message": "Table1_Alignment 中有 2 条 [执行] 记录含 PRE_STATE_desc 但缺少 source_verify_au",
            "locations": [
                {"table": "Table1_Alignment", "row_index": 1, "field": "parameters", "sub_key": "source_verify_au", "value": None, "PRE_STATE_desc": "检查接口当前状态", "issue": "缺少 source_verify_au 属性"},
                {"table": "Table1_Alignment", "row_index": 5, "field": "parameters", "sub_key": "source_verify_au", "value": None, "PRE_STATE_desc": "检查VLAN状态", "issue": "缺少 source_verify_au 属性"},
            ]
        },
        {
            "rule": 5,
            "level": "业务高危",
            "color": "#FF0000",
            "message": "Table1_Alignment 中有 2 条 [执行] 记录的 source_verify_au 值为空或 MISSING_OBSERVER",
            "locations": [
                {"table": "Table1_Alignment", "row_index": 2, "field": "parameters", "sub_key": "source_verify_au", "value": "MISSING_OBSERVER", "PRE_STATE_desc": "检查邻居状态", "issue": "source_verify_au 值无效: MISSING_OBSERVER"},
                {"table": "Table1_Alignment", "row_index": 4, "field": "parameters", "sub_key": "source_verify_au", "value": "", "PRE_STATE_desc": "检查OSPF邻居", "issue": "source_verify_au 值无效: "},
            ]
        },
    ]
}


def main():
    conn = pymysql.connect(**DB_CONFIG, charset="utf8mb4")
    cur = conn.cursor()

    # 查找一个可用的 rule_task_id
    cur.execute("SELECT id FROM rule_task WHERE status='success' AND is_deleted=0 LIMIT 1")
    row = cur.fetchone()
    if not row:
        # 创建一个临时规则任务
        cur.execute(
            "INSERT INTO rule_task (filename, status, extracted_json) VALUES (%s, %s, %s)",
            ("测试规则数据(校验测试用)", "success", json.dumps({"test": True}, ensure_ascii=False))
        )
        conn.commit()
        rule_task_id = cur.lastrowid
        print(f"创建临时规则任务 ID={rule_task_id}")
    else:
        rule_task_id = row[0]
        print(f"使用已有规则任务 ID={rule_task_id}")

    # 插入不合格的三元组任务
    cur.execute(
        "INSERT INTO triple_task (rule_task_id, model, status, triple_json, validation_result) VALUES (%s, %s, %s, %s, %s)",
        (
            rule_task_id,
            "GLM",
            "unqualified",
            json.dumps(triple_json, ensure_ascii=False),
            json.dumps(validation_result, ensure_ascii=False),
        )
    )
    conn.commit()
    task_id = cur.lastrowid
    print(f"已创建不合格三元组任务 ID={task_id}")
    print(f"  违规数: {len(validation_result['violations'])}")
    for v in validation_result["violations"]:
        print(f"  - 规则{v['rule']} | {v['level']} | {v['message']}")

    conn.close()


if __name__ == "__main__":
    main()
