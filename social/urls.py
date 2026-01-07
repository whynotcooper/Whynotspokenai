from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('profile/<str:username>/', views.profile, name='profile'),
    path("post/new/", views.post_create, name="post_create"),
    path("forum/", views.forum_home, name="forum_home"),
    path("forum/<slug:slug>/", views.chat_room, name="chat_room"),
    # ✅ 新增：用于弹窗的用户信息接口
    path('profile-card/<str:username>/', views.profile_card, name='profile_card'),
    # 接口：发送消息 / 拉取新消息（AJAX）
    path("forum/<slug:slug>/send/", views.send_message, name="send_message"),
    path("forum/<slug:slug>/poll/", views.poll_messages, name="poll_messages"),
]
