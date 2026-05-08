"""
数据迁移脚本：为已有TripleReview记录的TripleTask创建AiReview(status=reviewed)
确保旧数据在新的AI审核流程下仍可见
"""

import sys
import os

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import pymysql

DB_CONFIG = {
    "host": "127.0.0.1", "port": 3306, "user": "root",
    "password": "QPAL624119", "database": "act",
}


def main():
    conn = pymysql.connect(**DB_CONFIG, charset="utf8mb4")
    cur = conn.cursor()

    # 查找所有 status=success 的 triple_task 且没有 ai_review 记录的
    cur.execute("""
        SELECT DISTINCT t.id FROM triple_task t
        LEFT JOIN ai_review a ON a.triple_task_id = t.id
        WHERE t.status = 'success' AND a.id IS NULL
    """)
    task_ids = [row[0] for row in cur.fetchall()]

    if not task_ids:
        print("无需迁移，所有成功的三元组任务已有AI审核记录")
        conn.close()
        return

    print(f"发现 {len(task_ids)} 个需要迁移的任务")

    for task_id in task_ids:
        cur.execute(
            "INSERT INTO ai_review (triple_task_id, model, status, score, summary, created_at, reviewed_at) "
            "VALUES (%s, %s, %s, %s, %s, NOW(), NOW())",
            (task_id, "system", "reviewed", 100, "历史数据自动迁移，未经AI审核"),
        )

    conn.commit()
    print(f"已为 {len(task_ids)} 个任务创建AI审核记录")
    conn.close()


if __name__ == "__main__":
    main()
