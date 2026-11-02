from dataclasses import dataclass, field
from typing import Any, Literal, Protocol
from pydantic import BaseModel, Field, ConfigDict

class ToolCall(BaseModel):
    tool_id: str
    arguments: dict = Field(default_factory=dict)
    call_id: str = ''

class PlannerDecision(BaseModel):
    kind: Literal['call_tool','finish','ask_user']
    calls: list[ToolCall] = Field(default_factory=list)
    message: str = ''
    usage: dict = Field(default_factory=dict)

class ToolResult(BaseModel):
    success: bool
    output: dict = Field(default_factory=dict)
    error: str | None = None
    duration_ms: int = 0

class ToolArguments(BaseModel):
    model_config = ConfigDict(extra='forbid')

@dataclass
class ToolSpec:
    tool_id: str
    name: str
    description: str
    input_model: type[BaseModel]
    execute: Any
    output_schema: dict = field(default_factory=lambda: {'type':'object'})
    timeout: int = 120
    permission: str = 'user'
    version: str = '1.0'
    preconditions: Any = None
    effects: Any = None
    cost: Any = None
    uncertainty: Any = None

    def schema(self):
        return {'type':'function','function':{'name':self.tool_id,'description':self.description,
                                             'parameters':self.input_model.model_json_schema()}}

@dataclass
class PlanningContext:
    task_id: str
    owner: str
    prompt: str
    mode: str
    state: dict
    history: list[dict]
    tools: list[ToolSpec]

class Planner(Protocol):
    async def decide(self, context: PlanningContext) -> PlannerDecision: ...
