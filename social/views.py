from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Prefetch
from spoken_ai.models import UserInfoModel
from .models import Post, PostImage, UserProfile




def _require_login(request):
    """你现在不是 Django auth，这里用 session 做登录校验"""
    if not request.session.get("login_in"):
        # next 让登录后回到当前页面
        return redirect(f"/login/?next={request.path}")
    return None


# social/views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseForbidden
from .models import UserInfoModel, UserProfile, Post
from .forms import AvatarForm, ProfileForm

# social/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_http_methods


from spoken_ai.models import UserInfoModel
from .models import UserProfile, Post, PostImage
from .forms import ProfileForm, AvatarForm, PostForm


@require_http_methods(["GET", "POST"])
def profile(request, username):
    profile_user = get_object_or_404(UserInfoModel, username=username)
    profile_ext, _ = UserProfile.objects.get_or_create(user=profile_user)

    # ✅ 是否本人
    current_user_id = request.session.get("user_id")
    is_owner = bool(request.session.get("login_in")) and (str(current_user_id) == str(profile_user.id))

    # ✅ 自己看自己：看全部；别人看：只看公开
    posts_qs = Post.objects.filter(author=profile_user)
    if not is_owner:
        posts_qs = posts_qs.filter(is_public=True)

    # ✅ 重要：按时间/ID倒序，避免“看起来没更新”
    posts_qs = posts_qs.order_by("-created_at", "-id") if hasattr(Post, "created_at") else posts_qs.order_by("-id")

    # ✅ 关键：兼容不同 related_name
    # - 如果 PostImage.post 设置了 related_name="images" → 用 images
    # - 如果没设置 → Django 默认是 postimage_set
    try:
        posts_qs = posts_qs.prefetch_related("images")
        posts = list(posts_qs)
        # 强制访问一次，确保 related_name 真存在
        _ = posts[0].images.all() if posts else None
        rel_name = "images"
    except Exception:
        posts_qs = posts_qs.prefetch_related("postimage_set")
        posts = list(posts_qs)
        rel_name = "postimage_set"

    # ✅ 给模板一个统一入口：post._imgs
    for p in posts:
        p._imgs = getattr(p, rel_name).all()

    # ✅ 处理编辑资料
    if request.method == "POST":
        if not is_owner:
            return HttpResponseForbidden("No permission")

        profile_form = ProfileForm(request.POST, instance=profile_ext)
        avatar_form = AvatarForm(request.POST, request.FILES, instance=profile_user)

        if profile_form.is_valid() and avatar_form.is_valid():
            profile_form.save()
            avatar_form.save()
            return redirect("social:profile", username=username)
    else:
        profile_form = ProfileForm(instance=profile_ext)
        avatar_form = AvatarForm(instance=profile_user)

    return render(request, "social/profile.html", {
        "profile_user": profile_user,
        "profile_ext": profile_ext,
        "posts": posts,
        "is_owner": is_owner,
        "profile_form": profile_form,
        "avatar_form": avatar_form,

        # ✅ 给 base.html 顶栏用
        "login_in": request.session.get("login_in", False),
        "username": request.session.get("username", ""),
    })
from django.views.decorators.http import require_http_methods
from django.db import transaction
@require_http_methods(["GET", "POST"])
def post_create(request):
    # ✅ 必须登录（你现在用 session）
    if not request.session.get("login_in"):
        return HttpResponseForbidden("Please login")

    user_id = request.session.get("user_id")
    author = get_object_or_404(UserInfoModel, id=user_id)

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)

        # ✅ 诊断用：你可以先开着这三行提交一次，看是否真的收到文件
        print("FILES keys:", list(request.FILES.keys()))
        print("images count:", len(request.FILES.getlist("images")))
        print("POST keys:", list(request.POST.keys()))

        if form.is_valid():
            files = request.FILES.getlist("images")  # name="images" 必须对应你模板 input
            print("files:", files)

            # ✅ 最多 6 张（你 form.clean_images 已经验证，这里再兜底一次）
            files = files[:6]

            with transaction.atomic():
                # 1) 先存 Post
                post = form.save(commit=False)
                post.author = author
                post.save()

                # 2) 再存 PostImage
                for idx, f in enumerate(files):
                    PostImage.objects.create(post=post, image=f, order=idx)

            return redirect("social:profile", username=author.username)
    else:
        form = PostForm()
        print("form:", form)

    return render(request, "social/post_create.html", {"form": form})

def profile_edit(request):
    must = _require_login(request)
    if must:
        return must

    current_user = get_object_or_404(UserInfoModel, id=request.session.get("user_id"))
    profile_ext, _ = UserProfile.objects.get_or_create(user=current_user)

    if request.method == "GET":
        form = ProfileForm(instance=profile_ext)
        return render(request, "social/profile_edit.html", {"form": form})

    form = ProfileForm(request.POST, instance=profile_ext)
    if form.is_valid():
        form.save()
        return redirect("social:profile", username=current_user.username)

    return render(request, "social/profile_edit.html", {"form": form})
from django.views.decorators.http import require_POST
@require_POST
def post_delete(request, post_id):
    must = _require_login(request)
    if must:
        return must

    post = get_object_or_404(Post, id=post_id)

    # ✅ 只允许作者删除
    current_user_id = request.session.get("user_id")
    if not current_user_id or str(post.author_id) != str(current_user_id):
        return HttpResponseForbidden("No permission")

    username = post.author.username  # 删除前取一下
    post.delete()  # 如果 PostImage 外键 on_delete=CASCADE，会自动删图

    return redirect("social:profile", username=username)
# social/views.py
# social/views.py
import uuid
from urllib.parse import quote

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods

from spoken_ai.models import UserInfoModel
from .models import ForumRoom, ForumMessage

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.templatetags.static import static
from django.views.decorators.http import require_GET, require_POST

from .models import  UserProfile
from .forms import ProfileForm, AvatarForm


from .models import ForumRoom, LobbyMessage  # ✅ 加 LobbyMessage

def forum_home(request):
    login_in = request.session.get("login_in", False)
    username = request.session.get("username", "")

    # 房间创建/进入逻辑（保留）
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        if name:
            room, created = ForumRoom.objects.get_or_create(name=name)
            url = reverse("social:chat_room", kwargs={"slug": room.slug})
            if login_in and username:
                url += f"?username={username}"
            return redirect(url)

    rooms = ForumRoom.objects.order_by("-created_at")[:100]

    # ✅ 大厅消息：select_related 拿到 author（头像用得到）
    lobby_messages = (
        LobbyMessage.objects
        .select_related("author")
        .order_by("-created_at")[:30]
    )
    lobby_messages = list(reversed(lobby_messages))  # 页面从旧到新更自然

    return render(request, "social/forum_home.html", {
        "rooms": rooms,
        "login_in": login_in,
        "username": username,
        "lobby_messages": lobby_messages,
    })


@require_POST
def lobby_send(request):
    if not request.session.get("login_in"):
        return HttpResponseForbidden("Please login")

    text = (request.POST.get("text") or "").strip()
    if not text:
        return redirect("social:forum_home")
    if len(text) > 300:
        text = text[:300]

    user_id = request.session.get("user_id")
    session_username = request.session.get("username", "") or "anonymous"
    user = UserInfoModel.objects.filter(id=user_id).first() if user_id else None

    # ✅ author 存 FK；author_name 只是冗余（显示用/兜底）
    LobbyMessage.objects.create(
        author=user,
        author_name=(user.username if user else session_username),
        text=text
    )

    return redirect("social:forum_home")


@require_GET
def lobby_poll(request):
    after = request.GET.get("after")

    qs = LobbyMessage.objects.select_related("author").all()

    if after:
        try:
            after_id = int(after)
            qs = qs.filter(id__gt=after_id)
        except ValueError:
            pass

    qs = qs.order_by("created_at")[:50]

    messages = []
    for m in qs:
        # ✅ 更稳：优先 author.username（和 profile 路由一致）
        uname = (m.author.username if m.author else "") or (m.author_name or "anonymous")

        # ✅ 返回头像 url（给前端轮询渲染）
        avatar_url = ""
        if m.author and getattr(m.author, "avatar", None):
            try:
                avatar_url = m.author.avatar.url
            except Exception:
                avatar_url = ""

        messages.append({
            "id": m.id,
            "username": uname,
            "text": m.text,
            "created_at": m.created_at.strftime("%m-%d %H:%M"),
            "profile_url": reverse("social:profile", kwargs={"username": uname}),
            "avatar_url": avatar_url,  # ✅ 新增
        })

    return JsonResponse({"messages": messages})

@require_http_methods(["GET"])
def chat_room(request, slug):
    must = _require_login(request)
    if must:
        return must

    room = get_object_or_404(ForumRoom, slug=slug)

    # 最近 30 条（旧->新）
    msgs_qs = (ForumMessage.objects
               .filter(room=room)
               .select_related("author")
               .order_by("-created_at")[:30])
    msgs = list(reversed(list(msgs_qs)))

    return render(request, "social/chat_room.html", {
        "room": room,
        "messages": msgs,
        "username": request.session.get("username", ""),
        "login_in": request.session.get("login_in", False),
    })

@require_POST
def send_message(request, slug):
    must = _require_login(request)
    if must:
        return must

    room = get_object_or_404(ForumRoom, slug=slug)
    content = (request.POST.get("content") or "").strip()
    if not content:
        return HttpResponseBadRequest("Empty content")

    user_id = request.session.get("user_id")
    username = request.session.get("username", "unknown")

    author = UserInfoModel.objects.filter(id=user_id).first() if user_id else None

    msg = ForumMessage.objects.create(
        room=room,
        author=author,
        author_name=username,
        content=content[:500],
    )

    return JsonResponse({
        "ok": True,
        "id": msg.id,
        "created_at": msg.created_at.isoformat(),
    })


def poll_messages(request, slug):
    must = _require_login(request)
    if must:
        return must

    room = get_object_or_404(ForumRoom, slug=slug)
    since_id = request.GET.get("since_id")
    qs = ForumMessage.objects.filter(room=room).select_related("author")

    if since_id and since_id.isdigit():
        qs = qs.filter(id__gt=int(since_id))

    qs = qs.order_by("id")[:50]  # 每次最多返回 50 条

    data = []
    for m in qs:
        data.append({
            "id": m.id,
            "author": m.author_name or (m.author.username if m.author else "unknown"),
            "content": m.content,
            "created_at": m.created_at.strftime("%H:%M"),
        })

    return JsonResponse({"messages": data})


def _get_avatar_url(user: UserInfoModel) -> str:
    if not user:
        return static("img/default-avatar.png")
    try:
        if user.avatar:
            return user.avatar.url
    except Exception:
        pass
    return static("img/default-avatar.png")


def _get_profile_ext(user: UserInfoModel):
    if not user:
        return None
    ext = getattr(user, "profile_ext", None)
    if ext:
        return ext
    ext, _ = UserProfile.objects.get_or_create(user=user)
    return ext
@require_GET
def profile_card(request, username):
    u = get_object_or_404(UserInfoModel, username=username)
    ext = _get_profile_ext(u)

    return JsonResponse({
        "username": u.username,
        "nickname": ext.nickname if ext else "",
        "bio": ext.bio if ext else "",
        "avatar_url": _get_avatar_url(u),
    })
from .models import Post, PostImage, PostComment
from .forms import CommentForm
@require_http_methods(["GET", "POST"])
def post_detail(request, post_id: int):
    post = get_object_or_404(
        Post.objects.select_related("author").prefetch_related("images", "comments__author"),
        id=post_id
    )

    # 当前用户 & 权限
    current_user_id = request.session.get("user_id")
    is_login = bool(request.session.get("login_in"))
    is_owner = is_login and str(current_user_id) == str(post.author_id)

    if (not post.is_public) and (not is_owner):
        return HttpResponseForbidden("This post is not public.")

    # 评论列表
    comments = post.comments.all().select_related("author")

    # 提交评论
    if request.method == "POST":
        if not is_login:
            return HttpResponseForbidden("Please login")

        form = CommentForm(request.POST)
        if form.is_valid():
            user = UserInfoModel.objects.filter(id=current_user_id).first()
            c = form.save(commit=False)
            c.post = post
            c.author = user
            c.author_name = request.session.get("username", "") or (user.username if user else "unknown")
            c.save()
            return redirect("social:post_detail", post_id=post.id)
    else:
        form = CommentForm()

    return render(request, "social/post_detail.html", {
        "post": post,
        "comments": comments,
        "comment_form": form,
        "is_owner": is_owner,

        # 顶栏使用
        "login_in": request.session.get("login_in", False),
        "username": request.session.get("username", ""),
    })