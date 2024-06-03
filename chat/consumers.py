import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from django.template.loader import render_to_string
from django.conf import settings
from openai import OpenAI, AsyncOpenAI
from .models import ChatSession, Message, User
from asgiref.sync import sync_to_async

import redis

# Setup Redis connection
r = redis.Redis(host='localhost', port=6379, db=0)

def get_sender_username_and_content(msg):
    # This function extracts the username from the message sender
    username = msg.sender.username if msg.sender else "AI"
    content = msg.content
    return username, content

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.user = self.scope["user"]
        self.messages = await self.load_history()
        await self.accept()

        for message in self.messages:
            await self.send(text_data=json.dumps({"message": message['content'], "username": message['username']}))
    async def disconnect(self, close_code):
        # Cleanup if necessary
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_text = text_data_json["message"]
        
        # Store and display user message
        await self.store_and_send_message(message_text, self.user)

        # Generate and display AI response
        response_text = await self.chat_with_openai(message_text)
        await self.store_and_send_message(response_text, None)  # Assuming AI messages have no user associated

    async def chat_with_openai(self, user_message):
        # Append the new user message with role 'user'
        self.messages.append({"role": "user", "content": user_message})
        if len(self.messages) > 50:
            self.messages.pop(0)  # Remove the oldest message if more than 50

        # Call OpenAI API with the last 50 messages
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        openai_response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=self.messages[-50:],  # Send only the last 50 messages
            max_tokens=150
        )
        
        # Append AI's response with role 'assistant'
        ai_content = openai_response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": ai_content})

        return ai_content

    async def load_history(self):
        # Redis key for session
        redis_key = f'chat_history_{self.session_id}'

        # Fetch last 50 messages from Redis
        messages = await sync_to_async(r.lrange)(redis_key, -50, -1)  # Get last 50 messages
        if not messages:
            # If Redis is empty, load from DB and store in Redis
            db_messages = await sync_to_async(list)(Message.objects.filter(session_id=self.session_id).order_by('-timestamp')[:50])
            db_messages.reverse()  # Reverse to maintain the chronological order after slicing
            messages = []
            for msg in db_messages:
                sender_username, content = await sync_to_async(get_sender_username_and_content)(msg) 
                role = "assistant" if sender_username == "AI" else "user"
                message_data = json.dumps({"role": role, "username": sender_username, "content": content})
                await sync_to_async(r.rpush)(redis_key, message_data)
                messages.append(message_data)

        # Ensure that the Redis list does not exceed 50 messages
        await sync_to_async(r.ltrim)(redis_key, -50, -1)

        return [json.loads(msg) for msg in messages]



    async def store_and_send_message(self, message_text, user):
        # Fetch the AI user if user is None
        if not user:
            user = await sync_to_async(User.objects.get)(username='AI')  # Assume 'AI' is the username of the system user
        
        # Store in Redis and PostgreSQL
        session = await sync_to_async(ChatSession.objects.get)(id=self.session_id)
        message = await sync_to_async(Message.objects.create)(session=session, sender=user, content=message_text)
        role = "assistant" if user == "AI" else "user"
        await sync_to_async(r.rpush)(f'chat_history_{self.session_id}', json.dumps({"role": role, "username": user.username, "content": message_text}))
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message_text, "username": user.username}))