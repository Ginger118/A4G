"""Course LCEL subchain; one schema-only retry, no new execution authority."""
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from .schemas import Intent
from .. import llm

parser=PydanticOutputParser(pydantic_object=Intent)

async def classify_intent(template,values):
    async def model(prompt):
        messages=[{'role':'system' if m.type=='system' else 'user','content':m.content} for m in prompt.to_messages()]
        message,_=await llm.completion(messages,json_mode=True,max_tokens=700)
        return message.get('content') or ''
    chain=template | RunnableLambda(model) | parser
    for attempt in range(2):
        try:
            # Only add public schema instructions; do not treat an invalid model reply as authority.
            result=await chain.ainvoke({**values,'format_instructions':parser.get_format_instructions()+(' 请重新检查字段类型、枚举和JSON格式，不添加权限字段。' if attempt else '')})
            return result,{'attempts':attempt+1,'repaired':bool(attempt)}
        except OutputParserException:
            if attempt:raise ValueError('任务理解格式连续两次不符合约定，请补充或改写问题后重试') from None
