import asyncio
import datetime
import functools
import random
from typing import Callable, Union

import bcrypt
import orjson
from logzero import logger


def json_loads(obj: bytes | bytearray | memoryview | str) -> object:
    return orjson.loads(obj)


def json_dumps(obj: object, *, default: None | Callable[..., str] = None) -> str:
    # orjson.dumps returns bytes, apply decode() to match json.dumps
    return orjson.dumps(
        obj,
        default=default,
        option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY,
    ).decode()


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


local_tz = datetime.datetime.now().astimezone().tzinfo


def local_now() -> datetime.datetime:
    return datetime.datetime.now().replace(tzinfo=local_tz)


def local_now_ts() -> int:
    return int(local_now().timestamp())


def local_timestamp(ts: Union[int, float]) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(ts).replace(tzinfo=local_tz)


def local_today() -> datetime.datetime:
    return datetime.datetime.combine(
        datetime.datetime.now().date(), datetime.time.min
    ).replace(tzinfo=local_tz)


def local_today_ts() -> int:
    return int(local_today().timestamp())


def sampled(ratio: float = 1.0) -> bool:
    return random.random() < ratio


def retry(stop_max_attempt_number=2):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for i in range(1, stop_max_attempt_number):
                try:
                    return await func(*args, **kwargs)
                except Exception as ex:
                    logger.info(
                        f"retry function {func.__name__} call failed wait {0.1}s time"
                        f" {i}, <== {ex=}"
                    )
                    await asyncio.sleep(0.1)
            else:
                logger.info(f"retry function {func.__name__} last time")
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def sample_in_rate(rate: float = 1.0) -> bool:
    return random.random() < rate
