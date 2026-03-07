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
                    # Target size for compositing
                    target_w, target_h = 800, 600
                    
                    # Create white background
                    composite = Image.new("RGBA", (target_w, target_h), (255, 255, 255, 255))
                    
                    # 1. Process Outline (Low Opacity, Contain aspect ratio)
                    if drawing.outline and drawing.outline.image:
                        outline_path = drawing.outline.image.path
                        with Image.open(outline_path) as outline:
                            outline = outline.convert("RGBA")
                            
                            # Aspect ratio calculations (Contain)
                            img_w, img_h = outline.size
                            img_aspect = img_w / img_h
                            target_aspect = target_w / target_h
                            
                            if img_aspect > target_aspect:
                                draw_w = target_w
                                draw_h = int(target_w / img_aspect)
                                x = 0
                                y = (target_h - draw_h) // 2
                            else:
                                draw_h = target_h
                                draw_w = int(target_h * img_aspect)
                                x = (target_w - draw_w) // 2
                                y = 0
                            
                            outline_resized = outline.resize((draw_w, draw_h), Image.Resampling.LANCZOS)
                            
                            composite.paste(outline_resized, (x, y), outline_resized)
                    
                    # 2. Process Drawing
                    with Image.open(drawing.image.path) as drawing_img:
                        drawing_img = drawing_img.convert("RGBA")
                        # Paste drawing on top (it's already 800x600)
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
