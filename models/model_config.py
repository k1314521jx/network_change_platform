from models.models import db, now_cn


class ModelConfig(db.Model):
    __tablename__ = "model_config"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    api_key = db.Column(db.String(500), nullable=False)
    base_url = db.Column(db.String(500), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=now_cn)
    updated_at = db.Column(db.DateTime, default=now_cn, onupdate=now_cn)
