from grpc import ServicerContext

from internal.grpc import pb
from internal.handlers import openai as openai_handler
from internal.schemas.openai import Question


class BabataOpenAIServicer(pb.BabataOpenAIServicer):
    async def Ping(
        self,
        _ignored_request: pb.PingRequest,
        _ignored_context: ServicerContext,
    ) -> pb.PingResponse:
        """Ping returns pong."""
        return pb.PingResponse(pong=True)

    async def Ask(
        self,
        req: pb.AskRequest,
        _ignored_context: ServicerContext,
    ) -> pb.AskResponse:
        result = await openai_handler.ask(Question(content=req.content))
        return pb.AskResponse(content=result.content)
