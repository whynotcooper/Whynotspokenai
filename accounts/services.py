from django.shortcuts import render

# Create your views here.
# accounts/services.py
from typing import Optional
from django.contrib.auth.hashers import check_password, make_password

from spoken_ai.models import UserInfoModel


SESSION_LOGIN_KEY = "login_in"
SESSION_USER_ID_KEY = "user_id"
SESSION_USERNAME_KEY = "username"


def get_me(request) -> Optional[UserInfoModel]:
    """从 session 取当前登录用户（你现在的登录模式）"""
    if not request.session.get(SESSION_LOGIN_KEY):
        return None
    uid = request.session.get(SESSION_USER_ID_KEY)
    if not uid:
        return None
    return UserInfoModel.objects.filter(id=uid).first()


def login_user(request, user: UserInfoModel):
    """写入 session"""
    request.session[SESSION_LOGIN_KEY] = True
    request.session[SESSION_USERNAME_KEY] = user.username
    request.session[SESSION_USER_ID_KEY] = user.id


def logout_user(request):
    """清 session（比 django logout 更适合你当前的自建登录）"""
    request.session.flush()


def verify_password(raw_password: str, stored_password: str) -> bool:
    """
    兼容：你现在数据库可能是明文密码；未来建议改成哈希。
    - 如果 stored_password 看起来是 Django hash，就用 check_password
    - 否则退回明文比较
    """
    if not stored_password:
        return False

    # Django hash 通常形如: pbkdf2_sha256$... 或 argon2$...
    if "$" in stored_password and len(stored_password.split("$")) >= 3:
        return check_password(raw_password, stored_password)

    return raw_password == stored_password


def hash_password(raw_password: str) -> str:
    """注册/改密时建议存哈希（后续再逐步淘汰明文）"""
    return make_password(raw_password)
