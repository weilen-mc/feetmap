import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'feetmap.settings')
django.setup()

from django.template.loader import render_to_string
from django.contrib.auth.models import User
from draw.models import UserProfile

user, _ = User.objects.get_or_create(username='testuser')
profile, _ = UserProfile.objects.get_or_create(user=user)
profile.favorite_colors = ['#ff0000', '#00ff00']
profile.save()

class Req:
    def __init__(self, user):
        self.user = user

print(render_to_string('draw/index.html', {'request': Req(user), 'csrf_token': 'dummy'}))
