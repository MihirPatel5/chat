from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, SignupForm
from .models import Room
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from asgiref.sync import sync_to_async

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
    room = Room.objects.get(name=room_name)
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
