# accounts/views.py
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from spoken_ai.models import UserInfoModel
from .forms import LoginForm, RegisterForm
from .services import login_user, logout_user, verify_password, hash_password


@require_http_methods(["GET", "POST"])
def login_view(request):
    next_url = (request.POST.get("next") or request.GET.get("next") or "").strip()

    if request.method == "GET":
        form = LoginForm()
        return render(request, "accounts/login.html", {"form": form, "next": next_url})

    form = LoginForm(request.POST)
    if not form.is_valid():
        return render(request, "accounts/login.html", {"form": form, "next": next_url})

    login_id = form.cleaned_data["username"].strip()
    password = form.cleaned_data["password"]

    user = UserInfoModel.objects.filter(Q(username=login_id) | Q(phone=login_id)).first()
    if user and verify_password(password, user.password):
        login_user(request, user)

        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)

        return redirect("spoken_ai:index")

    messages.error(request, "用户名/手机号或密码不正确")
    return render(request, "accounts/login.html", {"form": form, "next": next_url})


from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods
from django.contrib import messages

@require_http_methods(["GET", "POST"])
def register_view(request):
    next_url = (request.POST.get("next") or request.GET.get("next") or "").strip()

    if request.method == "GET":
        form = RegisterForm()
        return render(request, "accounts/register.html", {"form": form, "next": next_url})

    form = RegisterForm(request.POST, request.FILES)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if not form.is_valid():
        # ✅ 关键：把错误打出来
        if is_ajax:
            print(form.errors)
            return JsonResponse({
                "code": 400,
                "message": "表单校验失败",
                "errors": form.errors,      # 字段级错误
                "non_field_errors": form.non_field_errors(),  # 非字段错误
            }, status=400)

        # 非 ajax：把错误显示在页面
        messages.error(request, "注册失败，请检查输入信息。")
        print(form.errors)
        return render(request, "accounts/register.html", {"form": form, "next": next_url})

    try:
        user = form.save(commit=False)
        user.password = hash_password(form.cleaned_data["password"])
        user.save()
    except Exception as e:
        # ✅ 关键：捕获保存时的 DB/文件错误（比如 unique 冲突、字段问题）
        if is_ajax:
            return JsonResponse({"code": 500, "message": f"保存失败：{str(e)}"}, status=500)
        messages.error(request, f"保存失败：{str(e)}")
        return render(request, "accounts/register.html", {"form": form, "next": next_url})

    login_user(request, user)

    safe_next = ""
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        safe_next = next_url

    if is_ajax:
        return JsonResponse({"code": 200, "message": "ok", "next": safe_next or ""})

    return redirect(safe_next or "spoken_ai:index")




def logout_view(request):
    logout_user(request)
    return render(request, "accounts/logout.html")



# accounts/views.py
from django.contrib import messages
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET", "POST"])
def password_reset_view(request):
    """
    占位版：当前 UserInfoModel 没有 email 字段时也能正常工作。
    后续你加 email + 邮件发送配置后，再升级到真正发邮件版（我下面也给了）。
    """
    email_sent = False

    if request.method == "POST":
        # 这里先不做真实发送，保持体验一致
        email_sent = True
        messages.success(request, "如果该邮箱已注册，我们已发送重置链接（演示版）。")

    return render(request, "accounts/password_reset.html", {
        "email_sent": email_sent,
    })
