#!/usr/bin/env python3
# coding: utf-8
"""
共有的方法
"""

# import sys
# import io
#
# def setup_io():  # 设置默认屏幕输出为utf-8编码
#     sys.stdout = sys.__stdout__ = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', line_buffering=True)
#     sys.stderr = sys.__stderr__ = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', line_buffering=True)
# setup_io()
import os
import re
import signal
import sys
import time
# import json
import socket
import paramiko
import subprocess
# import ipaddress
# import requests
import hashlib
import datetime
from real_time_log import settings

def write_log(content,colour='white',skip=False):
    """
    写入日志文件
    :param content: 写入内容
    :param colour: 颜色
    :param skip: 是否跳过打印时间
    :return:
    """
    # 颜色代码
    colour_dict = {
        'red': 31,  # 红色
        'green': 32,  # 绿色
        'yellow': 33,  # 黄色
        'blue': 34,  # 蓝色
        'purple_red': 35,  # 紫红色
        'bluish_blue': 36, # 浅蓝色
        'white': 37,  # 白色
    }
    choice = colour_dict.get(colour)  # 选择颜色

    path = "output.log"  # 日志文件
    with open(path, mode='a+', encoding='utf-8') as f:
        if skip is False:  # 不跳过打印时间时
            content = time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + content

        info = "\033[1;{};1m{}\033[0m".format(choice, content)
        print(info)
        f.write(content+"\n")

def execute_linux(cmd, timeout=10, skip=False):
    """
    执行linux命令,返回list
    :param cmd: linux命令
    :param timeout: 超时时间,生产环境, 特别卡, 因此要3秒
    :param skip: 是否跳过超时限制
    :return: dict
    """
    result = {'status': 1, 'data': None}  # 返回结果
    p = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE,shell=True,close_fds=True,preexec_fn=os.setsid)

    t_beginning = time.time()  # 开始时间
    while True:
        if p.poll() is not None:
            break
        seconds_passed = time.time() - t_beginning
        if not skip:
            if seconds_passed > timeout:
                # p.terminate()
                # p.kill()
                # raise TimeoutError(cmd, timeout)
                # write_log('错误, 命令: {},本地执行超时!'.format(cmd), "red")
                print('错误, 命令: {},本地执行超时!'.format(cmd))
                # 当shell=True时，只有os.killpg才能kill子进程
                try:
                    # time.sleep(1)
                    os.killpg(p.pid, signal.SIGUSR1)
                except Exception as e:
                    pass
                return False

    # 修改返回结果
    result['status'] = p.returncode
    result['data'] = p.stdout.readlines()  # 结果输出列表

    return result

# # 读取配置文件中ssh端口号
# cmd = "sudo cat /etc/ssh/sshd_config|grep ^Port|awk '{print $2}'"
# res = execute_linux(cmd)
# if not res or res['status'] != 0:
#     write_log("错误, 执行命令: {} 失败".format(cmd), "red")
#     exit()
#
# # 判断为空时，使用默认端口22
# if res['data'] == []:
#     # print("使用默认端口")
#     SSH_PORT = 22
# else:
#     # 使用配置文件中的端口号
#     SSH_PORT = res['data'][0].decode('utf-8').strip()
#     if not SSH_PORT.isdigit():
#         write_log("错误，获取本机ssh端口失败","red")
#         exit()

def ssh3(ip, cmd,seconds=10):
    """
    使用ssh连接远程服务器执行命令
    :param cmd: 执行的命令
    :param seconds: 执行命令的超时时间
    :return: list
    """
    result = {'status': 1, 'data': None}  # 返回结果
    try:
        ssh = paramiko.SSHClient()  # 创建一个新的SSHClient实例
        ssh.banner_timeout = seconds
        # 设置host key,如果在"known_hosts"中没有保存相关的信息, SSHClient 默认行为是拒绝连接, 会提示yes/no
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, settings.SSH_PORT, timeout=seconds)  # 连接远程服务器,超时时间1秒
        stdin, stdout, stderr = ssh.exec_command(cmd,get_pty=True,timeout=seconds)  # 执行命令
        out = stdout.readlines()    # 执行结果,readlines会返回列表
        # print(stderr.readlines())
        # # 执行状态,0表示成功，1表示失败
        channel = stdout.channel
        status = channel.recv_exit_status()
        # print("status",status,type(status))

        ssh.close()  # 关闭ssh连接
        # 修改返回结果
        result['status'] = status
        result['data'] = out
        return result
    except Exception as e:
        print(e)
        # print("登录服务器或者执行命令超时!!!","ip:",ip,"命令: ",cmd)
        write_log("错误, 登录服务器或者执行命令超时!!! ip: {} 命令: {}".format(ip,cmd),"red")
        return False

def get_log_list(host,dir):
    """
    日志列表
    :param host: ip地址
    :param dir: 目录名
    :return: list
    """
    # print("LOG_BASE_DIR",settings.LOG_BASE_DIR)
    dir_path = os.path.join(settings.LOG_BASE_DIR,dir)
    # print("dir_path",dir_path)
    # ls -lht可以查看文件大小以M来显示
    # --time-style '+%Y/%m/%d %H:%M:%S' 自定义显示方式
    cmd = "ls -lht --time-style '+%Y-%m-%d %H:%M:%S' {}".format(dir_path)
    # print("cmd",cmd,"host",host)
    # result = execute_linux(cmd)
    result = ssh3(host,cmd)
    # print("result", result,type(result))
    # ip = "localhost"

    file_list = []
    # print("0",result['data'][0])
    # if "无法访问" in result['data'][0] or not result or result['status'] != 0:
    if not result or result['status'] != 0:
        write_log("错误，主机: {}，日志目录不存在！".format(host),"red")
        return False
        # return render(request, "log_list.html", {"id": id, "file_list": file_list, "error_info": error_info})

    # 删除头部信息
    del result['data'][0]
    # print("结果0",result['data'])

    # if not result['data']:
    #     write_log("错误，ip: {}，日志目录为空！".format(ip), "red")
    #     return False

    # print(22222222222222)
    for i in result['data']:
        # i = i.decode('utf-8').strip()
        i = i.strip()
        # print("iii",i)
        # file_list.append(i)
        cut_str = i.split()
        # print("cut_str",cut_str)
        file_dict = {}
        if not file_dict.get('type'):
            # 截取第一个字符串
            f_prefix = cut_str[0][0]
            # 判断是否为文件夹
            if f_prefix == 'd':
                f_type = "dir"
            else:
                f_type = "file"

            # print("f_type",f_type)
            file_dict['type'] = f_type

        if not file_dict.get('size'):
            file_dict['size'] = cut_str[4]

        if not file_dict.get('time'):
            file_dict['time'] = "%s %s"%(cut_str[5],cut_str[6])

        # 文件名
        file_name = cut_str.pop()
        # 文件后缀
        file_suffix = file_name.split('.').pop()
        # print(file_suffix)

        if not file_dict.get('name'):
            file_dict['name'] = file_name

        # 判断是否可以实时查看日志
        if not file_dict.get('view'):
            if file_suffix == 'log':
                file_dict['view'] = '1'
            else:
                file_dict['view'] = '0'

        file_list.append(file_dict)
        
    # if not file_list:
    #     return False


    return file_list

def fuzzy_finder(key, data):
    """
    模糊查找器
    :param key: 关键字
    :param data: 数据
    :return: list
    """
    # 结果列表
    suggestions = []
    # 非贪婪匹配，转换 'djm' 为 'd.*?j.*?m'
    # pattern = '.*?'.join(key)
    pattern = '.*%s.*'%(key)
    print("pattern",pattern)
    # 编译正则表达式
    regex = re.compile(pattern)
    for item in data:
        # print("item",item['name'])
        # 检查当前项是否与regex匹配。
        match = regex.search(item['name'])
        if match:
            # 如果匹配，就添加到列表中
            suggestions.append(item)

    return suggestions


def get_search_log_list(host, dir,key):
    """
    获取搜索日志列表
    :param host: ip地址
    :param dir: 目录名
    :param dir: 关键字
    :return: dict
    {
        "access.log": {
            "type": "dir",
            "size": "123",
            "name": "access.log",
        },
        "access.log.gz": {
            "type": "dir",
            "size": "123",
            "name": "access.log",
        },
    }
    """
    result = get_log_list(host, dir)
    if not result:
        return False

    # 搜索关键字
    search_dict = fuzzy_finder(key, result)
    # print("search_dict",search_dict)
    if not search_dict:
        return {}

    # if not search_dict:
    #     return False

    return search_dict

def get_md5(value):
    md5obj = hashlib.md5()  # 创建md5对象
    md5obj.update(value.encode(encoding='utf-8'))
    return md5obj.hexdigest()


def cleanup_log():
    """
    清理下载日志
    :param path: 文件路径
    :return: bool
    """
    # 判断指定的目录是否存在
    if not os.path.exists(settings.DOWN_LOG_DIR):
        os.mkdir(settings.DOWN_LOG_DIR)

    file_list = [settings.DOWN_LOG_DIR]  # 文件夹列表
    # 获取当前时间
    today = datetime.datetime.now()
    # 计算偏移量,前1天
    offset = datetime.timedelta(days=-1)
    # 获取想要的日期的时间,即前1天时间
    re_date = (today + offset)
    # 前1天时间转换为时间戳
    re_date_unix = time.mktime(re_date.timetuple())

    write_log("开始清理下载目录","green")
    try:
        while file_list:  # 判断列表是否为空
            path = file_list.pop()  # 删除列表最后一个元素，并返回给path l = ['E:\python_script\day26']
            for item in os.listdir(path):  # 遍历列表,path = 'E:\python_script\day26'
                path2 = os.path.join(path, item)  # 组合绝对路径 path2 = 'E:\python_script\day26\test'
                if os.path.isfile(path2):  # 判断绝对路径是否为文件
                    # 比较时间戳,文件修改时间小于等于3天前
                    if os.path.getmtime(path2) <= re_date_unix:
                        os.remove(path2)
                        write_log('删除文件{}'.format(path2),"green")
                else:
                    if not os.listdir(path2):  # 判断目录是否为空
                        # 若目录为空，则删除，并递归到上一级目录，如若也为空，则删除，依此类推
                        os.removedirs(path2)
                        write_log('删除空目录{}'.format(path2),"green")
                    else:
                        # 为文件夹时,添加到列表中。再次循环。l = ['E:\python_script\day26\test']
                        file_list.append(path2)

        write_log("清理下载目录成功", "green")
        return True
    except Exception as e:
        print(e)
        write_log("清理下载目录失败", "red")
        return False