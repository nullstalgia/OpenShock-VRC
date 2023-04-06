import asyncio
import websockets

ip1 = "dev.???.com:42420"
#ip1 = "192.168.86.220:8080"
ip2 = "192.168.86.22:8080"

async def forward_messages(source, destination):
    async for message in source:
        await destination.send(message)

async def connect_to_servers():
    async with websockets.connect(f'ws://{ip1}/') as server1, \
            websockets.connect(f'ws://{ip2}/ws') as server2:
        print('Connected to servers')
        await asyncio.gather(
            forward_messages(server1, server2),
            forward_messages(server2, server1),
        )

asyncio.run(connect_to_servers())