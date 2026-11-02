import re
from ..contracts import PlannerDecision,ToolCall

class DemoPlanner:
    """Explicit deterministic fixture runner; never represented as an LLM planner."""
    async def decide(self, context):
        s=context.state
        if s.get('business')=='power':return self.power_decision(context)
        if not s.get('input_id'):
            return PlannerDecision(kind='ask_user',message='请先上传并选择客户反馈 CSV。')
        if not s.get('inspection'):
            tool,args='inspect_dataset',{'dataset_id':s['input_id']}
        elif not s.get('classified_id'):
            tool,args='classify_feedback',{'dataset_id':s['input_id']}
        elif not s.get('statistics_id'):
            args={'dataset_id':s['classified_id']}
            for product in s['inspection']['products']:
                if product in context.prompt: args['product']=product; break
            tool='aggregate_feedback'
        elif not s.get('evidence_id'):
            tool,args='search_knowledge',{'query':'售后 客户反馈 质量 物流 客服 处理时限 退款'}
        elif not s.get('report_id'):
            tool,args='generate_report',{'statistics_id':s['statistics_id'],'evidence_id':s['evidence_id']}
        else:
            return PlannerDecision(kind='finish',message='本地规则演示已完成。统计基于实际数据；分类和报告使用规则与模板，未调用模型。')
        return PlannerDecision(kind='call_tool',calls=[ToolCall(tool_id=tool,arguments=args,call_id='demo_'+tool)])

    def power_decision(self,context):
        s=context.state
        if not s.get('input_id'):return PlannerDecision(kind='ask_user',message='请先上传并选择线路运行 CSV。')
        if not s.get('inspection'):tool,args='inspect_power_data',{'dataset_id':s['input_id']}
        elif not s.get('statistics_id'):
            tool,args='analyze_line_loading',{'dataset_id':s['input_id']}
            for line_id in s['inspection']['line_ids']:
                if line_id in context.prompt:args['line_id']=line_id;break
        elif not s.get('evidence_id'):tool,args='search_knowledge',{'query':'线路 有功 限值 越限 数据分析 复核'}
        elif not s.get('report_id'):tool,args='generate_power_report',{'statistics_id':s['statistics_id'],'evidence_id':s['evidence_id']}
        else:return PlannerDecision(kind='finish',message='线路数据已完成代码统计并生成报告。当前是规则演示，未调用模型。')
        return PlannerDecision(kind='call_tool',calls=[ToolCall(tool_id=tool,arguments=args,call_id='demo_'+tool)])
