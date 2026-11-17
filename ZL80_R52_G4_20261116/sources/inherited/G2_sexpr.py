"""Small strict KiCad S-expression reader used for structural checks (not KiCad ERC)."""
from __future__ import annotations
import re
_TOKEN = re.compile(r'\s+|;[^\n]*|\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+')
def loads(text: str):
    stack=[]; roots=[]; pos=0
    for m in _TOKEN.finditer(text):
        if m.start()!=pos: raise ValueError(f'Unexpected text at offset {pos}')
        pos=m.end(); t=m.group()
        if t.isspace() or t.startswith(';'): continue
        if t=='(':
            v=[]
            (stack[-1] if stack else roots).append(v); stack.append(v)
        elif t==')':
            if not stack: raise ValueError(f'Unmatched close at offset {m.start()} line {text.count(chr(10),0,m.start())+1}')
            stack.pop()
        else:
            if not stack: raise ValueError(f'Atom outside expression at {m.start()}')
            if t.startswith('"'):
                # KiCad escapes quotes/backslashes; keep Unicode text untouched.
                t=re.sub(r'\\([\\"nrt])',lambda z:{'n':'\n','r':'\r','t':'\t'}.get(z[1],z[1]),t[1:-1])
            stack[-1].append(t)
    if stack:raise ValueError(f'{len(stack)} unclosed expressions')
    if len(roots)!=1:raise ValueError(f'Expected 1 root, found {len(roots)}')
    return roots[0]
def child(node,key):return next((x for x in node if isinstance(x,list) and x and x[0]==key),None)
def children(node,key):return [x for x in node if isinstance(x,list) and x and x[0]==key]
def walk(node,key):
    if isinstance(node,list):
        if node and node[0]==key:yield node
        for x in node:
            if isinstance(x,list):yield from walk(x,key)
