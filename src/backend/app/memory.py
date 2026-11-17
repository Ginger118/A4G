"""Persist all messages, select complete recent turns under a conservative byte budget."""
from langchain_core.messages import trim_messages
from . import storage as store
from .config import settings

CHAT_SYSTEM='你是序流电力知识与辅助分析助手，也能回答一般问题。用清晰自然的中文回答，保留会话上下文。普通对话没有检索或执行工具，不编造来源和执行结果；需要文档依据时提示使用资料问答。'

def estimate(messages):
    return sum(len(m.content.encode('utf-8'))+8 for m in messages)

def select_context(owner,session,question):
    rows=store.many('SELECT role,content FROM messages WHERE owner=? AND session_id=? ORDER BY created DESC,rowid DESC LIMIT 200',(owner,session))
    pairs=[];pending=None
    for m in reversed(rows):
        if m['role']=='user':pending=m
        elif m['role']=='assistant' and pending is not None:
            pairs.extend([pending,m]);pending=None
    reserve=len(CHAT_SYSTEM.encode())+len(question.encode())+16
    budget=max(0,settings.chat_context_budget-reserve)
    selected=trim_messages(pairs,max_tokens=budget,token_counter=estimate,strategy='last',start_on='human',end_on='ai',allow_partial=False)
    history=[{'role':'user' if m.type=='human' else 'assistant','content':m.content} for m in selected]
    meta={'strategy':'complete_turns_utf8_budget','budget_units':settings.chat_context_budget,'unit':'UTF-8 bytes + message overhead; not provider tokens','candidate_messages':len(pairs),'selected_messages':len(history),'dropped_messages':len(pairs)-len(history),'history_fetch_limit':200,'estimated_input_units':reserve+estimate(selected)}
    return history,meta
