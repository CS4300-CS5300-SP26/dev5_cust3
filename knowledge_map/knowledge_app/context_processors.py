from .models import UserProfile

def user_theme(request):
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return {'dark_mode': profile.dark_mode}
    return {'dark_mode': False}