# Generated by Django 2.1.8 on 2020-04-16 08:06

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hostname', models.CharField(max_length=32, verbose_name='主机名')),
                ('ipaddr', models.CharField(max_length=32, verbose_name='IP地址')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='host',
            unique_together={('hostname', 'ipaddr')},
        ),
    ]