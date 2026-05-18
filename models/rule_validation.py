from .models import db, now_cn


class RuleValidation(db.Model):
    __tablename__ = "rule_validation"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    triple_task_id = db.Column(db.Integer, db.ForeignKey("triple_task.id"), unique=True, nullable=False, index=True)
    status = db.Column(db.Enum("pending", "validating", "passed", "unqualified"), default="pending", index=True)
    validation_result = db.Column(db.JSON)
    first_validation_result = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=now_cn)
    updated_at = db.Column(db.DateTime, default=now_cn, onupdate=now_cn)
