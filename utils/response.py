#!/usr/bin/env python
# coding: utf-8
class BaseResponse(object):
    """
    返回response
    """
    def __init__(self):
        self.code = 200
        self.data = None
        self.error = None

    @property
    def dict(self):
        return self.__dict__


'''
response = BaseResponse()  # 默认状态
object
    code:200    # 前端代码判断
    data:None    # 前端渲染页面
    error:None   # 前端错误展示

{'code':1000,'data':None,'error':None}
'''

CODE = {
    "200":"正常",
    "500":"目录已经存在",
    "501":"删除失败",
    "502":"上传失败",
    "503":"请求方式非法",
    "504":"远程scp失败",
    "505":"远程解压文件失败",
    "506":"用户名不存在",
    "507":"更新密码失败",
}