import os
import sys

# 确保项目根目录在 Python 路径中
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from celery import Celery
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

celery = Celery(
    "network_change_platform",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["tasks.rule_tasks", "tasks.triple_tasks", "tasks.ai_review_tasks", "tasks.validation_tasks"],
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    worker_hijack_root_logger=False,
    worker_prefetch_multiplier=1,
)

# 配置日志：同时输出到控制台和文件（RotatingFileHandler 支持多 worker 并行写入 + 日志分割）
import logging
from logging.handlers import RotatingFileHandler

_log_dir = os.path.join(_project_root, "logs")
os.makedirs(_log_dir, exist_ok=True)

log_formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# RotatingFileHandler: 50MB 分割，保留 3 个备份
celery_file_handler = RotatingFileHandler(
    os.path.join(_log_dir, "celery.log"),
    maxBytes=50 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
celery_file_handler.setFormatter(log_formatter)
celery_file_handler.setLevel(logging.INFO)

# 控制台 handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# 为所有 celery 任务相关 logger 统一配置 handler
for logger_name in ["llm_service", "ai_review_service", "triple_validator"]:
    _logger = logging.getLogger(logger_name)
    _logger.setLevel(logging.INFO)
    _logger.addHandler(celery_file_handler)
    _logger.addHandler(console_handler)
    _logger.propagate = False
