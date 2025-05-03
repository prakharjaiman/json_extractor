from groq import Groq

from src.serializers.base import Model, LLMMessages, Response


class LLMGroqClient:
    def __init__(self, model: Model, groq_api_key: str,  temperature: float = 1,
        top_p: float = 1,
        n: int = 1,
        verbose: bool = False):
        self.model = model
        self.client =Groq(api_key=groq_api_key)
        self.temperature = temperature
        self.top_p = top_p
        self.n = n
        self.verbose = verbose

    def get_chat_response(self, messages: list[LLMMessages])-> Response:





