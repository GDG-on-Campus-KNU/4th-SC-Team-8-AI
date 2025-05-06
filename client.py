import asyncio
import websockets
import json

async def client():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        print(f"서버에 연결됨: {uri}")
        
        # 수신용 태스크: 서버에서 보내오는 메시지가 있으면 출력
        async def receive():
            async for msg in websocket:
                print(f"[서버 → 클라이언트] {msg}")

        # 전송용 태스크: 사용자 입력을 JSON으로 전송
        async def send():
            while True:
                line = await asyncio.to_thread(input, "보낼 JSON 입력> ")
                line = line.strip()
                if not line:
                    continue
                try:
                    # JSON 형식이 맞는지 확인
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    print("❌ 유효한 JSON이 아닙니다.")
                    continue
                await websocket.send(json.dumps(obj))
                print("✅ 전송 완료")

        # receive, send 두 태스크 동시 실행
        await asyncio.gather(receive(), send())

if __name__ == "__main__":
    try:
        asyncio.run(client())
    except KeyboardInterrupt:
        print("\n클라이언트 종료")  
