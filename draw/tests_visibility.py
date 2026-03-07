from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Outline, UserProfile

class OutlineVisibilityTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
        UserProfile.objects.create(user=self.user1)
        UserProfile.objects.create(user=self.user2)
        
        self.public_outline = Outline.objects.create(name='Public', visible_to_all=True)
        self.user1_outline = Outline.objects.create(name='User1 private', user=self.user1, visible_to_all=False)
        self.user2_outline = Outline.objects.create(name='User2 private', user=self.user2, visible_to_all=False)

    def test_user1_visibility(self):
        self.client.login(username='user1', password='password')
        from .context_processors import outlines_processor
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.user1)
        context = outlines_processor(request)
        outlines = context['all_outlines']
        
        outline_names = [o.name for o in outlines]
        self.assertIn('Public', outline_names)
        self.assertIn('User1 private', outline_names)
        self.assertNotIn('User2 private', outline_names)

    def test_user2_visibility(self):
        self.client.login(username='user2', password='password')
        from .context_processors import outlines_processor
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.user2)
        context = outlines_processor(request)
        outlines = context['all_outlines']
        
        outline_names = [o.name for o in outlines]
        self.assertIn('Public', outline_names)
        self.assertIn('User2 private', outline_names)
        self.assertNotIn('User1 private', outline_names)
