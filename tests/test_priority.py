import asyncio
import pytest
from langchain_core.prompts import ChatPromptTemplate
from app import storage as store,rag,llm
from app.memory import select_context
from app.config import settings
from app.markdown_chunks import split_markdown
from app.upstream.intent_chain import classify_intent

def save(owner,session,role,text):
    store.execute('INSERT INTO messages VALUES(?,?,?,?,?,?)',(store.uid('m'),owner,session,role,text,store.now()))

def test_memory_more_than_six_turns_and_isolation():
    store.init()
    for i in range(10):save('memory-owner','s','user',f'问题{i}');save('memory-owner','s','assistant',f'答案{i}')
    h,m=select_context('memory-owner','s','追问');assert len(h)==20 and h[0]['content']=='问题0'
    assert select_context('other-owner','s','追问')[0]==[]
    assert select_context('memory-owner','other-session','追问')[0]==[]

def test_memory_budget_pairs_and_no_sql_deletion(monkeypatch):
    store.init()
    for i in range(4):save('limited','s','user','问'+str(i)+'字'*30);save('limited','s','assistant','答'+str(i)+'文'*30)
    save('limited','s','user','失败后未完成的问题')
    from app.memory import CHAT_SYSTEM
    monkeypatch.setattr(settings,'chat_context_budget',len(CHAT_SYSTEM.encode())+len('追问'.encode())+16+240)
    h,m=select_context('limited','s','追问');assert len(h)==2 and h[0]['content'].startswith('问3')
    assert h[-1]['role']=='assistant' and m['dropped_messages']==6
    assert len(store.many('SELECT * FROM messages WHERE owner=?',('limited',)))==9

@pytest.mark.parametrize('text',['# 同名\n重复\n\n## 子标题\n重复\n\n# 同名\n重复','前言\r\n# 标题\r\n重复\r\n\r\n## 子题\r\n正文',' # 标题\n~~~python\n# 不应分段\n~~~\n## 真标题\n正文'])
def test_markdown_exact_offsets_and_headers(text):
    chunks=split_markdown(text,rag.splitter)
    assert chunks and all(text[c['offset']:c['offset']+len(c['text'])]==c['text'] for c in chunks)
    assert all(c['offset']>=0 for c in chunks)
    assert any(c['headers'] for c in chunks)
    if '不应分段' in text:assert len(chunks)==2

def test_markdown_sections_do_not_mix_and_plaintext_unchanged():
    c=split_markdown('# A\n第一章\n\n# B\n第二章',rag.splitter)
    assert len(c)==2 and c[0]['headers']=={'h1':'A'} and c[1]['headers']=={'h1':'B'}
    assert '第二章' not in c[0]['text']

TEMPLATE=ChatPromptTemplate.from_messages([('system','分类，仅JSON {format_instructions}'),('human','{question}')])
@pytest.mark.parametrize('replies,attempts',[(['{"intent_type":"chat","goal":"问候","requires_bos":false}'],1),(['bad-json','{"intent_type":"chat","goal":"问候","requires_bos":false}'],2)])
def test_structured_chain_success_or_one_repair(monkeypatch,replies,attempts):
    seen=[]
    async def model(*a,**kw):seen.append(a);return {'content':replies[len(seen)-1]},{}
    monkeypatch.setattr(llm,'completion',model)
    result,meta=asyncio.run(classify_intent(TEMPLATE,{'question':'你好'}))
    assert result.intent_type=='chat' and meta['attempts']==attempts and len(seen)==attempts

@pytest.mark.parametrize('bad',['bad-json','{"intent_type":"chat","goal":"x","execution_authorized":true}'])
def test_invalid_intent_never_executes_or_retries_forever(monkeypatch,bad):
    calls=[]
    async def model(*a,**kw):calls.append(1);return {'content':bad},{}
    monkeypatch.setattr(llm,'completion',model)
    with pytest.raises(ValueError,match='连续两次'):asyncio.run(classify_intent(TEMPLATE,{'question':'你好'}))
    assert len(calls)==2

def test_model_error_not_retried(monkeypatch):
    calls=[]
    async def model(*a,**kw):calls.append(1);raise llm.ModelUnavailable('教学故障')
    monkeypatch.setattr(llm,'completion',model)
    with pytest.raises(llm.ModelUnavailable):asyncio.run(classify_intent(TEMPLATE,{'question':'你好'}))
    assert len(calls)==1
