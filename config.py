# MySQL
DB_CONFIG = {
    "host": "127.0.0.1", "port": 3306, "user": "root",
    "password": "QPAL624119", "database": "act"
}

# Redis (Celery Broker 用 db0, Result Backend 用 db1, LLM思考过程用 db3)
REDIS_CONFIG = {"host": "127.0.0.1", "port": 6379, "db": 0, "password": ""}
REDIS_BACKEND_CONFIG = {"host": "127.0.0.1", "port": 6379, "db": 1, "password": ""}
REDIS_THINKING_CONFIG = {"host": "127.0.0.1", "port": 6379, "db": 3, "password": ""}

# LLM 思考过程缓存过期时间（秒）
LLM_THINKING_TTL = 86400  # 24小时

# Neo4j
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687", "user": "neo4j",
    "password": "12345678", "database": "neo4j"
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
FLASK_DEBUG = True

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
