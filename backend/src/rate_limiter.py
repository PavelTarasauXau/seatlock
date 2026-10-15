from redis.asyncio import Redis
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimiterMiddleware(BaseHTTPMiddleware):

    def __init__(self, app, limit: int = 5, window: int = 10):
        super().__init__(app)
        self.limit = limit
        self.window = window
