import os

# MySQL
DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.environ.get("MYSQL_PORT", 3306)),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", "QPAL624119"),
    "database": os.environ.get("MYSQL_DATABASE", "act"),
}

# Redis (Celery Broker 用 db0, Result Backend 用 db1, LLM思考过程用 db3)
REDIS_CONFIG = {
    "host": os.environ.get("REDIS_HOST", "127.0.0.1"),
    "port": int(os.environ.get("REDIS_PORT", 6379)),
    "db": 0,
    "password": os.environ.get("REDIS_PASSWORD", ""),
}
REDIS_BACKEND_CONFIG = {
    "host": os.environ.get("REDIS_HOST", "127.0.0.1"),
    "port": int(os.environ.get("REDIS_PORT", 6379)),
    "db": 1,
    "password": os.environ.get("REDIS_PASSWORD", ""),
}
REDIS_THINKING_CONFIG = {
    "host": os.environ.get("REDIS_HOST", "127.0.0.1"),
    "port": int(os.environ.get("REDIS_PORT", 6379)),
    "db": 3,
    "password": os.environ.get("REDIS_PASSWORD", ""),
}

# LLM 思考过程缓存过期时间（秒）
LLM_THINKING_TTL = 86400  # 24小时

# Neo4j
NEO4J_CONFIG = {
    "uri": f"bolt://{os.environ.get('NEO4J_HOST', 'localhost')}:{os.environ.get('NEO4J_PORT', 7687)}",
    "user": os.environ.get("NEO4J_USER", "neo4j"),
    "password": os.environ.get("NEO4J_PASSWORD", "12345678"),
    "database": os.environ.get("NEO4J_DATABASE", "neo4j"),
}

# LLM Models
MODELS = {
    "deepseek": {"api_key": "sk-20ba4224c6b34b6682976f63ce1a353b", "base_url": "https://api.deepseek.com", "model": "deepseek-v4-pro"},
    "GLM": {"api_key": "20da28c06e654f1eb842065da0bd2159.F4OjZc18cJgsZTnk", "base_url": "https://open.bigmodel.cn/api/paas/v4/", "model": "GLM-5.1"},
    "qwen": {"api_key": "sk-a96358aae7ee4a8da170f51829490532", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen3.6-plus"},
}
ACTIVE_MODEL = "deepseek"

# Flask
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "True") == "True"

# Upload
UPLOAD_FOLDER = "uploads"
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# Celery
CELERY_BROKER_URL = f"redis://{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/{REDIS_CONFIG['db']}"
CELERY_RESULT_BACKEND = f"redis://{REDIS_BACKEND_CONFIG['host']}:{REDIS_BACKEND_CONFIG['port']}/{REDIS_BACKEND_CONFIG['db']}"

# SQLAlchemy
SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    "?charset=utf8mb4"
)
