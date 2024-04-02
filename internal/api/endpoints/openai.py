from fastapi import Depends
from fastapi.routing import APIRouter

from internal.handlers import openai as openai_handler
from internal.models import T_Account
from internal.schemas.openai import Answer, Question
from pkg.response import Response

from ..deps import check_token

router = APIRouter()


@router.post("/ask", response_model=Response[Answer])
async def ask(question: Question, _: T_Account = Depends(check_token)):
    result = await openai_handler.ask(question)
    return Response[Answer](data=result)
