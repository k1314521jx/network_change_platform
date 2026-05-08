from models import db, PromptConfig, now_cn
from services.prompt_templates import SYSTEM_PROMPT, AI_REVIEW_SYSTEM_PROMPT


def seed_builtin_prompts():
    """首次启动时插入内置提示词"""
    for ptype, content, name in [
        ("extraction", SYSTEM_PROMPT, "默认抽取提示词"),
        ("review", AI_REVIEW_SYSTEM_PROMPT, "默认审核提示词"),
    ]:
        exists = PromptConfig.query.filter_by(
            type=ptype, is_builtin=True, is_deleted=False
        ).first()
        if not exists:
            prompt = PromptConfig(
                name=name,
                type=ptype,
                content=content,
                version=1,
                is_current=True,
                is_builtin=True,
            )
            db.session.add(prompt)
    db.session.commit()


def list_prompts(ptype, page=1, per_page=15, search=""):
    query = PromptConfig.query.filter_by(
        type=ptype, is_current=True, is_deleted=False
    )
    if search:
        query = query.filter(PromptConfig.name.like(f"%{search}%"))
    query = query.order_by(PromptConfig.created_at.desc())
    return query.paginate(page=page, per_page=per_page, error_out=False)


def get_prompt_detail(prompt_id):
    return db.session.get(PromptConfig, prompt_id)


def create_prompt(name, ptype, content):
    prompt = PromptConfig(
        name=name,
        type=ptype,
        content=content,
        version=1,
        is_current=True,
    )
    db.session.add(prompt)
    db.session.commit()
    return prompt


def update_prompt(prompt_id, content):
    old = db.session.get(PromptConfig, prompt_id)
    if not old or old.is_deleted:
        return None
    old.is_current = False
    new = PromptConfig(
        name=old.name,
        type=old.type,
        content=content,
        version=old.version + 1,
        is_current=True,
        is_builtin=old.is_builtin,
    )
    db.session.add(new)
    db.session.commit()
    return new


def delete_prompt(prompt_id):
    prompt = db.session.get(PromptConfig, prompt_id)
    if not prompt:
        return False
    PromptConfig.query.filter_by(
        name=prompt.name, type=prompt.type
    ).update({"is_deleted": True})
    db.session.commit()
    return True


def get_prompt_history(name, ptype):
    return (
        PromptConfig.query.filter_by(name=name, type=ptype, is_deleted=False)
        .order_by(PromptConfig.version.desc())
        .all()
    )


def get_prompt_options(ptype):
    return (
        PromptConfig.query.filter_by(type=ptype, is_current=True, is_deleted=False)
        .with_entities(PromptConfig.id, PromptConfig.name)
        .order_by(PromptConfig.created_at.desc())
        .all()
    )


def get_prompt_content_by_id(prompt_id):
    prompt = db.session.get(PromptConfig, prompt_id)
    if prompt and not prompt.is_deleted and prompt.is_current:
        return prompt.content
    return None


def activate_prompt(prompt_id):
    """将指定历史版本设为当前活跃版本，原活跃版本降级"""
    prompt = db.session.get(PromptConfig, prompt_id)
    if not prompt or prompt.is_deleted:
        return None
    if prompt.is_current:
        return prompt  # 已经是当前版本

    # 将同名同类型的当前版本降级
    PromptConfig.query.filter_by(
        name=prompt.name, type=prompt.type, is_current=True, is_deleted=False
    ).update({"is_current": False})

    prompt.is_current = True
    db.session.commit()
    return prompt
