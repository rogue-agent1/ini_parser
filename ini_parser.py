#!/usr/bin/env python3
"""INI file parser."""
import sys
def parse_ini(text):
    result={}; section='DEFAULT'
    for line in text.split('\n'):
        line=line.strip()
        if not line or line[0] in '#;': continue
        if line[0]=='[' and ']' in line: section=line[1:line.index(']')]; result.setdefault(section,{})
        elif '=' in line:
            k,v=line.split('=',1); result.setdefault(section,{})[k.strip()]=v.strip()
    return result
text=sys.stdin.read() if len(sys.argv)<2 else open(sys.argv[1]).read()
ini=parse_ini(text)
for section,kv in ini.items():
    print(f"[{section}]")
    for k,v in kv.items(): print(f"  {k} = {v}")
