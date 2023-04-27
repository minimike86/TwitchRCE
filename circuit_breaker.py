import asyncio


class CircuitBreaker:
    def __init__(self, max_failures: int, reset_timeout: int):
        self.max_failures: int = max_failures  # maximum number of failures allowed
        self.reset_timeout: int = reset_timeout  # time the circuit breaker remains open before attempting to reset
        self.current_failures = 0
        self.opened_since = None

    async def execute(self, coro_func):
        if self.current_failures >= self.max_failures:
            time_since_opened = asyncio.get_event_loop().time() - self.opened_since
            if time_since_opened > self.reset_timeout:
                self.current_failures = 0
            else:
                raise CircuitBreakerOpenError()

        try:
            result = await coro_func()
            self.current_failures = 0
            return result
        except Exception:
            self.current_failures += 1
            if self.current_failures == 1:
                self.opened_since = asyncio.get_event_loop().time()
            raise


class CircuitBreakerOpenError(Exception):
    pass
