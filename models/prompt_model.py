from models.models import db, now_cn


class PromptConfig(db.Model):
    __tablename__ = "prompt_config"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # extraction / review
    content = db.Column(db.Text, nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    is_current = db.Column(db.Boolean, nullable=False, default=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    is_builtin = db.Column(db.Boolean, nullable=False, default=False)
    changelog = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=now_cn)
    updated_at = db.Column(db.DateTime, default=now_cn, onupdate=now_cn)
