from .contracts import ToolSpec

class ToolRegistry:
    def __init__(self):
        self.tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec):
        if spec.tool_id in self.tools:
            raise ValueError('重复工具标识')
        self.tools[spec.tool_id] = spec

    def available_specs(self, role='user'):
        return [t for t in self.tools.values() if t.permission == 'user' or role == 'admin']

    def get(self, tool_id):
        if tool_id not in self.tools:
            raise ValueError('未注册的工具')
        return self.tools[tool_id]
