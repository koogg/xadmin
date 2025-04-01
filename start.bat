@echo off
chcp 65001 > nul
echo ===== 启动开发环境 =====

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

REM 激活虚拟环境（如果存在）
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo [成功] 虚拟环境已激活
) else (
    echo [错误] 未找到虚拟环境，请先安装 Python 并创建虚拟环境！
    exit /b
)

REM 端口设置
set DJANGO_PORT=8896
set DAPHNE_PORT=8896
set FLOWER_PORT=5566

REM 启动 Django 开发服务器
echo.
echo [启动] Django 服务器 (端口: %DJANGO_PORT%)...
start cmd /k "title Django 服务器 && python manage.py runserver 0.0.0.0:%DJANGO_PORT%"
timeout /t 5 /nobreak > nul

REM 启动 Celery Beat
echo [启动] Celery Beat...
start cmd /k "title Celery Beat && python -m celery -A server beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler --max-interval 60"
timeout /t 5 /nobreak > nul

REM 启动 Celery Worker
echo [启动] Celery Worker...
start cmd /k "title Celery Worker && python -m celery -A server worker -P threads -l INFO -c 10 -Q celery --heartbeat-interval 10 -n celery@%COMPUTERNAME% --without-mingle"
timeout /t 5 /nobreak > nul

REM 启动 Flower 监控
echo [启动] Flower 监控 (端口: %FLOWER_PORT%)...
start cmd /k "title Flower 监控 && python -m celery -A server flower --logging=info --url_prefix=api/flower --auto_refresh=False --address=0.0.0.0 --port=%FLOWER_PORT%"

REM 启动 WebSocket 服务器
echo [启动] WebSocket 服务器 (端口: %DAPHNE_PORT%)...
start cmd /k "title WebSocket 服务器 && daphne -p %DAPHNE_PORT% server.asgi:application"
timeout /t 5 /nobreak > nul

echo.
echo === 所有服务已启动! ===
echo Django 服务器: http://localhost:%DJANGO_PORT%
echo Flower 监控: http://localhost:%FLOWER_PORT%
echo WebSocket 服务器: ws://localhost:%DAPHNE_PORT%
