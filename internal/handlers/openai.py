from logzero import logger

from internal.schemas.openai import Answer, Question
from internal.services.openai import openai_client


async def ask(question: Question) -> Answer:
    logger.info(f"[H.OpenAi] ask question: {question.content}")
    completion = await openai_client.chat.completions.create(
        model="moonshot-v1-8k",
        messages=[
            {
                "role": "system",
                "content": (
                    "你是 Kimi，由 Moonshot AI 提供的人工智能助手，"
                    "你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。"
                    "同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。"
                    "Moonshot AI 为专有名词，不可翻译成其他语言。"
                ),
            },
            {"role": "user", "content": question.content},
        ],
        temperature=0.3,
    )
    return Answer(content=completion.choices[0].message.content)
