#!/bin/bash
# 启动监控脚本

cd "$(dirname "$0")"

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "虚拟环境不存在，正在创建..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# 运行监控脚本
python monitor.py

