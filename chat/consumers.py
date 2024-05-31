import json
from channels.generic.websocket import AsyncWebsocketConsumer
import redis

r = redis.Redis(host='localhost', port=6379, db=0)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.roomGroupName = "group_chat_gfg"
        await self.channel_layer.group_add(
            self.roomGroupName,
            self.channel_name
        )
        await self.accept()
        # Load chat history from Redis
        await self.load_chat_history()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.roomGroupName,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        username = text_data_json["username"]

        # Store message in Redis
        r.rpush(f'chat_{self.roomGroupName}', json.dumps({"message": message, "username": username}))

        await self.channel_layer.group_send(
            self.roomGroupName, {
                "type": "sendMessage",
                "message": message,
                "username": username,
            })

    async def sendMessage(self, event):
        message = event["message"]
        username = event["username"]
        await self.send(text_data=json.dumps({"message": message, "username": username}))

    async def load_chat_history(self):
        # Load the last 50 messages from Redis
        chat_history = r.lrange(f'chat_{self.roomGroupName}', -50, -1)
        for message in chat_history:
            message_data = json.loads(message)
            await self.send(text_data=json.dumps({"message": message_data["message"], "username": message_data["username"]}))
