from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator

# 用户信息表
class UserInfoModel(models.Model):
    username = models.CharField(
        max_length=100, 
        verbose_name='用户名',
        unique=True,  # 添加唯一约束
        validators=[
            RegexValidator(
                regex='^[a-zA-Z0-9_]+$',
                message='用户名只能包含字母、数字和下划线',
                code='invalid_username'
            )
        ]
    )
    
    password = models.CharField(
        max_length=100, 
        verbose_name='密码',
        validators=[
            MinLengthValidator(10, message='密码必须至少10位')
        ]
    )
    
    phone = models.CharField(
        max_length=11,  # 改为11位，符合手机号标准
        verbose_name='手机号',
        unique=True,  # 手机号唯一
        validators=[
            RegexValidator(
                regex='^1[3-9]\d{9}$',
                message='请输入有效的手机号',
                code='invalid_phone'
            )
        ]
    )
    
    money = models.DecimalField(  # 改为DecimalField，更适合金额
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        verbose_name='余额'
    )
    
    # 添加英语学习相关字段
    ENGLISH_LEVEL_CHOICES = [
        ('beginner', '初级'),
        ('intermediate', '中级'),
        ('advanced', '高级'),
    ]
    
    english_level = models.CharField(
        max_length=20,
        choices=ENGLISH_LEVEL_CHOICES,
        default='beginner',
        verbose_name='英语水平'
    )
    
    # 添加用户状态字段
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'db_user_info'
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']  # 默认按创建时间降序排列

    def __str__(self):
        return self.username
    

# models.py


class TaskCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name='任务描述')

    class Meta:
        db_table = 'db_task_category'
        verbose_name = '任务类别'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Task1Model(models.Model):
    name = models.CharField(max_length=200, verbose_name='任务名称')
    readingtext = models.TextField(verbose_name='阅读文本')
    answertext1 = models.TextField(verbose_name='答案1')
    answertext2 = models.TextField(verbose_name='答案2')
    reasontext = models.TextField(verbose_name='解题思路')
    
    category = models.ForeignKey(
        TaskCategory,
        on_delete=models.CASCADE,
        related_name='task1_tasks',      # ✅ 合法的 related_name
        verbose_name='所属类别'           # ✅ 中文放这里
    )

    class Meta:
        db_table = 'db_task1'
        verbose_name = '任务1'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Task2Model(models.Model):
    name = models.CharField(max_length=200, verbose_name='任务名称')
    
    # 阅读部分：校园公告/通知
    readingtext = models.TextField(verbose_name='阅读文本（公告）')
    
    # 听力部分
    audio = models.FileField(upload_to='task2_audio/', verbose_name='听力音频 (m4a)')
    listeningtext = models.TextField(verbose_name='听力文本（学生观点）')
    
    # 问题 & 答案
    questiontext = models.TextField(verbose_name='问题')
    answertext1 = models.TextField(verbose_name='答案1')
    answertext2 = models.TextField(verbose_name='答案2')
    reasontext = models.TextField(verbose_name='解题思路')

    # 分类（可选，与 Task1 共用）
    category = models.ForeignKey(
        TaskCategory,
        on_delete=models.CASCADE,
        related_name='task2_tasks',
        verbose_name='所属类别'
    )

    class Meta:
        db_table = 'db_task2'
        verbose_name = '任务2'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name