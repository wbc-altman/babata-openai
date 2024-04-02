from internal.models import T_Account
from internal.store.db import ScopedSession
from pkg.exceptions import ValidationException
from utils import get_password_hash


async def create_account(username: str, password: str) -> T_Account:
    account = await T_Account.get_object_or_none(username=username)
    if account is not None:
        raise ValidationException(f"username:{username} already exist")

    session = ScopedSession()

    db_account = T_Account(
        username=username, password=get_password_hash(password=password)
    )

    session.add(db_account)
    await session.commit()
    await session.refresh(db_account)
    return db_account
