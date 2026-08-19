import uuid
import asyncio
import time
import httpx

from telegram import Bot
from telegram.error import TelegramError

from uptime_guard.config import settings
from uptime_guard.database import session_factory, redis_client
from uptime_guard.models.check_log import CheckLog
from uptime_guard.models.target import Target
from uptime_guard.repositories.check_log import CheckLogRepository
from uptime_guard.repositories.target import TargetRepository


class CheckerService:
    def __init__(self, concurrency_limit: int = 50):
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        self.is_running = False
        self.bot = Bot(token=settings.telegram_bot_token)

    async def start(self) -> None:
        self.is_running = True
    
        async with httpx.AsyncClient(follow_redirects=True) as client:
            while self.is_running:
                try:
                    await self._run_check_cycle(client)
                except Exception as e:
                    print(f"CRASH in checker: {e}")
                    import traceback
                    traceback.print_exc()
                await asyncio.sleep(10)

    async def stop(self) -> None:
        self.is_running = False

    async def _run_check_cycle(self, client: httpx.AsyncClient) -> None:
        async with session_factory() as session:
            target_repo = TargetRepository(session)
            targets = await target_repo.get_active_targets()

        tasks = [self._check_single_target(target, client) for target in targets]
        await asyncio.gather(*tasks)

    async def _check_single_target(
        self, target: Target, client: httpx.AsyncClient
    ) -> None:
        async with self.semaphore:
            start_time = time.perf_counter()
            status_code = None
            is_success = False
            error_message = None

            try:
                response = await client.request(target.method, target.url, timeout=target.timeout)
                status_code = response.status_code
                is_success = (status_code == target.expected_status)

            except httpx.RequestError as e:
                error_message = str(e)

            response_time_ms = (time.perf_counter() - start_time) * 1000

            status_emoji = "UP" if is_success else "DOWN"
            code_text = status_code if status_code else "ERROR"
            print(f"[{status_emoji}] {target.url} | Code: {code_text} | Time: {response_time_ms:.0f}ms")

            # Логика алертов
            previous_status_str = await redis_client.get(f"status:{target.id}")
            previous_status = (previous_status_str == "1") if previous_status_str is not None else None
            
            if previous_status is not None and previous_status != is_success:
                await self._send_notification(target, is_success, status_code, error_message)
            elif previous_status is None and not is_success:
                await self._send_notification(target, is_success, status_code, error_message)

            # Обновление Redis
            await redis_client.set(f"status:{target.id}", "1" if is_success else "0")
            await redis_client.incr(f"stats:total:{target.id}")
            if is_success:
                await redis_client.incr(f"stats:success:{target.id}")
            await redis_client.set(f"stats:last_ping:{target.id}", int(response_time_ms))

            log = CheckLog(
                target_id=target.id,
                status_code=status_code,
                response_time_ms=response_time_ms,
                is_success=is_success,
                error_message=error_message
            )  

            from sqlalchemy.exc import IntegrityError
            
            async with session_factory() as log_session:
                log_repo = CheckLogRepository(log_session)
                try:
                    await log_repo.create(log)
                except IntegrityError:
                    await redis_client.delete(
                        f"status:{target.id}", 
                        f"stats:total:{target.id}", 
                        f"stats:success:{target.id}", 
                        f"stats:last_ping:{target.id}"
                    )

    async def _send_notification(self, target: Target, is_success: bool, status_code: int | None, error_message: str | None) -> None:
        if not target.user or not target.user.telegram_id:
            return

        if is_success:
            text = f"Сайт восстановлен!*\n\n🔗 {target.url}\nКод: {status_code}"
        else:
            reason = f"Код {status_code}" if status_code else error_message
            text = f"САЙТ УПАЛ!*\n\n🔗 {target.url}\nПричина: {reason}"

        try:
            await self.bot.send_message(chat_id=target.user.telegram_id, text=text, parse_mode="Markdown")
        except TelegramError as e:
            print(f"Failed to send alert to {target.user.telegram_id}: {e}")