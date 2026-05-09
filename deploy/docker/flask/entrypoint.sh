#!/bin/bash
set -e

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 等待 MySQL 就绪..."
while ! python -c "
import socket, sys
s = socket.socket()
try:
    s.connect(('${MYSQL_HOST:-mysql}', ${MYSQL_PORT:-3306}))
    s.close()
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    sleep 2
done
echo "[$(date '+%Y-%m-%d %H:%M:%S')] MySQL 已就绪"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 等待 Redis 就绪..."
while ! python -c "
import socket, sys
s = socket.socket()
try:
    s.connect(('${REDIS_HOST:-redis}', ${REDIS_PORT:-6379}))
    s.close()
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    sleep 2
done
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Redis 已就绪"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 初始化数据库（自动建表）..."
python -c "from app import create_app; app = create_app(); print('数据库初始化完成')"

if [ "$1" = "celery" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 启动 Celery Worker..."
    exec celery -A tasks.celery_app:celery worker --loglevel=info --concurrency=2
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 启动 Flask (gunicorn)..."
    exec gunicorn --bind 0.0.0.0:5000 --workers 4 --worker-class gevent --timeout 120 --access-logfile logs/access.log --error-logfile logs/error.log "app:create_app()"
fi
