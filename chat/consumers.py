import json
from channels.generic.websocket import AsyncWebsocketConsumer
import redis
from django.conf import settings
from openai import OpenAI, AsyncOpenAI

r = redis.Redis(host='localhost', port=6379, db=0)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        # Clean up action, if any
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # Process message through OpenAI
        response = await self.chat_with_openai(message)

        # Send both the user message and AI response
        await self.send(text_data=json.dumps({"message": message, "username": "You"}))
        await self.send(text_data=json.dumps({"message": response, "username": "AI"}))

    async def chat_with_openai(self, message):
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        print("tejas", message)
        previous_messages = [
            {
                "role": "system",
                "content": """you are a layer ai. answer like shakespear for fun though."""
            },
            {
            "role": "user",
            "content": f"""Generate a response to the following message: {message}"""
            }
        ]

        openai_response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=previous_messages,
        )
        return openai_response.choices[0].message.content