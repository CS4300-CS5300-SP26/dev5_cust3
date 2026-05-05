# from .models import UserProfile


def user_theme(request):
    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        if profile is None:
            return {"dark_mode": False}
        return {"dark_mode": profile.dark_mode}
    return {"dark_mode": False}
