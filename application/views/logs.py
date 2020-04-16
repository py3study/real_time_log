#!/usr/bin/env python3
# coding: utf-8

from django.shortcuts import render, HttpResponse, redirect
from dwebsocket.decorators import accept_websocket, require_websocket
import paramiko
import os
import json
from real_time_log import settings
from utils.common import write_log, ssh3
from utils.response import BaseResponse


def view_log(request):
    """
    查看实时日志
    :param request:
    :return:
    """
    ip = request.GET.get('ip')
    # port = settings.SSH_PORT
    dir = request.GET.get('dir')
    # 日志文件
    file_name = request.GET.get('file_name')
    log_file = os.path.join(settings.LOG_BASE_DIR, dir, file_name)
    data = {
        "ip": ip,
        "dir": dir,
        "file_name": file_name,
        "log_file": log_file
    }
    return render(request, "view_log.html", data)


@accept_websocket
def real_time_log(request):
    # ip,port,username,password=server_info(id)
    # print(request.GET)
    ip = request.GET.get('ip')
    port = settings.SSH_PORT
    dir = request.GET.get('dir')
    # 日志文件
    file_name = request.GET.get('file_name')
    log_file = os.path.join(settings.LOG_BASE_DIR, dir, file_name)
    # print("log_file",log_file)
    # log_file = request.GET.get('file')
    if not request.is_websocket():  # 判断是不是websocket连接
        message = request.GET['message']
        return HttpResponse(message)


    for message in request.websocket:
        # print("message",message,type(message))
        if not message:
            return HttpResponse('jquery发送消息不能为空！')

        message = message.decode('utf-8')  # 接收前端发来的数据
        # print("message",message)

        if message != 'view_logs':  # 这里根据web页面获取的值进行对应的操作
            request.websocket.send('小样儿，没权限!!!'.encode('utf-8'))
            return HttpResponse('小样儿，没权限!!!')

        # 先判断文件是否为空
        cmd = "wc -c %s|awk '{print $1}'" % log_file
        print("统计文件行数，命令：%s"%cmd)
        result = ssh3(ip, cmd)
        # print("result", result,type(result))

        if not result or result['status'] != 0:
            # print("获取文件大小失败")
            request.websocket.send("Failed to get file size")  # 发送消息到客户端
            return HttpResponse("Failed to get file size")
            # request.websocket
            # return HttpResponse("错误，主机: {}，ssh连接失败！".format(ip))
        value = result['data'].pop().strip()
        if value == '0':
            # print("文件内容为空")
            request.websocket.send("File content is empty")  # 发送消息到客户端
            # time.sleep(0.1)
            return HttpResponse("File content is empty")

        command = "tail -f %s" % (log_file)
        # command = "tail -1000 %s" % (log_file)
        print("查看实时日志，命令：", command)
        # return HttpResponse(log_file)
        # 远程连接服务器
        # print(11111)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port, timeout=10)
        # print(2222)
        # 务必要加上get_pty=True,否则执行命令会没有权限
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
        # result = stdout.read()
        # print(33333)
        # print("result", stdout.readline().strip())
        # 循环发送消息给前端页面
        while True:
            nextline = stdout.readline()  # 读取脚本输出内容
            # nextline = stdout.readline()  # 读取脚本输出内容
            # 切分字符串长度，最多80
            # film_type = '都市浪漫爱情喜剧'
            # film_type_new = []
            # for i in range(0, len(nextline), 80):
            #     film_type_new.append(nextline[i:i + 80])
            #
            # for i in film_type_new:
            #     print("发送字符串",i.strip().encode('utf-8'))
            #
            #     # print("nextline",nextline.strip())
            #     request.websocket.send(i.strip().encode('utf-8'))  # 发送消息到客户端
            request.websocket.send((nextline.strip()).encode('utf-8'))  # 发送消息到客户端
            # 判断消息为空时,退出循环
            if not nextline:
                # print("关闭1")
                break

        # print("关闭2")
        ssh.close()  # 关闭ssh连接





def close_log(request):
    """
    关闭实时日志
    :param request:
    :return:
    """

    res = BaseResponse()  # 初始化返回值
    if request.method == "POST":
        ip = request.POST.get('ip')
        dir = request.POST.get('dir')
        # 日志文件
        file_name = request.POST.get('file_name')
        log_file = os.path.join(settings.LOG_BASE_DIR, dir, file_name)
        # print("关闭日志%s" % log_file)

        cmd = "kill -9 `ps -aux|grep -v grep|grep %s|awk '{print $2}'`" % file_name
        print("关闭日志，命令：", cmd)
        result = ssh3(ip, cmd)
        # print("result", result,type(result))

        if not result or result['status'] != 0:
            res.code = 500
            res.error = "错误，主机: {}，关闭实时日志: {} 失败！".format(ip, log_file)
            return HttpResponse(json.dumps(res.__dict__))

    else:
        res.code = 500
        res.error = "非法请求"

    return HttpResponse(json.dumps(res.__dict__))
