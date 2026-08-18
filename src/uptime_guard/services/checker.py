from starlette.requests import ClientDisconnect
import asyncio
from datetime import datetime, timezone
import time
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from uptime_guard.database import session_factory
from uptime_guard.models.check_log import CheckLog
from uptime_guard.models.target import Target
from uptime_guard.repositories.check_log import CheckLogRepository
from uptime_guard.repositories.target import TargetRepository


class CheckerService:
    def __init__(self, concurrency_limit: int = 50):
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        self.is_running = False

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

            log = CheckLog(
                target_id=target.id,
                status_code=status_code,
                response_time_ms=response_time_ms,
                is_success=is_success,
                error_message=error_message
            )  

            async with session_factory() as log_session:
                log_repo = CheckLogRepository(log_session)
                await log_repo.create(log)