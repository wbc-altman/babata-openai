from datetime import timedelta

from fastapi import Body, Depends
from fastapi.routing import APIRouter
from jose import jwt

from internal.api.deps import check_token
from internal.conf.settings import app_settings
from internal.handlers import account as account_handler
from internal.models import T_Account
from internal.schemas.auth import AccountOut, Token
from pkg.exceptions import ValidationException
from pkg.response import Response
from utils import local_now, verify_password

router = APIRouter()


@router.post("/login", response_model=Response[Token])
async def login(username: str = Body(...), password: str = Body(...)):
    account = await T_Account.get_object_or_none(username=username)
    if account is None:
        raise ValidationException("username invalid")

    if not verify_password(plain_password=password, hashed_password=account.password):
        raise ValidationException("password invalid")

    access_token_expires = timedelta(minutes=60 * 2)

    data = {
        "account_id": account.id,
        "exp": local_now() + access_token_expires,
    }

    encoded_jwt = jwt.encode(
        data,
        app_settings.JWT_SECRET_KEY,
        algorithm=app_settings.JWT_ALGORITHM,
    )

    return Response[Token](
        data=Token(
            access_token=encoded_jwt,
        )
    )


@router.post("/register", response_model=Response[AccountOut])
async def register(username: str = Body(...), password: str = Body(...)):
    it = await account_handler.create_account(username, password)
    return Response[AccountOut](data=it)


@router.get("/profile", response_model=Response[AccountOut])
async def profile(it: T_Account = Depends(check_token)):
    return Response[AccountOut](data=it)
