#!/usr/bin/env python
"""Utility to look for hard tabs and \r characters in all sources.
"""

from IPython.external.path import path

fs = path('..').walkfiles('*.py')

rets = []

for f in fs:
    errs = ''
    cont = f.bytes()
    if '\t' in cont:
        errs+='t'

    if '\r' in cont:
        errs+='r'
        rets.append(f)
        
    if errs:
        print "%3s" % errs, f
        if 't' in errs:
            for ln,line in enumerate(f.lines()):
                if '\t' in line:
                    print 'TAB:',ln,':',line,
        if 'r' in errs:
            for ln,line in enumerate(open(f.abspath(),'rb')):
                if '\r' in line:
                    print 'RET:',ln,':',line,

rr = rets[-1]
