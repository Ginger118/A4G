"""DAY3 structured output; draft contracts carry no execution authority."""
from typing import Literal, TypedDict
from pydantic import BaseModel, ConfigDict, Field

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

class UpstreamRequest(StrictModel):
    question: str = Field(min_length=2,max_length=6000)
    mode: Literal['live','demo'] = 'live'
    session_id: str = Field(default='',max_length=100,pattern=r'^[a-zA-Z0-9_-]*$')
    document_ids: list[str] = Field(default_factory=list,max_length=8)
    dataset_id: str | None = None
    scene_ref: str | None = Field(default=None,max_length=100)
    snapshot_ref: str | None = Field(default=None,max_length=100)

class Intent(StrictModel):
    intent_type: Literal['chat','document_qa','data_query','analysis','plan_request']
    goal: str = Field(default='',max_length=1000)
    requires_bos: bool = False

class PlanStep(StrictModel):
    step_id: str
    capability_id: str
    purpose: str
    depends_on: list[str] = Field(default_factory=list)
    input_refs: list[str] = Field(default_factory=list)
    execution: Literal['not_executed'] = 'not_executed'

class TaskContract(StrictModel):
    schema_version: Literal['upstream.v0.1'] = 'upstream.v0.1'
    request_id: str
    intent_type: str
    scope: dict
    goal: dict
    constraints: dict = Field(default_factory=lambda:{'mode':'read_only','allow_model_parameter_change':False,'execution_authorized':False})
    evidence_refs: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    status: Literal['answered','needs_clarification','needs_evidence','ready_for_planner']
    plan_steps: list[PlanStep] = Field(default_factory=list)
    created_at: str
    downstream_status: Literal['not_connected'] = 'not_connected'

class UpstreamState(TypedDict, total=False):
    question: str
    mode: str
    owner: str
    request_id: str
    session_id: str
    document_ids: list[str]
    dataset_id: str | None
    scene_ref: str | None
    snapshot_ref: str | None
    previous: dict
    intent: dict
    intent_diagnostics: dict
    scope: dict
    missing_fields: list[str]
    evidence: list[dict]
    plan_steps: list[dict]
    answer: str
    contract: dict
