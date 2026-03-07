from django.contrib import admin
from .models import Outline, UserProfile, Drawing

@admin.register(Outline)
class OutlineAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'visible_to_all')
    list_filter = ('visible_to_all', 'user')

admin.site.register(UserProfile)
admin.site.register(Drawing)
