from src.exceptions import TooManyRequestsError
from src.redis_client import redis

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 15 * 60


def _key(email: str) -> str:
    return f"login_fail:{email.lower()}"


async def ensure_login_allowed(email: str) -> None:
    attempts = await redis.get(_key(email))
    if attempts is not None and int(attempts) >= MAX_ATTEMPTS:
        seconds_left = await redis.ttl(_key(email))
        minutes_left = max(1, -(-seconds_left // 60))
        raise TooManyRequestsError(f"Too many failed login attempts, try again in {minutes_left} min")


async def register_failed_login(email: str) -> None:
    attempts = await redis.incr(_key(email))
    if attempts == 1:
        # First failure starts the window; Redis deletes the key when it expires
        await redis.expire(_key(email), WINDOW_SECONDS)


async def reset_login_attempts(email: str) -> None:
    await redis.delete(_key(email))
