from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_outline, name='upload_outline'),
    path('select_outline/', views.select_outline, name='select_outline'),
    path('save_drawing/', views.save_drawing, name='save_drawing'),
    path('save_favorites/', views.save_favorites, name='save_favorites'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
