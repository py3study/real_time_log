from django.db import models

# Create your models here.
class Host(models.Model):  # 主机
    hostname = models.CharField(max_length=32, verbose_name="主机名")
    ipaddr = models.CharField(max_length=32, verbose_name="IP地址")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        # 多列唯一索引
        unique_together = ('hostname','ipaddr')