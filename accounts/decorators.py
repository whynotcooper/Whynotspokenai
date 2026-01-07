# accounts/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse

from .services import get_me


def session_login_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        me = get_me(request)
        if not me:
            # 让用户登录后回跳
            login_url = reverse("accounts:login")
            return redirect(f"{login_url}?next={request.get_full_path()}")
        return view_func(request, *args, **kwargs)
    return _wrapped
