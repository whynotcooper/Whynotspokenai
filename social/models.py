from django.db import models
from django.utils.text import slugify
from spoken_ai.models import UserInfoModel


class UserProfile(models.Model):
    user = models.OneToOneField(UserInfoModel, on_delete=models.CASCADE, related_name="profile_ext")
    nickname = models.CharField(max_length=50, blank=True, default="", verbose_name="昵称")
    bio = models.CharField(max_length=200, blank=True, default="", verbose_name="个性签名")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "social_user_profile"

    def __str__(self):
        return self.nickname or self.user.username


class Post(models.Model):
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


class ForumRoom(models.Model):
    name = models.CharField(max_length=60, unique=True, verbose_name="房间名")
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "social_forum_room"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            # 对中文字符生成拼音或UUID slug
            slug = slugify(self.name)
            if not slug:  # 如果slugify返回空字符串（如纯中文）
                import uuid
                slug = f"room-{uuid.uuid4().hex[:8]}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ForumMessage(models.Model):
    room = models.ForeignKey(ForumRoom, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(UserInfoModel, on_delete=models.SET_NULL, null=True, blank=True)
    author_name = models.CharField(max_length=100, default="", blank=True)
    content = models.TextField(max_length=500, verbose_name="消息内容")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "social_forum_message"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.room.name} - {self.author_name or 'unknown'}"


class PostComment(models.Model):
    post = models.ForeignKey("Post", on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(UserInfoModel, on_delete=models.SET_NULL, null=True, blank=True)
    author_name = models.CharField(max_length=100, default="", blank=True)
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "social_post_comment"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.post_id} - {self.author_name[:20]}"

class LobbyMessage(models.Model):
    author = models.ForeignKey(
        UserInfoModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lobby_messages"
    )
    author_name = models.CharField(max_length=100, default="", blank=True)
    text = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "social_lobby_message"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author_name}: {self.text[:30]}"
