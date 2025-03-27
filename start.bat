@echo off
chcp 65001 > nul
echo ===== �Զ����������ű� =====

REM ��ȡ��ǰ�ű�����Ŀ¼
set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

REM �������⻷��(�������)
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo �Ѽ������⻷��
) else (
    echo ����: δ�ҵ����⻷����ʹ��ϵͳPython
)

REM ���ö˿�
set DJANGO_PORT=8896
set DAPHNE_PORT=8896
set FLOWER_PORT=5566

REM ������������
echo.
echo ��������Django���� (�˿�: %DJANGO_PORT%)...
start cmd /k "title Django���� && python manage.py runserver 0.0.0.0:%DJANGO_PORT%"
timeout /t 5 /nobreak > nul

echo ��������Celery Beat����...
start cmd /k "title Celery Beat && python -m celery -A server beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler --max-interval 60"
timeout /t 5 /nobreak > nul

echo ��������Celery Worker����...
start cmd /k "title Celery Worker && python -m celery -A server worker -P threads -l INFO -c 10 -Q celery --heartbeat-interval 10 -n celery@%%h --without-mingle"
timeout /t 5 /nobreak > nul

echo ��������Flower���� (�˿�: %FLOWER_PORT%)...
start cmd /k "title Flower��� && python -m celery -A server flower --logging=info --url_prefix=api/flower --auto_refresh=False --address=0.0.0.0 --port=%FLOWER_PORT%"

echo ��������WebSocket���� (�˿�: %DAPHNE_PORT%)...
start cmd /k "title WebSocket���� && daphne -p %DAPHNE_PORT% server.asgi:application"
timeout /t 5 /nobreak > nul

echo.
echo ���з����������!
echo Django�����ַ: http://localhost:%DJANGO_PORT%
echo Flower��ص�ַ: http://localhost:%FLOWER_PORT%
echo WebSocket�����ַ: ws://localhost:%DAPHNE_PORT%
