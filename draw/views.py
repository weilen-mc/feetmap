from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
import json
import base64
import io
import zipfile
import os
from PIL import Image
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
            outline = form.save(commit=False)
            outline.user = request.user
            outline.save()
            profile, created = UserProfile.objects.get_or_create(user=request.user)
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
                profile, created = UserProfile.objects.get_or_create(user=request.user)
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
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.favorite_colors = favorites
            profile.save()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    return JsonResponse({"success": False}, status=400)

@login_required
def gallery_view(request):
    drawings_query = Drawing.objects.filter(user=request.user).order_by('created_at')
    
    # Serialize drawings for the frontend Timelapse feature
    drawings_data = []
    for d in drawings_query:
        drawings_data.append({
            'id': d.id,
            'outline_id': d.outline.id,
            'outline_name': d.outline.name,
            'outline_url': d.outline.image.url,
            'url': d.image.url,
            'created_at': d.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    # Order by descending for the standard gallery view
    drawings = drawings_query.order_by('-created_at')
    
    return render(request, 'draw/gallery.html', {
        'drawings': drawings,
        'drawings_json': drawings_data
    })

@login_required
def bulk_delete_drawings(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            drawing_ids = data.get('drawing_ids', [])
            Drawing.objects.filter(id__in=drawing_ids, user=request.user).delete()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    return JsonResponse({"success": False}, status=400)

@login_required
def bulk_download_drawings(request):
    if request.method == 'POST':
        try:
            drawing_ids = request.POST.getlist('drawing_ids')
            if not drawing_ids:
                return HttpResponse("No drawings selected", status=400)
            
            drawings = Drawing.objects.filter(id__in=drawing_ids, user=request.user)
            
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w') as zf:
                for drawing in drawings:
                    # Process Drawing first to get target size
                    with drawing.image.open() as drawing_file:
                        with Image.open(drawing_file) as drawing_img:
                            drawing_img = drawing_img.convert("RGBA")
                            target_w, target_h = drawing_img.size
                            
                            # Create white background
                            composite = Image.new("RGBA", (target_w, target_h), (255, 255, 255, 255))
                            
                            # 1. Process Outline (Resize to match drawing exactly)
                            if drawing.outline and drawing.outline.image:
                                with drawing.outline.image.open() as outline_file:
                                    with Image.open(outline_file) as outline:
                                        outline = outline.convert("RGBA")
                                        # New: Resize outline to match the drawing resolution exactly
                                        # This works because they now share the same aspect ratio
                                        outline_resized = outline.resize((target_w, target_h), Image.Resampling.LANCZOS)
                                        composite.paste(outline_resized, (0, 0), outline_resized)
                            
                            # 2. Paste Drawing on top
                            composite.paste(drawing_img, (0, 0), drawing_img)
                    
                    # 3. Save to memory and then to zip
                    img_io = io.BytesIO()
                    composite.save(img_io, format='PNG')
                    img_io.seek(0)
                    
                    filename = os.path.basename(drawing.image.name)
                    zf.writestr(f"{drawing.id}_{filename}", img_io.read())
            
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="drawings.zip"'
            return response
        except Exception as e:
            return HttpResponse(f"Error creating zip: {e}", status=500)
    return HttpResponse("Invalid request", status=400)

@login_required
def update_user_settings(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            
            if 'last_color' in data:
                profile.last_color = data['last_color']
            if 'last_width' in data:
                profile.last_width = data['last_width']
            if 'last_opacity' in data:
                profile.last_opacity = data['last_opacity']
                
            profile.save()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    return JsonResponse({"success": False}, status=400)
