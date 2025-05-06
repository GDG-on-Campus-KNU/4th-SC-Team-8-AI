import asyncio
import websockets
import json

clients = set()

async def send(socket, data):
    await socket.send(data)

async def recieve(socket):
    clients.add(socket)
    async for message in socket:
        landmarks = json.loads(message)
        print(landmarks["multiHandLandmarks"])
        print(landmarks["multiHandWorldLandmarks"])
        print(landmarks["multiHandedness"])

async def handle_input():
    while True:
        score = await asyncio.to_thread(input, "Enter score: ")
        if clients:
            await asyncio.gather(*[send(socket, score) for socket in clients])
        else:
            print("No clients connected.")

async def main():
    async with websockets.serve(recieve, "localhost", 8765) as server:
        print("WebSocket server started at ws://localhost:8765")
        await handle_input()

if __name__ == "__main__":
    asyncio.run(main())