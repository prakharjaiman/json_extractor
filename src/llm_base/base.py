from abc import ABC, abstractmethod
import pydantic
from pydantic import BaseModel

class AgentBase(ABC):

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    


