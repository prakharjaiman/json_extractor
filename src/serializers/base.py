import json
from enum import Enum
import re
from typing import Union, Any
from uuid import uuid4

from pydantic import BaseModel

class Model(Enum):
    llama_70b = "llama-3.3-70b-versatile"
    deepseek = "deepseek-r1-distill-llama-70b"
    llama_8b = "llama-3.1-8b-instant"

class Role(Enum):
    system = "system"
    user = "user"
    assistant = "assistant"
    tool = "tool"

class FunctionCall(BaseModel):
    name: str
    arguments: str

class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: FunctionCall

    def fn_name(self):
        return self.function.name

    def args(self):
        return json.loads(self.function.arguments)

    @classmethod
    def make_new_call_id(cls):
        return f"call_{uuid4().hex[:24]}"


class SystemMessage(BaseModel):
    role: str = Role.system.name
    content: str


class UserMessage(BaseModel):
    role: str = Role.user.name
    content: str


class AssistantMessage(BaseModel):
    role: str = Role.assistant.name
    content: str | None
    tool_calls: list[ToolCall] | None = None


class ToolMessage(BaseModel):
    role: str = Role.tool.name
    content: str
    tool_call_id: str

LLMMessages = Union[SystemMessage, UserMessage, AssistantMessage, ToolMessage]
RoleMessageTypeMapping = {
    Role.system: SystemMessage,
    Role.user: UserMessage,
    Role.assistant: AssistantMessage,
    Role.tool: ToolMessage,
}

class Response(BaseModel):
    content: str | None
    tool_calls: list[ToolCall] | None = None

    def to_assistant_message(self):
        return AssistantMessage(content=self.content, tool_calls=self.tool_calls)

    @classmethod
    #todo: check. From chatgpt
    def from_api_response(
        cls,
        response: Any,
        extract_json: bool = False
    ):
        choice = response.choices[0]
        message = choice.message
        content = message.content

        tool_calls: list[ToolCall] = []
        raw_tc = getattr(message, "tool_calls", None)
        if raw_tc:
            for tc in raw_tc:
                if tc.function.name == "multi_tool_use.parallel":
                    batch = json.loads(tc.function.arguments).get("tool_uses", [])
                    if not batch:
                        raise ValueError("No tool_uses found in parallel call")
                    for use in batch:
                        fn = use["recipient_name"].split(".")[-1]
                        args = json.dumps(use["parameters"])
                        tool_calls.append(
                            ToolCall(
                                id=tc.id,
                                function=FunctionCall(name=fn, arguments=args),
                            )
                        )
                else:
                    tool_calls.append(
                        ToolCall(
                            id=tc.id,
                            function=FunctionCall(
                                name=tc.function.name,
                                arguments=tc.function.arguments,
                            ),
                        )
                    )

        # (Optional) extract a JSON blob from the content
        if extract_json:
            m = re.search(r"\{.*}", content, re.DOTALL)
            if not m:
                raise ValueError(f"Could not extract JSON from response: {content!r}")
            content = m.group(0)
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON after extraction: {e}")

        return cls(
            content=content,
            tool_calls=tool_calls or None,
        )