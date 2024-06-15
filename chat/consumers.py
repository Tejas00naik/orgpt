import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from openai import AsyncOpenAI
from .models import ChatSession, Message, User
from asgiref.sync import sync_to_async
import redis

# Setup Redis connection
r = redis.Redis(host='localhost', port=6379, db=0)

def get_sender_username_and_content(msg):
    #This function extracts the username from the message sender
    username = msg.sender.username if msg.sender else "AI"
    content = msg.content
    return username, content

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.user = self.scope["user"]
        self.message_offset = 10 # Initialize message offset
        self.messages = await self.load_history()
        await self.accept()
        print("initially loaded msgs", self.messages, len(self.messages))

        print(type(self.messages))
        pass_to_ui = self.messages[:10]
        pass_to_ui = pass_to_ui[::-1]
        for message in pass_to_ui:
            await self.send(text_data=json.dumps({"message": message['content'], "username": message['username']}))
    async def disconnect(self, close_code):
        #add posgress synching logic here
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('command') == 'fetch_more':
            more_messages = await self.fetch_more_messages()
            print("new messages", more_messages, len(more_messages))
            # This line is where the "sending more messages" happens
            await self.send(text_data=json.dumps({"messages": more_messages}))
        else:
            message_text = data["message"]
            await self.store_and_send_message(message_text, self.user)
            response_text = await self.chat_with_openai(message_text)
            await self.store_and_send_message(response_text, None)


    async def fetch_more_messages(self):
        redis_key = f'chat_history_{self.session_id}'
        start = self.message_offset
        end = start + 5
        
        # Get messages from Redis, ensure they are properly deserialized
        more_messages = await sync_to_async(r.lrange)(redis_key, start, end)
        more_messages = [json.loads(msg.decode('utf-8')) for msg in more_messages]  # Ensure messages are decoded and loaded correctly

        if not more_messages:
            # Load from DB if not in Redis
            db_messages = await sync_to_async(list)(Message.objects.filter(session_id=self.session_id).order_by('-timestamp')[start:end])
            for msg in db_messages:
                sender_username, content = await sync_to_async(get_sender_username_and_content)(msg)
                role = "assistant" if sender_username == "AI" else "user"
                message_data = {"role": role, "username": sender_username, "content": content}
                more_messages.append(message_data)
                # Store newly fetched messages back into Redis
                await sync_to_async(r.lpush)(redis_key, json.dumps(message_data))

        self.message_offset += 6  # Increment offset by 5 each time
        return more_messages

    async def chat_with_openai(self, user_message):
        print(self.messages)
        self.messages.append({"role": "user", "content": user_message})
        if len(self.messages) > 50:
            self.messages.pop(0)
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        openai_response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=self.messages[-50:],
            max_tokens=150
        )
        ai_content = openai_response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": ai_content})
        return ai_content

    async def load_history(self):
        redis_key = f'chat_history_{self.session_id}'
        messages = await sync_to_async(r.lrange)(redis_key, 0, 49)

        if not messages:
            db_messages = await sync_to_async(list)(Message.objects.filter(session_id=self.session_id).order_by('-timestamp')[:50])
            messages = []
            for msg in db_messages:
                sender_username, content = await sync_to_async(get_sender_username_and_content)(msg) 
                role = "assistant" if sender_username == "AI" else "user"
                message_data = json.dumps({"role": role, "username": sender_username, "content": content})
                await sync_to_async(r.rpush)(redis_key, message_data)
                messages.append(message_data)
        await sync_to_async(r.ltrim)(redis_key, -50, -1)
        return [json.loads(msg) for msg in messages]

    async def store_and_send_message(self, message_text, user):
        if not user:
            user = await sync_to_async(User.objects.get)(username='AI')
        session = await sync_to_async(ChatSession.objects.get)(id=self.session_id)
        message = await sync_to_async(Message.objects.create)(session=session, sender=user, content=message_text)
        role = "assistant" if user == "AI" else "user"
        await sync_to_async(r.lpush)(f'chat_history_{self.session_id}', json.dumps({"role": role, "username": user.username, "content": message_text}))
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message_text, "username": user.username}))