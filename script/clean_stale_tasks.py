"""
清理异常状态的 Celery 任务数据

用法:
  # 预览模式（不删除，仅显示会清理的数据）
  python script/clean_stale_tasks.py --dry-run

  # 清理 pending 超过 30 分钟的任务（默认）
  python script/clean_stale_tasks.py

  # 清理指定 ID 的任务
  python script/clean_stale_tasks.py --ids 10 11 12

  # 清理 pending 超过指定分钟的任务
  python script/clean_stale_tasks.py --timeout 60
"""

import argparse
import sys
import os

# 确保项目根目录在 sys.path 中
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import pymysql
from datetime import datetime, timedelta

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "QPAL624119",
    "database": "act",
}

TABLES = [
    {
        "name": "rule_task",
        "display": "规则任务",
    },
    {
        "name": "triple_task",
        "display": "三元组任务",
    },
]


def get_conn():
    return pymysql.connect(**DB_CONFIG, charset="utf8mb4")


def clean_by_ids(conn, ids, dry_run):
    """按指定 ID 删除任务数据"""
    cur = conn.cursor()

    for table in TABLES:
        tname = table["name"]
        display = table["display"]

        placeholders = ",".join(["%s"] * len(ids))
        cur.execute(f"SELECT id, status, created_at FROM {tname} WHERE id IN ({placeholders})", ids)
        rows = cur.fetchall()

        if not rows:
            print(f"  {display}({tname}): 未找到匹配记录")
            continue

        for row in rows:
            print(f"  {display} ID={row[0]} | 状态={row[1]} | 创建时间={row[2]}")

        if dry_run:
            print(f"  [预览] 将删除以上 {len(rows)} 条{display}记录")
        else:
            # 先删关联数据
            if tname == "rule_task":
                # 删除关联的三元组审核 → 三元组任务 → 规则任务
                cur.execute(
                    f"DELETE FROM neo4j_import_log WHERE triple_review_id IN "
                    f"(SELECT id FROM triple_review WHERE triple_task_id IN "
                    f"(SELECT id FROM triple_task WHERE rule_task_id IN ({placeholders})))",
                    ids,
                )
                cur.execute(
                    f"DELETE FROM triple_review WHERE triple_task_id IN "
                    f"(SELECT id FROM triple_task WHERE rule_task_id IN ({placeholders}))",
                    ids,
                )
                cur.execute(
                    f"DELETE FROM triple_task WHERE rule_task_id IN ({placeholders})", ids
                )
            elif tname == "triple_task":
                cur.execute(
                    f"DELETE FROM neo4j_import_log WHERE triple_review_id IN "
                    f"(SELECT id FROM triple_review WHERE triple_task_id IN ({placeholders}))",
                    ids,
                )
                cur.execute(
                    f"DELETE FROM triple_review WHERE triple_task_id IN ({placeholders})", ids
                )

            cur.execute(f"DELETE FROM {tname} WHERE id IN ({placeholders})", ids)
            conn.commit()
            print(f"  已删除 {len(rows)} 条{display}记录（含关联数据）")

    cur.close()


def clean_stale_pending(conn, timeout_minutes, dry_run):
    """清理 pending 超时的任务（视为 Celery 异常卡死）"""
    cur = conn.cursor()
    cutoff = datetime.now() - timedelta(minutes=timeout_minutes)

    for table in TABLES:
        tname = table["name"]
        display = table["display"]

        cur.execute(
            f"SELECT id, status, created_at FROM {tname} WHERE status='pending' AND created_at < %s",
            (cutoff,),
        )
        rows = cur.fetchall()

        if not rows:
            print(f"  {display}({tname}): 无超时 pending 记录")
            continue

        stale_ids = [row[0] for row in rows]
        for row in rows:
            print(f"  {display} ID={row[0]} | 状态={row[1]} | 创建时间={row[2]}")

        if dry_run:
            print(f"  [预览] 将删除以上 {len(rows)} 条超时{display}记录")
        else:
            placeholders = ",".join(["%s"] * len(stale_ids))

            if tname == "rule_task":
                cur.execute(
                    f"DELETE FROM neo4j_import_log WHERE triple_review_id IN "
                    f"(SELECT id FROM triple_review WHERE triple_task_id IN "
                    f"(SELECT id FROM triple_task WHERE rule_task_id IN ({placeholders})))",
                    stale_ids,
                )
                cur.execute(
                    f"DELETE FROM triple_review WHERE triple_task_id IN "
                    f"(SELECT id FROM triple_task WHERE rule_task_id IN ({placeholders}))",
                    stale_ids,
                )
                cur.execute(
                    f"DELETE FROM triple_task WHERE rule_task_id IN ({placeholders})", stale_ids
                )
            elif tname == "triple_task":
                cur.execute(
                    f"DELETE FROM neo4j_import_log WHERE triple_review_id IN "
                    f"(SELECT id FROM triple_review WHERE triple_task_id IN ({placeholders}))",
                    stale_ids,
                )
                cur.execute(
                    f"DELETE FROM triple_review WHERE triple_task_id IN ({placeholders})",
                    stale_ids,
                )

            cur.execute(f"DELETE FROM {tname} WHERE id IN ({placeholders})", stale_ids)
            conn.commit()
            print(f"  已删除 {len(rows)} 条超时{display}记录（含关联数据）")

    cur.close()


def main():
    parser = argparse.ArgumentParser(description="清理异常状态的 Celery 任务数据")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际删除")
    parser.add_argument("--ids", type=int, nargs="+", help="指定要删除的任务 ID 列表")
    parser.add_argument("--timeout", type=int, default=30, help="pending 超时分钟数（默认30）")
    args = parser.parse_args()

    conn = get_conn()

    if args.ids:
        print(f"按 ID 清理: {args.ids}")
        clean_by_ids(conn, args.ids, args.dry_run)
    else:
        print(f"清理 pending 超过 {args.timeout} 分钟的异常任务")
        clean_stale_pending(conn, args.timeout, args.dry_run)

    conn.close()
    print("\n完成")


if __name__ == "__main__":
    main()
