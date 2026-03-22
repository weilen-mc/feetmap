from django.db import models
from django.contrib.auth.models import User

class Outline(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='outlines/')
    visible_to_all = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    selected_outline = models.ForeignKey(Outline, on_delete=models.SET_NULL, null=True, blank=True)
    favorite_colors = models.JSONField(default=list, blank=True)
    
    # Persistent drawing settings
    last_color = models.CharField(max_length=7, default="#ff0000")
    last_width = models.IntegerField(default=15)
    last_opacity = models.IntegerField(default=15)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Drawing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    outline = models.ForeignKey(Outline, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='drawings/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        d_name = self.name if self.name else f"Drawing on {self.outline.name}"
        return f"{d_name} by {self.user.username} at {self.created_at}"
