#!/usr/bin/env python3
# coding: utf-8

import os
import json

from django.shortcuts import render, HttpResponse, redirect
from django.http import StreamingHttpResponse

from utils.common import execute_linux, write_log, get_log_list, ssh3,cleanup_log,get_search_log_list
from real_time_log import settings
from application import models
from utils.response import BaseResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def view_dir(request):
    """
    查看目录列表
    :param request:
    :return:
    """
    ip = request.GET.get('ip')
    if not ip:
        return HttpResponse("主机不能为空")

    # 判断主机是否存活
    cmd = "whoami"
    result = ssh3(ip, cmd)
    # print("result", result,type(result))

    if not result or result['status'] != 0:
        return HttpResponse("错误，主机: {}，ssh连接失败！".format(ip))

    dir = request.GET.get('dir')
    if not dir:
        dir = ''

    # 搜索关键字
    key = request.GET.get('search')
    # print("key",key)
    # 判断关键字是否存在
    if key:
        # print(1)
        log_list = get_search_log_list(ip, dir,key)
        # 分页a标签的herf前缀
        herf_prefix = "?ip={}&dir={}&search={}".format(ip,dir,key)
    else:
        log_list = get_log_list(ip, dir)
        # 分页a标签的herf前缀
        herf_prefix = "?ip={}&dir={}".format(ip,dir)

    # print("log_list",log_list)
    # log_list = get_log_list(ip, dir)
    if log_list is False:
        return HttpResponse("获取目录列表失败")
    elif log_list == []:
        return HttpResponse("目录列表为空")
    elif log_list == {}:
        return HttpResponse("搜索结果为空")
    else:
        pass

    dir_path = os.path.join(settings.LOG_BASE_DIR, dir)
    # next_dir_path = os.path.join(dir_path,dir)

    # 分页
    paginator = Paginator(log_list, settings.PAGE_SIZE)  # 每页显示指定的条数

    # 异常判断
    try:
        # 当前页码，如果取不到page参数，默认为1
        current_num = int(request.GET.get("page", 1))  # 当前页码
        log_list = paginator.page(current_num)  # 获取当前页码的数据
    except EmptyPage:  # 页码不存在时,报EmptyPage错误
        log_list = paginator.page(1)  # 强制更新为第一页

    #  如果页数十分多时，换另外一种显示方式
    if paginator.num_pages > settings.PAGE_NUM_PAGES:  # 一般网页展示11页,左5页,右5页,加上当前页,共11页
        if current_num - 5 < 1:  # 如果前5页小于1时
            pageRange = range(1, settings.PAGE_NUM_PAGES)  # 页码的列表:范围是初始状态
        elif current_num + 5 > paginator.num_pages:  # 如果后5页大于总页数时
            # 页码的列表:范围是(当前页-5,总页数+1)。因为range顾头不顾尾,需要加1
            pageRange = range(current_num - 5, paginator.num_pages + 1)
        else:
            # 页码的列表:后5页正常时,页码范围是(当前页-5,当前页+6)。注意不是+5,因为range顾头不顾尾！
            pageRange = range(current_num - 5, current_num + 6)
    else:
        pageRange = paginator.page_range  # 页码的列表

    data = {
        "paginator": paginator, "current_num": current_num, "pageRange": pageRange,"herf_prefix":herf_prefix,
        "ip": ip,
        "dir_path": dir_path,
        "dir": dir,
        "log_list": log_list,
        # "host_all": host_all
    }
    return render(request, "view_dir.html", data)


def get_dir_json(request):
    """
    目录列表json，供前端ajax调用
    :param request:
    :return:
    """
    res = BaseResponse()  # 初始化返回值
    if request.method == "POST":
        ip = request.POST.get('ip')
        dir = request.POST.get('dir')
        key = request.POST.get('key')
        if key:
            log_list = get_search_log_list(ip, dir,key)
            # 分页a标签的herf前缀
            herf_prefix = "?ip={}&dir={}&search={}".format(ip, dir, key)
        else:
            log_list = get_log_list(ip, dir)
            # 分页a标签的herf前缀
            herf_prefix = "?ip={}&dir={}".format(ip, dir)

        # print("log_list", log_list)
        if log_list is False:
            res.code = 500
            res.error = "获取目录列表失败"
        elif log_list == []:
            res.code = 500
            res.error = "目录列表为空"
        elif log_list == {}:
            res.code = 500
            res.error = "搜索结果为空"
        else:
            res.data = log_list
            res.url = "/view_dir/%s" % (herf_prefix)
    else:
        res.code = 500
        res.error = "非法请求"

    return HttpResponse(json.dumps(res.__dict__))


def download(request):
    """
    下载日志文件
    :param request:
    :return:
    """
    ip = request.GET.get('ip')
    dir = request.GET.get('dir')
    file_name = request.GET.get('file_name')

    host_obj = models.Host.objects.filter(ipaddr=ip).first()
    if not host_obj:
        return HttpResponse("错误，主机: %s 不存在"%ip)

    hostname = host_obj.hostname
    # print("dir", dir)
    # print("file_name", file_name)
    # 完整路径
    complete_path = os.path.join(settings.LOG_BASE_DIR, dir, file_name)
    # print("complete_path", complete_path)

    # 先清理下载目录中的文件
    if not cleanup_log():
        return HttpResponse("错误，清理下载目录失败","red")

    # scp文件到/tmp
    local_path = os.path.join('/tmp/log_download', hostname + '#' + file_name)
    local_file_name = hostname + '#' + file_name
    # print(host, local_path, local_file_name)
    # down = sftp_down_file(host, complete_path, local_path, timeout=10)
    cmd = "scp -P {} {}:{} {}".format(settings.SSH_PORT, ip, complete_path, local_path)
    res = execute_linux(cmd)
    # print("res",res,type(res))
    if not res or res['status'] != 0:
        write_log("错误, 执行命令: {} 失败".format(cmd), "red")
        return HttpResponse("下载主机: {}文件: {}到/tmp/log_download目录失败".format(hostname, complete_path))
        # return False
    # print("res",res,type(res))
    # if not res:
    #     return HttpResponse("下载主机: {}文件: {}到/tmp目录失败".format(host,complete_path))

    # return HttpResponse('download')
    if not os.path.isfile(local_path):  # 判断下载文件是否存在
        return HttpResponse("Sorry but Not Found the File")

    def file_iterator(file_path, chunk_size=512):
        """
        文件生成器,防止文件过大，导致内存溢出
        :param file_path: 文件绝对路径
        :param chunk_size: 块大小
        :return: 生成器
        """
        with open(file_path, mode='rb') as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break

    try:
        # 设置响应头
        # StreamingHttpResponse将文件内容进行流式传输，数据量大可以用这个方法
        response = StreamingHttpResponse(file_iterator(local_path))
        # 以流的形式下载文件,这样可以实现任意格式的文件下载
        response['Content-Type'] = 'application/octet-stream'
        # Content-Disposition就是当用户想把请求所得的内容存为一个文件的时候提供一个默认的文件名
        response['Content-Disposition'] = 'attachment;filename="{}"'.format(local_file_name)
    except Exception as e:
        return HttpResponse("Sorry but Not Found the File, msg:{}".format(e))

    return response

