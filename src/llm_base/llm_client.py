from groq import Groq

from src.serializers.base import Model, LLMMessages, Response


class LLMGroqClient:
    def __init__(self, model: Model, groq_api_key: str,  temperature: float = 1,
        top_p: float = 1,
        n: int = 1,):
        self.model = model
        self.client =Groq(api_key=groq_api_key)
        self.temperature = temperature
        self.top_p = top_p
        self.n = n


    async def get_chat_response(self, messages: list[LLMMessages], is_json: bool = False, max_completion_tokens: int = None):
        llm_messages = [m.dict(exclude_none=True) for m in messages]
        response = await self.client.chat.completions.create(
            model = self.model.name,
            messages = llm_messages,
            temperature=self.temperature,
           top_p=self.top_p,
           response_format={"type": "json_object"} if is_json else None,
           max_completion_tokens=max_completion_tokens if max_completion_tokens else 4096,
        )

        return response.choices[0].message


       








