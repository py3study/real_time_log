# 说明
linux日志管理系统，实现日志下载以及日志实时查看功能。

日志主要在/var/log目录


# 运行原理
```text
本程序运行在跳板机这台服务器，它可以免密登录所有后端主机，使用ls -l /var/log查看后端目录列表。
使用Python调用系统命令，将结果通过html来展示。
下载时，先将后端服务器日志scp到跳板机的/tmp/log_download目录，然后使用django实现日志下载。
查看实时日志，采用websocket，后端调用tail -f命令

```

# 配置文件
修改 setting.py，主要修改以下参数
```bash
# 日志根目录
LOG_BASE_DIR = "/var/log"
# 每一页显示几条
PAGE_SIZE = 10
# 分页数
PAGE_NUM_PAGES = 11
# 服务器ssh端口
SSH_PORT = 22
# 下载日志目录
DOWN_LOG_DIR = "/tmp/log_download"
```


## sqlite插入记录
```sql
INSERT INTO "main"."application_host" ("id", "hostname", "ipaddr", "create_time", "ROWID") VALUES (1, 'test-1', '192.168.31.221', '2020-03-31 11:16:03', 1);

```
注意：请修改为自己的服务器，确保已经做了ssh免密

# 运行
```bash
python3 manage.py runserver 0.0.0.0:8000
```

# 效果
首页

![Image text](https://github.com/py3study/real_time_log/blob/master/result/1.png)

目录浏览

![Image text](https://github.com/py3study/real_time_log/blob/master/result/2.png)

实时日志

![Image text](https://github.com/py3study/real_time_log/blob/master/result/3.gif)

# 注意事项
```bash
1. 如果使用https方式访问，需要修改view_log.html，将ws修改为wss。
2. 本项目使用root权限运行，如果是普通用户，请加sudo执行。
```

Copyright (c) 2020-present, xiao You
