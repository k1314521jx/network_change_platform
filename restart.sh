#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# ---------- 停止服务 ----------
echo ">>> 停止服务..."

# 杀 gunicorn (Flask)
GUNICORN_PIDS=$(pgrep -f "gunicorn.*app:create_app")
if [ -n "$GUNICORN_PIDS" ]; then
    echo "    杀 gunicorn: $GUNICORN_PIDS"
    echo "$GUNICORN_PIDS" | xargs kill -9 2>/dev/null
    sleep 1
fi

# 杀 celery worker
CELERY_PIDS=$(pgrep -f "celery.*tasks.celery_app:celery worker")
if [ -n "$CELERY_PIDS" ]; then
    echo "    杀 celery: $CELERY_PIDS"
    echo "$CELERY_PIDS" | xargs kill -9 2>/dev/null
    sleep 1
fi

echo ">>> 服务已停止"

# ---------- 启动服务 ----------
echo ">>> 启动服务..."

nohup gunicorn -c gunicorn.conf.py "app:create_app()" > /dev/null 2>&1 &
echo "    gunicorn 启动中..."

nohup celery -A tasks.celery_app:celery worker --loglevel=info --concurrency=4 --max-tasks-per-child=50 > /dev/null 2>&1 &
echo "    celery 启动中..."

sleep 3

# ---------- 检测状态 ----------
echo ""
echo "=============================="

# 检测 gunicorn
if pgrep -f "gunicorn.*app:create_app" > /dev/null; then
    G_PID=$(pgrep -f "gunicorn.*app:create_app" | head -1)
    echo "  gunicorn  [ 成功 ] PID: $G_PID"
else
    echo "  gunicorn  [ 失败 ]"
fi

# 检测 celery
if pgrep -f "celery.*tasks.celery_app:celery worker" > /dev/null; then
    C_PID=$(pgrep -f "celery.*tasks.celery_app:celery worker" | head -1)
    echo "  celery    [ 成功 ] PID: $C_PID"
else
    echo "  celery    [ 失败 ]"
fi

echo "=============================="
