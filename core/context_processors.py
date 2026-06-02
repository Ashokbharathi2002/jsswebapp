from .models import Note

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
