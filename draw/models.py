from django.db import models
from django.contrib.auth.models import User

class Outline(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='outlines/')

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    selected_outline = models.ForeignKey(Outline, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Drawing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    outline = models.ForeignKey(Outline, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='drawings/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Drawing by {self.user.username} on {self.outline.name} at {self.created_at}"
