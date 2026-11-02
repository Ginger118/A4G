#!/usr/bin/env python3
"""Check staged/public files without printing credential values. Standard library only."""
import argparse
import os
from pathlib import Path
import re
import subprocess

PATTERNS={
    'private key':re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'provider token':re.compile(rb'(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{24,}'),
    'GitHub token':re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})'),
    'AWS access key':re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'Slack token':re.compile(rb'\bxox[baprs]-[A-Za-z0-9-]{20,}'),
}
ASSIGNMENT=re.compile(rb'(?im)^[ \t]*(?:[A-Z_]*(?:API_KEY|ACCESS_TOKEN|CLIENT_SECRET|AUTH_TOKEN))[ \t]*=[ \t]*[\"\x27]?([^\s\"\x27#]*)')
PLACEHOLDERS={b'',b'YOUR_API_KEY',b'YOUR_TOKEN',b'CHANGEME',b'REPLACE_ME',b'PLACEHOLDER'}

def findings(path,content):
    p=Path(path)
    protected={'.runtime','.venv','.vendor','node_modules','.ssh','.aws','.vscode'}
    result=[]
    if any(part in protected for part in p.parts):result.append('local/private directory')
    if p.name.startswith('.env') and not p.name.endswith('.example'):result.append('non-template environment file')
    if p.suffix in {'.sqlite','.sqlite3','.db','.pem','.key','.p12','.pfx'}:result.append('private runtime/key file')
    if p.parts and p.parts[0]=='evidence' and p.name!='README.md':result.append('local execution evidence')
    if p.parts and p.parts[0]=='个人材料' and p.name!='填写说明.md':result.append('personal material')
    result += [name for name,pattern in PATTERNS.items() if pattern.search(content)]
    for match in ASSIGNMENT.finditer(content):
        if match.group(1).upper() not in PLACEHOLDERS:result.append('non-placeholder credential assignment')
    for name in ('AGENT_API_KEY','ANTHROPIC_API_KEY','DEEPSEEK_API_KEY','GITHUB_TOKEN','GH_TOKEN'):
        value=os.environ.get(name,'')
        if len(value)>=16 and value.encode() in content:result.append('configured credential value')
    return sorted(set(result))

def git(*args):
    return subprocess.check_output(['git',*args])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged',action='store_true')
    args=parser.parse_args()
    os.chdir(git('rev-parse','--show-toplevel').decode().strip())
    if args.staged:
        paths=git('diff','--cached','--name-only','--diff-filter=ACM','-z').split(b'\0')
    else:
        paths=git('ls-files','--cached','--others','--exclude-standard','-z').split(b'\0')
    failed=False;count=0
    for raw in paths:
        if not raw:continue
        path=os.fsdecode(raw)
        content=git('show',':'+path) if args.staged else Path(path).read_bytes()
        count+=1
        issues=findings(path,content)
        if issues:
            failed=True
            print(path+': '+', '.join(issues))
    print(f'Secret guard: {"BLOCKED" if failed else "passed"} ({count} files checked; credential values are never printed)')
    return 1 if failed else 0

if __name__=='__main__':raise SystemExit(main())
