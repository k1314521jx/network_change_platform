from flask import Blueprint, jsonify
from sqlalchemy import func, Date, cast
from models import db, RuleTask, TripleTask, AiReview, TripleReview
from models.rule_validation import RuleValidation

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.route("/overview", methods=["GET"])
def overview():
    """总览统计：各阶段成功/完成数量"""
    rule_success = db.session.query(func.count(RuleTask.id)).filter(
        RuleTask.status == "success", RuleTask.is_deleted == False
    ).scalar()

    triple_success = db.session.query(func.count(TripleTask.id)).filter(
        TripleTask.status == "success"
    ).scalar()

    rule_validation_passed = db.session.query(func.count(RuleValidation.id)).filter(
        RuleValidation.status == "passed"
    ).scalar()

    ai_review_done = db.session.query(func.count(AiReview.id)).filter(
        AiReview.status == "reviewed"
    ).scalar()

    human_review_done = db.session.query(func.count(TripleReview.id)).filter(
        TripleReview.review_status.in_(["approved", "rejected"])
    ).scalar()

    return jsonify({
        "code": 0,
        "data": {
            "rule_success": rule_success or 0,
            "triple_success": triple_success or 0,
            "validation_passed": rule_validation_passed or 0,
            "ai_review_done": ai_review_done or 0,
            "human_review_done": human_review_done or 0,
        },
    })


@dashboard_bp.route("/daily-trend", methods=["GET"])
def daily_trend():
    """每日趋势：规则化成功/失败、图谱生成成功/失败、规则审核通过/不合格"""
    # 最近30天
    base = db.session.query(
        cast(RuleTask.created_at, Date).label("day"),
        RuleTask.status,
        func.count(RuleTask.id).label("cnt"),
    ).filter(
        RuleTask.is_deleted == False,
        RuleTask.status.in_(["success", "failed"]),
    ).group_by("day", RuleTask.status).all()

    rule_trend = {}
    for day, status, cnt in base:
        d = day.isoformat()
        if d not in rule_trend:
            rule_trend[d] = {"success": 0, "failed": 0}
        rule_trend[d][status] = cnt

    # 图谱生成
    base2 = db.session.query(
        cast(TripleTask.created_at, Date).label("day"),
        TripleTask.status,
        func.count(TripleTask.id).label("cnt"),
    ).filter(
        TripleTask.status.in_(["success", "failed"]),
    ).group_by("day", TripleTask.status).all()

    triple_trend = {}
    for day, status, cnt in base2:
        d = day.isoformat()
        if d not in triple_trend:
            triple_trend[d] = {"success": 0, "failed": 0}
        triple_trend[d][status] = cnt

    # 规则审核
    base3 = db.session.query(
        cast(RuleValidation.created_at, Date).label("day"),
        RuleValidation.status,
        func.count(RuleValidation.id).label("cnt"),
    ).filter(
        RuleValidation.status.in_(["passed", "unqualified"]),
    ).group_by("day", RuleValidation.status).all()

    validation_trend = {}
    for day, status, cnt in base3:
        d = day.isoformat()
        if d not in validation_trend:
            validation_trend[d] = {"passed": 0, "unqualified": 0}
        validation_trend[d][status] = cnt

    # 合并所有日期
    all_days = sorted(set(list(rule_trend.keys()) + list(triple_trend.keys()) + list(validation_trend.keys())))

    days = []
    rule_success_list = []
    rule_failed_list = []
    triple_success_list = []
    triple_failed_list = []
    validation_passed_list = []
    validation_unqualified_list = []

    for d in all_days:
        days.append(d)
        r = rule_trend.get(d, {"success": 0, "failed": 0})
        rule_success_list.append(r["success"])
        rule_failed_list.append(r["failed"])
        t = triple_trend.get(d, {"success": 0, "failed": 0})
        triple_success_list.append(t["success"])
        triple_failed_list.append(t["failed"])
        v = validation_trend.get(d, {"passed": 0, "unqualified": 0})
        validation_passed_list.append(v["passed"])
        validation_unqualified_list.append(v["unqualified"])

    return jsonify({
        "code": 0,
        "data": {
            "days": days,
            "rule": {"success": rule_success_list, "failed": rule_failed_list},
            "triple": {"success": triple_success_list, "failed": triple_failed_list},
            "validation": {"passed": validation_passed_list, "unqualified": validation_unqualified_list},
        },
    })


@dashboard_bp.route("/ai-score-by-model", methods=["GET"])
def ai_score_by_model():
    """AI审核分数按图谱转换模型分组（折线图：x=日期, y=平均分, series=模型）"""
    rows = db.session.query(
        cast(AiReview.reviewed_at, Date).label("day"),
        TripleTask.model.label("triple_model"),
        func.avg(AiReview.score).label("avg_score"),
    ).join(
        TripleTask, AiReview.triple_task_id == TripleTask.id
    ).filter(
        AiReview.status == "reviewed",
        AiReview.score.isnot(None),
    ).group_by("day", "triple_model").order_by("day").all()

    # 构建结构: { model: { day: avg_score } }
    model_map = {}
    all_days_set = set()
    for day, model, avg_score in rows:
        d = day.isoformat()
        all_days_set.add(d)
        if model not in model_map:
            model_map[model] = {}
        model_map[model][d] = round(float(avg_score), 1)

    all_days = sorted(all_days_set)
    models = sorted(model_map.keys())

    series = []
    for m in models:
        series.append({
            "model": m,
            "scores": [model_map[m].get(d) for d in all_days],
        })

    return jsonify({
        "code": 0,
        "data": {
            "days": all_days,
            "series": series,
        },
    })


@dashboard_bp.route("/violation-rate-by-model", methods=["GET"])
def violation_rate_by_model():
    """规则审核：按首次验证不合格数据，统计不同模型下规则1-5的不符合占比"""
    # 查询所有有 first_validation_result 的不合格记录
    rows = db.session.query(
        TripleTask.model,
        RuleValidation.first_validation_result,
    ).join(
        TripleTask, RuleValidation.triple_task_id == TripleTask.id
    ).filter(
        RuleValidation.first_validation_result.isnot(None),
    ).all()

    # 按模型统计: { model: { total: N, rule_counts: {1:0, 2:0, 3:0, 4:0, 5:0} } }
    model_stats = {}
    for model, result in rows:
        if not result or "violations" not in result:
            continue
        if model not in model_stats:
            model_stats[model] = {"total": 0, "rule_counts": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}}
        model_stats[model]["total"] += 1
        for v in result["violations"]:
            rule_num = v.get("rule")
            if rule_num and 1 <= rule_num <= 5:
                model_stats[model]["rule_counts"][rule_num] += 1

    # 转换为占比
    models = sorted(model_stats.keys())
    data = []
    for m in models:
        total = model_stats[m]["total"]
        rates = {}
        for r in range(1, 6):
            cnt = model_stats[m]["rule_counts"][r]
            rates[f"rule{r}"] = round(cnt / total * 100, 1) if total > 0 else 0
        data.append({
            "model": m,
            "total": total,
            **rates,
        })

    return jsonify({
        "code": 0,
        "data": data,
    })
