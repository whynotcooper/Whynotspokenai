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
from .models import UserProfile, Post
from .forms import ProfileForm, AvatarForm


@require_http_methods(["GET", "POST"])
def profile(request, username):
    profile_user = get_object_or_404(UserInfoModel, username=username)
    profile_ext, _ = UserProfile.objects.get_or_create(user=profile_user)

    posts = Post.objects.filter(author=profile_user, is_public=True).prefetch_related("images")

    current_user_id = request.session.get("user_id")
    is_owner = bool(request.session.get("login_in")) and (str(current_user_id) == str(profile_user.id))

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
    })



def post_create(request):
    must = _require_login(request)
    if must:
        return must

    current_user = get_object_or_404(UserInfoModel, id=request.session.get("user_id"))

    if request.method == "GET":
        form = PostForm()
        return render(request, "social/post_create.html", {"form": form})

    # POST：创建帖子 + 多图
    form = PostForm(request.POST)
    images = request.FILES.getlist("images")  # <input multiple name="images">

    if not form.is_valid():
        return render(request, "social/post_create.html", {"form": form})

    post = form.save(commit=False)
    post.author = current_user
    post.save()

    for idx, f in enumerate(images):
        PostImage.objects.create(post=post, image=f, order=idx)

    return redirect("social:profile", username=current_user.username)


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


def _require_login(request):
    """
    未登录则跳转到登录页，并携带 next=当前完整路径（含 querystring）
    """
    if not request.session.get("login_in"):
        next_url = quote(request.get_full_path())  # ✅ 比 request.path 更完整
        login_url = reverse("spoken_ai:login")     # ✅ 不要硬编码 /login/
        return redirect(f"{login_url}?next={next_url}")
    return None


@require_http_methods(["GET", "POST"])
def forum_home(request):
    must = _require_login(request)
    if must:
        return must

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        if name:
            room, _ = ForumRoom.objects.get_or_create(name=name)

            # ✅ 兜底：如果历史数据 slug 为空，补一个
            if not room.slug:
                room.slug = uuid.uuid4().hex[:12]
                room.save(update_fields=["slug"])

            return redirect("social:chat_room", slug=room.slug)

    rooms = ForumRoom.objects.all().order_by("-created_at")[:50]

    return render(request, "social/forum_home.html", {
        "rooms": rooms,
        # ✅ 给模板/页面用（也方便你聊天室显示用户名）
        "username": request.session.get("username", ""),
        "login_in": request.session.get("login_in", False),
    })


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