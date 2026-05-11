from functools import wraps

from flask import Blueprint, request, jsonify, session
from sqlalchemy.exc import IntegrityError

from models import db, User
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint("auth", __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"code": 401, "message": "未登录"}), 401
        return f(*args, **kwargs)
    return decorated


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"code": -1, "message": "用户名和密码不能为空"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"code": -1, "message": "用户名或密码错误"}), 400

    session["user_id"] = user.id
    session["username"] = user.username

    return jsonify({"code": 0, "data": {"id": user.id, "username": user.username}})


@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"code": 0, "message": "已退出登录"})


@auth_bp.route("/api/auth/me", methods=["GET"])
def get_me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"code": 401, "message": "未登录"}), 401

    user = db.session.get(User, user_id)
    if not user:
        session.clear()
        return jsonify({"code": 401, "message": "用户不存在"}), 401

    return jsonify({"code": 0, "data": {"id": user.id, "username": user.username}})


def seed_admin_user():
    """创建默认管理员账号（不存在时创建，并发安全）"""
    if not User.query.filter_by(username="admin").first():
        try:
            user = User(
                username="admin",
                password_hash=generate_password_hash("admin123456"),
            )
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
