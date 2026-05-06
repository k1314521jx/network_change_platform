import json
from models import db, RuleTask
from tasks.celery_app import celery

# 模拟返回的示例 JSON（来自 [REF: 引用<b>]）
SAMPLE_EXTRACTED_JSON = {
    "name": "003INT南京杭州西安POP TDSW对接NP及NP设备配置整改",
    "demand_info": {
        "device_info": [
            "CN-NJ-NKG-NE8000F1A-TRANSITWAN-P02-PGW01-99.99.236.94",
            "J-NKG-NE8000F1A-TRANSITWAN-P02-PGW02-99.99.236.95",
            "CN-HZ-HGH-NE8000F1A-TRANSITWAN-P02-PGW01-99.99.232.92",
            "CN-HZ-HGH-NE8000F1A-TRANSITWAN-P02-PGW02-99.99.232.93",
            "CN-HZ-HGY-NE8000F1A-TRANSITWAN-P01-PGW01-99.99.52.92",
            "CN-HZ-HGY-NE8000F1A-TRANSITWAN-P01-PGW02-99.99.52.93",
            "CN-XA-SJHL-NE8000F1A-TRANSITWAN-P01-PGW01-99.99.228.84",
            "CN-XA-SJHL-NE8000F1A-TRANSITWAN-P01-PGW02-99.99.228.85",
            "CN-XA-XG-NE8000F1A-TRANSITWAN-P02-PGW01-99.99.230.86",
            "CN-XA-XG-NE8000F1A-TRANSITWAN-P02-PGW02-99.99.230.87",
            "CN-NJ-NKG-FM8850-P01-TDSW01-99.99.236.74",
            "CN-NJ-NKG-FM8850-P01-TDSW02-99.99.236.75",
            "CN-HZ-HYS-FMB850-P01-TDSW01-99.99.232.86",
            "CN-HZ-HYS-FM8850-P01-TDSW02-99.99.232.87",
            "CN-HZ-HGY-FM8850-P02-TDSW01-99.99.52.86",
            "CN-HZ-HGY-FM8850-P02-TDSW02-99.99.52.87",
            "CN-XA-SJHL-FMB850-P01-TDSW01-99.99.228.25",
            "CN-XA-SJHL-FM8850-P01-TDSW02-99.99.228.29",
            "CN-XA-XG-FM8850-P02-TDSW01-99.99.230.84",
            "CN-XA-XG-FM8850-P02-TDSW02-99.99.230.85"
        ],
        "implementation_step": [
            "1.南京、杭州和西安POP新建NP,目前已完成链路调测和链路启用",
            "2.对接流量分发交换机",
            "3.对NP设备配置进行整改",
            "4.删除系统自带账户",
            "5.使用白屏工具进行变更"
        ]
    },
    "config": {
        "CN-NJ-NKG-NE8000F1A-TRANSITWAN-P02-PGW01-99.99.236.94": [
            "local-user admin123 state block fal-times 3 interval 5",
            "local-user admin123 ftp-directory cfcard:",
            "dis cur con ssl",
            "ssl policy router default",
            "ssl minimum version tls1.2",
            "cipher-suite exclude key-exchange rsa",
            "cipher-suite exclude cipher mode cbc",
            "cipher-suite exclude hmac sha1",
            "dffie-helman modulus 3072",
            "binding cipher-suite-customization default_cipher_suite",
            "ecdh group nist",
            "signature algorithm-list rsa-pss-rsae-sha256 rsa-pss-rsae-sha384 rsa-pss-rsae-sha512",
            "ssl cipher-suite-list default_cipher_suite",
            "set cipher-suite tls12_ck_ecdhe_rsa_with_aes_128_gcm_sha256",
            "set cipher-suite tls12_ck_ecdhe_rsa_with_aes_256_gcm_sha384",
            "set cipher-suite tis13_aes_128_gcm_sha256",
            "set cipher-suite tis13_aes_256_gcm_sha384",
            "set cipher-suite tis13_aes_128_gcm_sha256"
        ],
        "CN-NJ-NKG-NE8000F1A-TRANSITWAN-P02-PGW02-99.99.236.95": [
            "dsplay current-confouration configuration aaa",
            "user-password password-force-change disable",
            "local-user adminadmin pasword irreversible-cipher $1cSD5ROerc=HDB@e1+ljlQxO)6%(=6k%NJTAweiRS",
            "local-user adminadmin service-type terminal ssh",
            "local-user adminadmin level 3",
            "local-user adminadmin state block fail-times 3 interval 5",
            "local-user root password irreversible-cipher S1c$]í(3Q<7uSSIODB@e1+ljlQx&y-SM(In ERFU_BFS6X$",
            "local-user root service-type ssh mml",
            "local-user root state block fail-times 3 interval 5",
            "local-user root user-group manage-ug",
            "local-user root expire 2000-01-01",
            "local-user hwclouds password ireversibe-cipher $1cSJv@/%×L=$^1YFDB@e1+ljlQxy&#8/EFwO)MMSNWVaS1s",
            "local-user hwclouds service-type terminal ssh",
            "local-user hwclouds level 3",
            "local-user hwclouds state block fail-times 3 interval 5",
            "local-user grpcuser password irreversible-cipher ",
            "local-user grpcuser service-type http",
            "local-user grpcuser level 3",
            "local-user grpcuser state block fail-times 3 interval 5",
            "local-user admin123 password ireversble-cipher ",
            "local-user admin123 service-type ftp ssh",
            "local-user admin123 level 3",
            "local-user admin123 state block fal-times 3 interval 5",
            "local-user admin123 ftp-directory cfcard:",
            "dis cur con ssl",
            "ssl policy router default",
            "ssl minimum version tls1.2",
            "cipher-suite exclude key-exchange rsa",
            "cipher-suite exclude cipher mode cbc",
            "cipher-suite exclude hmac sha1",
            "dffie-helman modulus 3072",
            "binding cipher-suite-customization default_cipher_suite",
            "ecdh group nist",
            "signature algorithm-list rsa-pss-rsae-sha256 rsa-pss-rsae-sha384 rsa-pss-rsae-sha512",
            "ssl cipher-suite-list default_cipher_suite",
            "set cipher-suite tls12_ck_ecdhe_rsa_with_aes_128_gcm_sha256",
            "set cipher-suite tls12_ck_ecdhe_rsa_with_aes_256_gcm_sha384",
            "set cipher-suite tis13_aes_128_gcm_sha256",
            "set cipher-suite tis13_aes_256_gcm_sha384",
            "set cipher-suite tis13_aes_128_gcm_sha256"
        ],
        "CN-NJ-NKG-FM8850-P01-TDSW01-99.99.236.74": [
            "dis cu int eth 120",
            "display current-configuration interface 100GE1/0/61",
            "interface 100GE1/0/61",
            "description l60058710-0617-pgw",
            "shutdown",
            "device transceiver 100GBASE-FIBER",
            "return",
            "displayl current-configuration interface 100GE1/0/62",
            "interface 100GE1/0/62",
            "description l60058710-0617-pgw",
            "shutdown",
            "device transceiver 100GBASE-FIBER",
            "return",
            "display current-configuration interface 100GE1/0/63",
            "interface 100GE1/0/63",
            "description l60058710-0617-pgw",
            "shutdown",
            "device transceiver 100GBASE-FIBER",
            "display current-configuration interface 100GE1/0/64",
            "interface 100GE1/0/64",
            "description l60058710-0617-pgw",
            "shutdown",
            "device transceiver 100GBASE-FIBER"
        ],
        "CN-NJ-NKG-FM8850-P01-TDSW02-99.99.236.75": [
            "dis cu int eth 120",
            "display current-configuration interface 100GE1/0/61",
            "interface 100GE1/0/61",
            "description l60058710-0617-pgw",
            "shutdown",
            "device transceiver 100GBASE-FIBER",
            "displayl current-configuration interface 100GE1/0/62",
            "interface 100GE1/0/62",
            "description l60058710-0617-pgw",
            "shutdown",
            "device transceiver 100GBASE-FIBER",
            "return",
            "display current-configuration interface 100GE1/0/63",
            "interface 100GE1/0/63",
            "description l60058710-0617-pgw",
            "shutdown",
            "device transceiver 100GBASE-FIBER",
            "return",
            "display current-configuration interface 100GE1/0/64",
            "interface 100GE1/0/64",
            "description l60058710-0617-pgw",
            "shutdown",
            "device transceiver 100GBASE-FIBER"
        ]
    },
    "step_info": [
        {
            "step_index": 1,
            "step_name": "南京杭州西安POP NP设备配置整改",
            "command": {
                "pre_check": [
                    {"command": ["display current-configuration configuration ssl"], "rollback_command": [], "desc": ""},
                    {"command": ["display current-confiquration configuration aaa"], "rollback_command": [], "desc": ""}
                ],
                "exe_command": [
                    {"command": ["mmi-mode enable"], "rollback_command": ["mmi-mode enable"], "desc": ""},
                    {"command": ["system-view"], "rollback_command": ["system-view"], "desc": ""},
                    {"command": ["undo ssl policy router_default"], "rollback_command": [
                        "ssl policy router_default",
                        "ssl minimum version tls1.2",
                        "cipher-suite exclude key-exchange rsa",
                        "cipher-suite exclude cipher mode cbc",
                        "cipher-suite exclude hmac sha1",
                        "diffie-hellman modulus 3072",
                        "binding cipher-sute-customization defaut_cipher_suite",
                        "ecdh group nist",
                        "signature algorithm-list rsa-pss-rsae-sha256 rsa-pss-rsae-sha384 rsa-pss-rsae-sha512",
                        "quit"
                    ],
                     "desc": "删除默认SSL策略"},
                    {"command": ["undo ssl cipher-suite-list default_cipher_suite"],
                     "rollback_command": [
                        "ssl cipher-suite-list default_cipher_suite",
                        "set cipher-suite tls12_ck_ecdhe_rsa_with_aes_128_gcm_sha256",
                        "set cipher-suite tls12_ck_ecdhe_rsa_with_aes_256_gcm_sha384",
                        "set cipher-suite tis13_aes_128_gcm_sha256",
                        "set cipher-suite tis13_aes_256_gcm_sha384",
                        "set cipher-suite tis13_aes_128_gcm_sha256",
                        "quit"
                     ], "desc": "删除默认SSL密码套件列表"},
                    {"command": ["undo local-user root"],
                     "rollback_command": ["local-user root password irreversible-cipher Changeme_123"], "desc": "删除设备上名为“root”的本地用户"},
                    {"command": ["undo local-user admin123"], "rollback_command": [
                        "local-user root service-type ssh mml",
                        "local-user root state block fail-times 3 interval 5",
                        "local-user root user-group manage-ug",
                        "local-user root expire 2000-01-01",
                        "local-user admin123 password irreversible-cipher Admin@123",
                        "local-user admin123 service-type ftp ssh",
                        "local-user admin123 level 3",
                        "local-user admin123 state block fail-times 3 interval 5",
                        "local-user admin123 ftp-directory cfcard"
                    ],
                     "desc": "删除设备上名为“admin123”的本地用户"},
                    {"command": ["quit"], "rollback_command": ["quit"], "desc": ""},
                    {"command": ["commit"], "rollback_command": ["commit"], "desc": ""},
                    {"command": ["return"], "rollback_command": ["return"], "desc": "关闭接口"},
                    {"command": ["save"], "rollback_command": ["save"], "desc": ""}
                ],
                "post_check": [
                    {"command": ["display current-configuration configuration ssl"], "rollback_command": [], "desc": ""},
                    {"command": ["display current-confiquration configuration aaa"], "rollback_command": [], "desc": ""}
                ]
            },
            "device": [
                "CN-NJ-NKG-NE8000F1A-TRANSITWAN-P02-PGW01-99.99.236.94",
                "CN-NJ-NKG-NE8000F1A-TRANSITWAN-P02-PGW02-99.99.236.95"
            ]
        },
        {
            "step_index": 2,
            "step_name": "南京杭州西安POP TDSW对接NP",
            "command": {
                "pre_check": [
                    {"command": ["display current-configuration interface Eth-Trunk 120"], "rollback_command": [],
                     "desc": ""},
                    {"command": ["display current-configuration interface 100GE1/0/61"], "rollback_command": [],
                     "desc": ""},
                    {"command": ["display current-configuration interface 100GE1/0/62"], "rollback_command": [],
                     "desc": ""},
                    {"command": ["display current-configuration interface 100GE1/0/63"], "rollback_command": [],
                     "desc": ""},
                    {"command": ["display current-configuration interface 100GE1/0/64"], "rollback_command": [],
                     "desc": ""}
                ],
                "exe_command": [
                    {"command": "mmi-mode enable", "rollback_command": ["mmi-mode enable"], "desc": ""},
                    {"command": "system-view", "rollback_command": ["system-view"], "desc": ""},
                    {"command": [
                        "interface Eth-Trunk120",
                        "description TO_PGW01-99.99236.94/PGW02-99.99.236.95",
                        "port link-type hybrid",
                        "port hybrid untagged vlan 1000",
                        "port vlan-stacking vlan 2 to 4063 stack-vlan 1000",
                        "stp disable",
                        "mac-address learning disable",
                        "quit"
                    ], "rollback_command": ["undo interface Eth-Trunk120"],
                     "desc": ""},
                    {"command": ["interface 100GE1/0/61"], "rollback_command": ["interface 100GE1/0/61"], "desc": ""},
                    {"command": ["description TO_CN-NJ-NKG-NE8000F1A-TRANSITWAN-P02-PGW01-99.99.236.94_100GE0/1/50"],
                     "rollback_command": ["description l60058710-0617-pgw"], "desc": ""},
                    {"command": ["eth-trunk 120"], "rollback_command": ["shutdown"], "desc": ""},
                    {"command": ["undo shutdown"], "rollback_command": ["undo eth-trunk"], "desc": ""},
                    {"command": ["quit"], "rollback_command": ["quit"], "desc": ""},
                    {"command": ["interface 100GE1/0/61"], "rollback_command": ["interface 100GE1/0/62"], "desc": ""},
                    {"command": ["description TO_CN-NJ-NKG-NE8000F1A-TRANSITWAN-P02-PGW01-99.99.236.94_100GE0/1/50"],
                     "rollback_command": ["description l60058710-0617-pgw"], "desc": ""},
                    {"command": ["eth-trunk 120"], "rollback_command": ["shutdown"], "desc": ""},
                    {"command": ["undo shutdown"], "rollback_command": ["undo eth-trunk"], "desc": ""},
                    {"command": ["quit"], "rollback_command": ["quit"], "desc": ""},
                    {"command": ["interface 100GE1/0/61"], "rollback_command": ["interface 100GE1/0/63"], "desc": ""},
                    {"command": ["description TO_CN-NJ-NKG-NE8000F1A-TRANSITWAN-P02-PGW01-99.99.236.94_100GE0/1/50"],
                     "rollback_command": ["description l60058710-0617-pgw"], "desc": ""},
                    {"command": ["eth-trunk 120"], "rollback_command": ["shutdown"], "desc": ""},
                    {"command": ["undo shutdown"], "rollback_command": ["undo eth-trunk"], "desc": ""},
                    {"command": ["quit"], "rollback_command": ["quit"], "desc": ""},
                    {"command": ["interface 100GE1/0/61"], "rollback_command": ["interface 100GE1/0/64"], "desc": ""},
                    {"command": ["description TO_CN-NJ-NKG-NE8000F1A-TRANSITWAN-P02-PGW01-99.99.236.94_100GE0/1/50"],
                     "rollback_command": ["description l60058710-0617-pgw"], "desc": ""},
                    {"command": ["eth-trunk 120"], "rollback_command": ["shutdown"], "desc": ""},
                    {"command": ["undo shutdown"], "rollback_command": ["undo eth-trunk"], "desc": ""},
                    {"command": ["quit"], "rollback_command": ["quit"], "desc": ""}
                ],
                "post_check": [
                    {"command": "display current-configuration interface Eth-Trunk 120", "rollback_command": [],
                     "desc": ""},
                    {"command": "display current-configuration interface 100GE1/0/61", "rollback_command": [],
                     "desc": ""},
                    {"command": "display current-configuration interface 100GE1/0/62", "rollback_command": [],
                     "desc": ""},
                    {"command": "display current-configuration interface 100GE1/0/63", "rollback_command": [],
                     "desc": ""},
                    {"command": "display current-configuration interface 100GE1/0/64", "rollback_command": [],
                     "desc": ""}
                ]
            },
            "device": [
                "CN-NJ-NKG-FM8850-P01-TDSW01-99.99.236.74",
                "CN-NJ-NKG-FM8850-P01-TDSW02-99.99.236.75"
            ]
        },
        {
            "step_index": 3,
            "step_name": "保存配置",
            "command": {
                "pre_check": [],
                "exe_command": [{"command": ["save"], "rollback_command": [], "desc": ""}],
                "post_check": []
            },
            "device": [
                "CN-NJ-NKG-NE8000F1A-TRANSITWAN-P02-PGW01-99.99.236.94",
                "CN-NJ-NKG-NE8000F1A-TRANSITWAN-P02-PGW02-99.99.236.95",
                "CN-NJ-NKG-FM8850-P01-TDSW01-99.99.236.74",
                "CN-NJ-NKG-FM8850-P01-TDSW02-99.99.236.75"
            ]
        }
    ]
}


def _get_flask_app():
    """在 worker 进程中获取 Flask app 实例"""
    import os, sys
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    import app as app_module
    return app_module.create_app()


@celery.task(bind=True, name="rule_tasks.process_excel")
def process_excel(self, task_id: int, filepath: str):
    """模块A: 异步处理上传的Excel文件，模拟返回结构化JSON"""
    flask_app = _get_flask_app()
    with flask_app.app_context():
        task = db.session.get(RuleTask, task_id)
        if not task:
            return {"error": "Task not found"}

        try:
            task.status = "success"
            task.extracted_json = SAMPLE_EXTRACTED_JSON
            db.session.commit()
            return {"status": "success", "task_id": task_id}
        except Exception as e:
            task.status = "failed"
            task.extracted_json = {"error": str(e)}
            db.session.commit()
            return {"status": "failed", "error": str(e)}
