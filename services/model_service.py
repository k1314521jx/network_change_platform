from models import db, ModelConfig, now_cn
from openai import OpenAI


def list_models():
    return ModelConfig.query.filter_by(is_deleted=False).order_by(ModelConfig.created_at.desc()).all()


def get_model_detail(model_id):
    return db.session.get(ModelConfig, model_id)


def create_model(name, api_key, base_url, model):
    exists = ModelConfig.query.filter_by(name=name, is_deleted=False).first()
    if exists:
        return None
    m = ModelConfig(name=name, api_key=api_key, base_url=base_url, model=model)
    db.session.add(m)
    db.session.commit()
    return m


def update_model(model_id, **kwargs):
    m = db.session.get(ModelConfig, model_id)
    if not m or m.is_deleted:
        return None
    if "name" in kwargs and kwargs["name"] != m.name:
        conflict = ModelConfig.query.filter_by(name=kwargs["name"], is_deleted=False).first()
        if conflict:
            return None
    for key in ("name", "api_key", "base_url", "model", "is_active"):
        if key in kwargs:
            setattr(m, key, kwargs[key])
    db.session.commit()
    return m


def delete_model(model_id):
    m = db.session.get(ModelConfig, model_id)
    if not m:
        return False
    m.is_deleted = True
    db.session.commit()
    return True


def get_model_options():
    return (
        ModelConfig.query.filter_by(is_active=True, is_deleted=False)
        .with_entities(ModelConfig.id, ModelConfig.name, ModelConfig.model)
        .order_by(ModelConfig.created_at.desc())
        .all()
    )


def get_model_config_by_name(name):
    """按 name 查询启用的模型配置，供 llm_service 使用"""
    return ModelConfig.query.filter_by(name=name, is_active=True, is_deleted=False).first()


def get_first_active_model():
    """获取第一个启用的模型配置，作为默认模型"""
    return ModelConfig.query.filter_by(is_active=True, is_deleted=False).order_by(ModelConfig.created_at.asc()).first()


def test_model_connection(api_key, base_url, model):
    """验证模型连接：发一个极短请求测试可用性"""
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=10.0)
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1,
        )
        return True, f"连接成功，模型响应: {resp.choices[0].finish_reason}"
    except Exception as e:
        return False, str(e)
