from django.db import models

# Create your models here.
from django.db import models
from spoken_ai.models import UserInfoModel


class UserProfile(models.Model):
    """
    可选：单独存昵称/签名等展示信息，不用继续改 db_user_info 表结构
    """
    user = models.OneToOneField(UserInfoModel, on_delete=models.CASCADE, related_name="profile_ext")
    nickname = models.CharField(max_length=50, blank=True, default="", verbose_name="昵称")
    bio = models.CharField(max_length=200, blank=True, default="", verbose_name="个性签名")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "social_user_profile"

    def __str__(self):
        return self.nickname or self.user.username


class Post(models.Model):
    """
    小红书风格图文帖子：文字主体 + 多图
    """
    author = models.ForeignKey(UserInfoModel, on_delete=models.CASCADE, related_name="social_posts")
    title = models.CharField(max_length=80, blank=True, default="", verbose_name="标题")
    content = models.TextField(blank=True, default="", verbose_name="正文")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True)

    class Meta:
        db_table = "social_post"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author.username} - {self.title[:20]}"


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="posts/%Y/%m/%d/")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "social_post_image"
        ordering = ["order", "id"]
# social/models.py

from django.utils.text import slugify


class ForumRoom(models.Model):
    name = models.CharField(max_length=60, unique=True, verbose_name="房间名")
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "social_forum_room"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ForumMessage(models.Model):
    room = models.ForeignKey(ForumRoom, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(UserInfoModel, on_delete=models.SET_NULL, null=True, blank=True)
    author_name = models.CharField(max_length=100, default="", blank=True)  # 兜底显示名
    content = models.TextField(max_length=500, verbose_name="消息内容")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "social_forum_message"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.room.name} - {self.author_name or 'unknown'}"
