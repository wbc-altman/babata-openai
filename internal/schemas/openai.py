from pydantic import BaseModel


class Question(BaseModel):
    content: str


class Answer(BaseModel):
    content: str
