from django.urls import path
from ChitChat import views as chat_views

urlpatterns = [
    path('', chat_views.index_view, name='chat-index'),
    path('auth/login/', chat_views.login_user, name='login-user'),
    path('auth/logout/', chat_views.logout_user, name='logout-user'),
    path('register/', chat_views.register, name='register'),
    path('chat/<str:room_name>/', chat_views.chatPage, name='chatPage'),
    path('create-room/', chat_views.create_room, name='create-room'),
    path('join-room/<str:room_name>/', chat_views.join_room, name='join-room'),
    path('upload_media/',chat_views.upload_media,name='upload_media'),
]
