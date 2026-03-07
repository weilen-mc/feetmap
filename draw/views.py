from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
import base64
from django.core.files.base import ContentFile
from .forms import UserRegistrationForm, OutlineUploadForm
from .models import UserProfile, Outline, Drawing

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            UserProfile.objects.get_or_create(user=user)
            login(request, user)
            return redirect('index')
    else:
        form = UserRegistrationForm()
    return render(request, 'draw/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'draw/login.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    logout(request)
    return redirect('login')

@login_required
def index(request):
    return render(request, 'draw/index.html')

@login_required
def upload_outline(request):
    if request.method == 'POST':
        form = OutlineUploadForm(request.POST, request.FILES)
        if form.is_valid():
            outline = form.save()
            profile = request.user.userprofile
            profile.selected_outline = outline
            profile.save()
            return redirect('index')
    else:
        form = OutlineUploadForm()
    return render(request, 'draw/upload.html', {'form': form})

@login_required
def select_outline(request):
    if request.method == 'POST':
        outline_id = request.POST.get('outline_id')
        if outline_id:
            try:
                outline = Outline.objects.get(id=outline_id)
                profile = request.user.userprofile
                profile.selected_outline = outline
                profile.save()
            except Outline.DoesNotExist:
                pass
    return redirect('index')

@login_required
def save_drawing(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data.get('image_data')
            outline_id = data.get('outline_id')
            
            if image_data and outline_id:
                format_str, imgstr = image_data.split(';base64,')
                ext = format_str.split('/')[-1]
                
                outline = Outline.objects.get(id=outline_id)
                drawing = Drawing(user=request.user, outline=outline)
                
                import time
                filename = f"drawing_{request.user.id}_{outline.id}_{int(time.time())}.{ext}"
                drawing.image.save(filename, ContentFile(base64.b64decode(imgstr)), save=True)
                
                return JsonResponse({"success": True})
        except Exception as e:
            print(f"Error saving drawing: {e}")
            return JsonResponse({"success": False, "error": str(e)}, status=400)
            
    return JsonResponse({"success": False}, status=400)

@login_required
def save_favorites(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            favorites = data.get('favorites', [])
            profile = request.user.userprofile
            profile.favorite_colors = favorites
            profile.save()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    return JsonResponse({"success": False}, status=400)

@login_required
def gallery_view(request):
    drawings = Drawing.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'draw/gallery.html', {'drawings': drawings})
