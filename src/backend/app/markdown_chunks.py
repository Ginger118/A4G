"""ATX header boundaries outside fences. Preserve exact source slices and offsets."""
import re
from langchain_text_splitters import MarkdownHeaderTextSplitter
header_splitter=MarkdownHeaderTextSplitter(headers_to_split_on=[('#'*i,f'h{i}') for i in range(1,7)],strip_headers=False)
VERSION='markdown-atx-offset-v1'

def split_markdown(text,splitter):
    boundaries=[0];offset=0;fence=None
    for line in text.splitlines(keepends=True):
        stripped=line.lstrip(' ')
        marker=re.match(r'(`{3,}|~{3,})',stripped) if len(line)-len(stripped)<=3 else None
        if marker:
            token=marker.group(1)
            if fence is None:fence=token
            elif token[0]==fence[0] and len(token)>=len(fence):fence=None
        elif fence is None and re.match(r'^ {0,3}#{1,6}[ \t]+',line) and offset:boundaries.append(offset)
        offset+=len(line)
    boundaries.append(len(text));chunks=[];headers={}
    for start,end in zip(boundaries,boundaries[1:]):
        section=text[start:end]
        # The course splitter supplies title metadata, but never replaces the original text.
        parsed=header_splitter.split_text(section)
        if parsed and re.match(r'^ {0,3}#{1,6}[ \t]+',section):
            local=parsed[0].metadata
            if local:
                level=min(int(k[1:]) for k in local)
                headers={k:v for k,v in headers.items() if int(k[1:])<level};headers.update(local)
        for doc in splitter.create_documents([section]):
            relative=doc.metadata['start_index'];value=doc.page_content
            if relative<0 or text[start+relative:start+relative+len(value)]!=value:raise ValueError('Markdown原文定位失败，未发布文档')
            chunks.append({'id':len(chunks)+1,'text':value,'offset':start+relative,'headers':dict(headers)})
    return chunks
