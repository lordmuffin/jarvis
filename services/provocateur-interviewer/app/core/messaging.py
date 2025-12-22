import os
import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError

class MessagingService:
    def __init__(self):
        self.url = os.getenv("NATS_URL", "nats://nats:4222")
        self.nc = None

    async def connect(self):
        try:
            self.nc = await nats.connect(self.url)
            print(f"Connected to NATS at {self.url}")
        except (NoServersError, TimeoutError) as e:
            print(f"Failed to connect to NATS: {e}")

    async def publish(self, subject: str, payload: bytes):
        if not self.nc:
            await self.connect()
        if self.nc:
            await self.nc.publish(subject, payload)
            # await self.nc.flush() 

    async def close(self):
        if self.nc:
            await self.nc.close()

    async def subscribe(self, subject: str, cb):
        if not self.nc:
            await self.connect()
        if self.nc:
            await self.nc.subscribe(subject, cb=cb)
