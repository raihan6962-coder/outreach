from datetime import date
from typing import Optional
from redis.asyncio import Redis


class RateLimiter:
    DAILY_PREFIX = "rate:daily:"
    HOURLY_PREFIX = "rate:hourly:"

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def check_daily_limit(self, gmail_account_id: str, limit: int) -> bool:
        key = f"{self.DAILY_PREFIX}{gmail_account_id}:{date.today().isoformat()}"
        count = await self.redis.get(key)
        if count is None:
            return True
        return int(count) < limit

    async def check_hourly_limit(self, gmail_account_id: str, limit: int) -> bool:
        key = f"{self.HOURLY_PREFIX}{gmail_account_id}:{date.today().isoformat()}"
        count = await self.redis.get(key)
        if count is None:
            return True
        return int(count) < limit

    async def increment_daily(self, gmail_account_id: str):
        key = f"{self.DAILY_PREFIX}{gmail_account_id}:{date.today().isoformat()}"
        await self.redis.incr(key)
        await self.redis.expire(key, 86400)

    async def increment_hourly(self, gmail_account_id: str):
        key = f"{self.HOURLY_PREFIX}{gmail_account_id}:{date.today().isoformat()}"
        await self.redis.incr(key)
        await self.redis.expire(key, 3600)

    async def get_usage(self, gmail_account_id: str) -> dict:
        daily_key = f"{self.DAILY_PREFIX}{gmail_account_id}:{date.today().isoformat()}"
        hourly_key = f"{self.HOURLY_PREFIX}{gmail_account_id}:{date.today().isoformat()}"
        daily = await self.redis.get(daily_key)
        hourly = await self.redis.get(hourly_key)
        return {
            "daily": int(daily) if daily else 0,
            "hourly": int(hourly) if hourly else 0,
        }
