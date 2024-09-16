import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message, Room
from asgiref.sync import sync_to_async
from datetime import datetime, timedelta
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"

        # Retrieve the room instance
        self.room = await database_sync_to_async(Room.objects.get)(name=self.room_name)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        previous_messages = await self.get_previous_messages()

        await self.send(text_data=json.dumps({
            'messages': previous_messages
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', None)
        media_url = text_data_json.get('media_url', None)
        username = self.scope['user'].username
        timestamp = datetime.now().isoformat()

        if message or media_url:
            media_file = media_url if media_url else None

            await self.save_message(
                user=self.scope['user'],
                room=self.room,
                message=message,
                media_file=media_file,
                timestamp=timestamp
            )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'media_url': media_url,
                'username': username,
                'time': timestamp,
                'is_read': False
            }
        )

    async def chat_message(self, event):
        message = event.get('message', '')
        media_url = event.get('media_url', '')
        username = event['username']
        time = event['time']

        await self.send(text_data=json.dumps({
            'username': username,
            'message': message,
            'media_url': media_url,
            'time': time,
        }))

    @database_sync_to_async
    def save_message(self, user, room, message, media_file, timestamp):
        """Save the message to the database."""
        Message.objects.create(
            user=user,
            room=room,
            content=message,
            media_file=media_file,
            timestamp=timestamp
        )

    @database_sync_to_async
    def get_previous_messages(self):
        messages = Message.objects.filter(room=self.room).order_by('timestamp').values(
            'user__username', 'content', 'timestamp', 'is_read', 'media_file'
        )

        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        formatted_messages = []
        previous_day_label = None  # To track the last day label added

        for msg in messages:
            msg_date = msg['timestamp'].date()

            if msg_date == today:
                day_label = "Today"
            elif msg_date == yesterday:
                day_label = "Yesterday"
            else:
                day_label = msg_date.strftime('%d %B, %Y')

            # Add the day label only if it's different from the previous one
            if day_label != previous_day_label:
                formatted_messages.append({'day_label': day_label})
                previous_day_label = day_label

            formatted_message = {
                'username': msg['user__username'],
                'message': msg['content'],
                'media_url': msg['media_file'] if msg['media_file'] else '',
                'time': msg['timestamp'].strftime('%H:%M'),  # Display only time
                'is_read': msg['is_read']
            }

            formatted_messages.append(formatted_message)

        self.mark_messages_as_read()

        return formatted_messages


    @database_sync_to_async
    def mark_messages_as_read(self):
        """Mark unread messages as read for the current user."""
        Message.objects.filter(
            room=self.room,
            is_read=False,
            user__username=self.scope["user"].username
        ).update(is_read=True)
