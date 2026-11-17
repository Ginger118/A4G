"""Verified capability catalogue, not model-created action semantics."""
from .schemas import TaskContract
CAPABILITIES = {
 'inspect_power_data': [],
 'analyze_line_loading': ['inspect_power_data'],
 'search_knowledge': [],
 'generate_power_report': ['analyze_line_loading','search_knowledge'],
}
def validate_contract(contract: TaskContract, known_refs: set[str]) -> TaskContract:
    if contract.constraints != {'mode':'read_only','allow_model_parameter_change':False,'execution_authorized':False}:
        raise ValueError('任务草案不能授予执行或写入权限')
    seen=set(); capabilities=set()
    for step in contract.plan_steps:
        if step.capability_id not in CAPABILITIES: raise ValueError('未知能力')
        if step.step_id in seen or any(d not in seen for d in step.depends_on): raise ValueError('步骤依赖无效')
        if not set(CAPABILITIES[step.capability_id]) <= capabilities: raise ValueError('缺少能力前提')
        if any(ref not in known_refs for ref in step.input_refs): raise ValueError('输入来源未核验')
        seen.add(step.step_id); capabilities.add(step.capability_id)
    if any(ref not in known_refs for ref in contract.evidence_refs): raise ValueError('证据引用无效')
    if contract.status=='ready_for_planner':
        if contract.missing_fields or not contract.plan_steps or not contract.evidence_refs: raise ValueError('证据与步骤不完整')
        if not contract.scope.get('dataset_sha256'): raise ValueError('缺少有效输入版本')
        if not contract.goal.get('acceptance_predicates'): raise ValueError('目标判据缺失')
    return contract
