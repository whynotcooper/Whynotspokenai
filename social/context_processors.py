# social/context_processors.py

def auth_context(request):
    """
    给所有模板提供 login_in / username
    """
    return {
        "login_in": request.session.get("login_in", False),
        "username": request.session.get("username", ""),
    }
