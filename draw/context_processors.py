from .models import Outline

def outlines_processor(request):
    if request.user.is_authenticated:
        outlines = Outline.objects.all()
        selected_outline = request.user.userprofile.selected_outline if hasattr(request.user, 'userprofile') else None
        return {'all_outlines': outlines, 'selected_outline': selected_outline}
    return {}
