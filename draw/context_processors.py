from .models import Outline

def outlines_processor(request):
    if request.user.is_authenticated:
        from django.db.models import Q
        outlines = Outline.objects.filter(Q(visible_to_all=True) | Q(user=request.user))
        selected_outline = request.user.userprofile.selected_outline if hasattr(request.user, 'userprofile') else None
        return {'all_outlines': outlines, 'selected_outline': selected_outline}
    return {}
