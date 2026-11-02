import json
import httpx
from .config import settings

class ModelUnavailable(Exception):
    pass

async def completion(messages, tools=None, json_mode=False, vision=False, max_tokens=2600):
    if not settings.live:
        raise ModelUnavailable('未配置真实模型。请设置 AGENT_API_KEY，或切换本地规则演示。')
    if not vision:
        return await langchain_completion(messages,tools,json_mode,max_tokens)
    body = {'model': settings.vision_model if vision else settings.model,
            'messages': messages, 'max_tokens': max_tokens, 'temperature': 0.2}
    if 'deepseek.com' in settings.api_base:
        body['thinking'] = {'type': 'disabled'}
    if tools:
        body['tools'] = tools
        body['parallel_tool_calls'] = False
    if json_mode:
        body['response_format'] = {'type': 'json_object'}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(100, connect=15), follow_redirects=False) as client:
            response = await client.post(settings.api_base + '/chat/completions',
                headers={'Authorization': 'Bearer ' + settings.api_key}, json=body)
        if response.status_code != 200:
            # Never expose provider response bodies: they may echo inputs or credentials.
            raise ModelUnavailable(f'模型服务返回 HTTP {response.status_code}，请检查服务配置与额度。')
        payload = response.json()
        return payload['choices'][0]['message'], payload.get('usage', {})
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        raise ModelUnavailable('模型连接超时或网络不可达。请稍后重试。') from exc
    except (KeyError, ValueError) as exc:
        raise ModelUnavailable('模型返回格式不符合接口约定。') from exc

def json_content(message):
    content = (message.get('content') or '').strip()
    if content.startswith('```'):
        content = content.split('\n',1)[1].rsplit('```',1)[0]
    return json.loads(content)

async def langchain_completion(messages, tools=None, json_mode=False, max_tokens=2600):
    """Real LangChain invocation, behind the existing replaceable model boundary."""
    from langchain_deepseek import ChatDeepSeek
    import openai
    try:
        model=ChatDeepSeek(model=settings.model,api_key=settings.api_key,api_base=settings.api_base,
                          temperature=0.2,max_tokens=max_tokens,timeout=100,max_retries=0,
                          extra_body={'thinking':{'type':'disabled'}})
        runnable=model.bind_tools(tools,parallel_tool_calls=False) if tools else model
        if json_mode:runnable=runnable.bind(response_format={'type':'json_object'})
        result=await runnable.ainvoke(messages)
        content=result.content if isinstance(result.content,str) else ''.join(p.get('text','') for p in result.content if isinstance(p,dict))
        message={'role':'assistant','content':content}
        if result.tool_calls:
            message['tool_calls']=[{'id':c['id'],'type':'function','function':{'name':c['name'],'arguments':json.dumps(c['args'],ensure_ascii=False)}} for c in result.tool_calls]
        reasoning=result.additional_kwargs.get('reasoning_content')
        if reasoning is not None:message['reasoning_content']=reasoning
        usage=result.response_metadata.get('token_usage') or {}
        if not usage and result.usage_metadata:
            u=result.usage_metadata
            usage={'prompt_tokens':u['input_tokens'],'completion_tokens':u['output_tokens'],'total_tokens':u['total_tokens']}
        return message,usage
    except openai.APIStatusError as exc:
        raise ModelUnavailable(f'模型服务返回 HTTP {exc.status_code}，请检查配置与额度。') from exc
    except (openai.APIConnectionError,openai.APITimeoutError) as exc:
        raise ModelUnavailable('模型连接超时或网络不可达。请稍后重试。') from exc
    except (KeyError,ValueError,TypeError) as exc:
        raise ModelUnavailable('LangChain 模型返回格式不符合接口约定。') from exc
