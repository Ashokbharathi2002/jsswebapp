from .models import Note, Notice

def user_notes(request):
    """
    Context processor to make the logged-in user's notes available in all templates.
    """
    if request.user.is_authenticated:
        return {
            'user_notes': Note.objects.filter(user=request.user).order_by('-updated_at')
        }
    return {
        'user_notes': []
    }

def active_notices(request):
    """
    Context processor to make active notices available globally in all templates.
    """
    return {
        'active_notices': Notice.objects.filter(is_active=True).order_by('-created_at')
    }

