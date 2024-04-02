from typing import Optional

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader
from fastapi.security.utils import get_authorization_scheme_param
from jose import JWTError, jwt

from internal.conf.settings import app_settings
from internal.models import T_Account
from internal.store.db import ScopedSession
from pkg.exceptions import UnauthorizedException, ValidationException


async def get_token(
    token: str = Security(APIKeyHeader(name="Authorization", auto_error=False)),
) -> Optional[str]:
    scheme, param = get_authorization_scheme_param(token)
    if not token or scheme.lower() != "bearer":
        raise UnauthorizedException()
    return param


async def check_token(token: str = Depends(get_token)) -> T_Account:
    err = UnauthorizedException("token invalid")
    try:
        payload = jwt.decode(
            token,
            app_settings.JWT_SECRET_KEY,
            algorithms=[app_settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise err
    account_id: int = payload.get("account_id")
    if account_id is None:
        raise err

    account = await T_Account.get_object_or_none(id=account_id)
    if account is None:
        raise ValidationException(f"account: {account_id} not found")
    return account


async def get_session():
    session = ScopedSession()
    try:
        yield session
    finally:
        await ScopedSession.remove()
