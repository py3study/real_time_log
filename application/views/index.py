#!/usr/bin/env python3
# coding: utf-8
from django.shortcuts import render, HttpResponse, redirect
from application import models
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from real_time_log import settings


def index(request):
    """
    用户首页
    :param request:
    :return:
    """
    # 服务器
    # 所有主机
    host_list = models.Host.objects.all()

    # host = request.GET.get('host')
    # if not host:
    #     # 为空时，获取第一条记录
    #     host = host_all.first().hostname
    #
    # log_list = get_log_list(host, '')
    # # print("log_list11", log_list)
    # if not log_list:
    #     log_list = []
    # 分页
    paginator = Paginator(host_list, settings.PAGE_SIZE)  # 每页显示指定的条数

    # 异常判断
    try:
        # 当前页码，如果取不到page参数，默认为1
        current_num = int(request.GET.get("page", 1))  # 当前页码
        host_list = paginator.page(current_num)  # 获取当前页码的数据
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
        "paginator": paginator, "current_num": current_num, "pageRange": pageRange,
        # "host": host,
        # "log_base": settings.LOG_BASE_DIR,
        # "dir": "/",
        # "log_list": log_list,
        "host_list":host_list
    }
    return render(request, "index.html", data)