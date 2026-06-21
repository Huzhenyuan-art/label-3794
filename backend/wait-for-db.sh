#!/bin/bash

set -e

MAX_RETRIES=30
RETRY_INTERVAL=2

echo "等待数据库连接就绪..."

for attempt in $(seq 1 $MAX_RETRIES); do
    if python -c "
import os
import sys
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', '3306'))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '123456')
DB_NAME = os.getenv('DB_NAME', 'label_portal')

uri = f'mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4&connect_timeout=5'

try:
    engine = create_engine(uri, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
        conn.commit()
    print('数据库连接成功')
    sys.exit(0)
except Exception as e:
    print(f'数据库连接失败（第 {attempt}/$MAX_RETRIES 次）：{e}')
    sys.exit(1)
" 2>&1; then
        echo "数据库已就绪，启动应用..."
        exec "$@"
    fi

    if [ $attempt -lt $MAX_RETRIES ]; then
        echo "等待 $RETRY_INTERVAL 秒后重试..."
        sleep $RETRY_INTERVAL
    fi
done

echo "数据库连接重试次数已达上限，启动失败"
exit 1
