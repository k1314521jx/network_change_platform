from datetime import datetime, timezone, timedelta
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 北京时间 (UTC+8)
CN_TZ = timezone(timedelta(hours=8))


def now_cn():
    return datetime.now(CN_TZ)


class RuleTask(db.Model):
    __tablename__ = "rule_task"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum("pending", "success", "failed"), default="pending", index=True)
    extracted_json = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=now_cn)
    is_deleted = db.Column(db.Boolean, default=False)

    triple_tasks = db.relationship("TripleTask", backref="rule_task", lazy="dynamic")


class TripleTask(db.Model):
    __tablename__ = "triple_task"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rule_task_id = db.Column(db.Integer, db.ForeignKey("rule_task.id"), nullable=False)
    status = db.Column(db.Enum("pending", "success", "failed"), default="pending", index=True)
    triple_json = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=now_cn)

    reviews = db.relationship("TripleReview", backref="triple_task", lazy="dynamic")


class TripleReview(db.Model):
    __tablename__ = "triple_review"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    triple_task_id = db.Column(db.Integer, db.ForeignKey("triple_task.id"), nullable=False)
    reviewed_json = db.Column(db.JSON)
    review_status = db.Column(db.Enum("pending", "approved", "rejected"), default="pending", index=True)
    reviewer = db.Column(db.String(100))
    review_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=now_cn)

    import_logs = db.relationship("Neo4jImportLog", backref="triple_review", lazy="dynamic")


class Neo4jImportLog(db.Model):
    __tablename__ = "neo4j_import_log"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    triple_review_id = db.Column(db.Integer, db.ForeignKey("triple_review.id"), nullable=False)
    status = db.Column(db.Enum("success", "failed"), default="failed")
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=now_cn)
