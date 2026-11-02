import asyncio
import time
from pydantic import ValidationError
from .contracts import ToolResult
from .. import storage as store

class Executor:
    def __init__(self, registry):
        self.registry = registry

    async def execute(self, call, context):
        started = time.perf_counter()
        before = {k:v for k,v in context.state.items() if k != 'messages'}
        store.event(context.task_id, 'tool_started', call.tool_id,
                    {'tool_id':call.tool_id,'call_id':call.call_id,'arguments':call.arguments,'state_before':before})
        try:
            tool = self.registry.get(call.tool_id)
            actor = store.one('SELECT role FROM users WHERE id=?', (context.owner,))
            if not actor or (tool.permission != 'user' and actor['role'] != 'admin'):
                raise ValueError('当前用户无权调用此工具')
            args = tool.input_model.model_validate(call.arguments)
            output = await asyncio.wait_for(tool.execute(args, context), timeout=tool.timeout)
            import jsonschema
            jsonschema.validate(output, tool.output_schema)
            result = ToolResult(success=True, output=output)
        except asyncio.TimeoutError:
            result = ToolResult(success=False, error='工具执行超时')
        except ValidationError:
            result = ToolResult(success=False, error='工具参数不符合输入规范，请检查字段和类型')
        except ValueError as exc:
            result = ToolResult(success=False, error=str(exc)[:300])
        except Exception:
            result = ToolResult(success=False, error='工具发生内部错误，本次调用未完成')
        result.duration_ms = round((time.perf_counter()-started)*1000)
        store.event(context.task_id, 'tool_completed' if result.success else 'tool_failed',
                    call.tool_id, {'tool_id':call.tool_id,'call_id':call.call_id, **result.model_dump(),
                                   'state_after':{k:v for k,v in context.state.items() if k != 'messages'}})
        return result
