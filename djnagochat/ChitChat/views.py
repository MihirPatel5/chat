from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, SignupForm
from .models import Room, Message
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@login_required
def chatPage(request, room_name):
    room, created = Room.objects.get_or_create(name=room_name)
    if request.user not in room.users.all():
        return redirect('join-room', room_name=room_name)
    return render(request, 'chat/chatPage.html', {'room': room})


@login_required
def create_room(request):
    rooms = Room.objects.all()
    if request.method == 'POST':
        room_name = request.POST['room_name']
        room, created = Room.objects.get_or_create(name=room_name)
        return redirect('chatPage', room_name=room.name)
    return render(request, 'chat/create_room.html', {'rooms': rooms})


@login_required
def join_room(request, room_name):
    room = get_object_or_404(Room, name=room_name)
    if room:
        room.users.add(request.user)
        return redirect('chatPage', room_name=room_name)
    return redirect('chat-index')


@login_required
def index_view(request):
    rooms = Room.objects.all()
    return render(request, 'chat/room_list.html', {'rooms': rooms})


def register(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login-user')
    else:
        form = SignupForm()
    return render(request, 'chat/register.html', {'form': form})


def login_user(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect('create-room')
    else:
        form = LoginForm()
    return render(request, 'chat/loginpage.html', {'form': form})


def logout_user(request):
    logout(request)
    return redirect('login-user')


@csrf_exempt
def upload_media(request):
    if request.method == 'POST':
        media_file = request.FILES.get('media', None)
        room_name = request.POST.get('room')
        room = get_object_or_404(Room, name=room_name)
        
        message = Message.objects.create(
            media_file=media_file,
            room=room,
            user=request.user,
            content=request.POST.get('message', '') 
        )

        if media_file: 
            return JsonResponse({'media_url': message.media_file.url})
        return JsonResponse({'message': message.content})  


@csrf_exempt
def upload_audio(request):
    if request.method == 'POST' and request.FILES.get('audio'):
        audio_file = request.FILES['audio']
        room_name = request.POST.get('room')
        room = get_object_or_404(Room, name=room_name)

        message = Message.objects.create(
            media_file=audio_file,
            room=room,
            user=request.user,
            content=''  
        )

        return JsonResponse({'audio_url': message.media_file.url})
    return JsonResponse({'error': 'Invalid request'}, status=400)
