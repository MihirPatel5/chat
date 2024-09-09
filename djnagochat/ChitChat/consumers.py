import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message, Room, User
from asgiref.sync import sync_to_async
from datetime import datetime, timedelta

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"

        await self.accept()
        self.room = await sync_to_async(Room.objects.get)(name=self.room_name)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        messages = await self.get_previous_messages()
        await self.send(text_data=json.dumps({
            'messages': messages
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = text_data_json['username']
        time = text_data_json['time']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_message',
                'message': message,
                'username': username,
                'time': time,
            }
        )

        if username == self.scope["user"].username:
            user = await sync_to_async(User.objects.get)(username=username)
            await sync_to_async(Message.objects.create)(
                room=self.room,
                user=user,
                content=message,
                is_read=False 
            )

    async def send_message(self, event):
        message = event['message']
        username = event['username']
        time = event['time']

        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'time': time,
        }))

    async def get_previous_messages(self):
        messages = await sync_to_async(
            list
        )(Message.objects.filter(room=self.room).order_by('timestamp').values('user__username', 'content', 'timestamp', 'is_read'))

        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        formatted_messages = []
        unread_messages = []

        for msg in messages:
            msg_date = msg['timestamp'].date()

            if msg_date == today:
                day_label = "Today"
            elif msg_date == yesterday:
                day_label = "Yesterday"
            else:
                day_label = msg_date.strftime('%d %B, %Y')

            formatted_message = {
                'username': msg['user__username'],
                'message': msg['content'],
                'time': msg['timestamp'].isoformat(),
                'day_label': day_label,
                'is_read': msg['is_read']
            }

            if not msg['is_read'] and msg['user__username'] != self.scope["user"].username:
                unread_messages.append(formatted_message)
            else:
                formatted_messages.append(formatted_message)

        return unread_messages + formatted_messages

    async def mark_messages_as_read(self):
        user = self.scope["user"]
        await sync_to_async(Message.objects.filter(room=self.room, user__username=user.username, is_read=False).update)(is_read=True)


