import aiohttp
import asyncio
from utils.logging_utils import logger

async def send_mail_notification(request_url: str, max_retries: int = 3):
    url = "https://alphamail.site/api/v1/auth/mail"
    payload = {"url": request_url}

    for attempt in range(1, max_retries + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"[메일 전송 성공] {await response.text()}")
                        return
                    elif response.status == 409:
                        logger.warning(f"[메일 전송 실패 - 409] {await response.text()}")
                        return
                    else:
                        logger.warning(f"[예상치 못한 응답] status={response.status}, body={await response.text()}")
        except Exception as e:
            logger.error(f"[메일 전송 예외 - 시도 {attempt}] {e}")
        
        logger.info(f"[재시도 대기] {attempt}번째 실패, 2초 후 재시도")
        await asyncio.sleep(2)
    
    logger.error(f"[메일 전송 실패] 최대 재시도({max_retries}) 후에도 실패함")