# admin.py
from django.contrib import admin
from .models import (
    UserInfoModel,
    TaskCategory,
    Task1Model,
    Task2Model,
    Task3Model,
)


@admin.register(UserInfoModel)
class UserInfoAdmin(admin.ModelAdmin):
    # 列表页显示的字段
    list_display = (
        'id',
        'username',
        'phone',
        'money',
        'english_level',
        'is_active',
        'create_time',
    )
    # 可点击进入详情的字段
    list_display_links = ('id', 'username')
    # 支持搜索的字段
    search_fields = ('username', 'phone')
    # 右侧筛选
    list_filter = ('english_level', 'is_active', 'create_time')
    # 只读字段（创建/更新时间一般不允许手动改）
    readonly_fields = ('create_time', 'update_time')
    # 列表默认排序
    ordering = ('-create_time',)


@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)


@admin.register(Task1Model)
class Task1Admin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'readingtext', 'answertext1', 'answertext2')
    list_filter = ('category',)


@admin.register(Task2Model)
class Task2Admin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'readingtext', 'listeningtext', 'questiontext')
    list_filter = ('category',)
    # 如果你希望文件上传路径只读，可以加：
    # readonly_fields = ('audio',)


@admin.register(Task3Model)
class Task3Admin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'readingtext', 'listeningtext', 'questiontext')
    list_filter = ('category',)
    # readonly_fields = ('audio',)
