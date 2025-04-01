# xadmin-server

xadmin-基于Django+vue3的rbac权限管理系统

前端 [xadmin-client](https://github.com/nineaiyu/xadmin-client)

## 项目目录结构
~~~
├── captcha                     #图片验证码应用
├── common                      # 项目工具类库，包含各种封装方法
├── config.yml                   # 运行配置文件，包含数据库，Redis等配置信息
├── docker-compose-sqlite.yml
├── docker-compose.yml          # docker compose 运行文件
├── Dockerfile                  # 用与构建容器镜像文件
├── LICENSE
├── loadjson                  # 默认的菜单，权限，字段配置
├── locale                    # 国际化配置，支持中文和英语
├── logs                      # 运行日志
├── manage.py
├── message                   # websocket 消息
├── notifications             # 站内信，消息通知推送应用
├── README.md
├── requirements.txt          # Django 运行依赖
├── server                    # 项目主应用
├── settings                  # 项目相关配置应用
└── system                    # 系统应用，包含用户，菜单，日志，角色等
~~~

## 开发部署文档

修改配置文件
~~~ shell
cp config_example.yml config.yml
~~~
a.将config.yml里面的 DB_PASSWORD ， REDIS_PASSWORD 取消注释
~~~ shell
sed -i "s@^#DB_PASSWORD:@DB_PASSWORD:@" config.yml
sed -i "s@^#REDIS_PASSWORD:@REDIS_PASSWORD:@" config.yml
~~~
b.生成，并填写 SECRET_KEY

~~~ shell
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
~~~
生产数据表并迁移
~~~ shell
python manage.py makemigrations
python manage.py migrate
~~~
收集静态资源，编译国际化，下载IP数据库
~~~ shell
python manage.py collectstatic
python manage.py compilemessages
python manage.py download_ip_db -f
~~~
创建超级管理员
~~~ shell
python manage.py createsuperuser
~~~
导入默认菜单，权限，角色等数据（仅新部署执行一次）
~~~ shell
python manage.py load_init_json
~~~
启动程序
- api服务
~~~ shell
python manage.py runserver 0.0.0.0:8896
~~~
- celery服务
~~~ shell
python -m celery -A server beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler --max-interval 60
python -m celery -A server worker -P threads -l INFO -c 10 -Q celery --heartbeat-interval 10 -n celery@%h --without-mingle
~~~
- celery flower服务
~~~ shell
python -m celery -A server flower -logging=info --url_prefix=api/flower --auto_refresh=False  --address=0.0.0.0 --port=5566
~~~
- WebSocket
~~~ shell
daphne -p 8896 server.asgi:application
~~~
# 附录

⚠️ Windows上面无法正常运行celery flower，导致任务监控无法正常使用，请使用Linux环境开发部署

## 启动程序(启动之前必须配置好Redis和数据库)

### A.一键执行命令【不支持windows平台，如果是Windows，请使用 手动执行命令】

```shell
python manage.py start all -d  # -d 参数是后台运行，如果去掉，则前台运行
```


#### Other
~~~
1. 通知模块核心文件 ：
   
   - notifications/message.py - 包含消息发送的核心工具类
   - notifications/notifications.py - 包含消息类型定义和基类
   - notifications/models.py - 包含消息存储的数据模型
2. 任务模块核心文件 ：
   
   - server/celery.py - Celery配置文件
   - common/celery/decorator.py - 任务装饰器定义
   - common/tasks.py - 通用任务定义
~~~
