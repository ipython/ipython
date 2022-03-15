#!/usr/bin/env python
"""Utility to look for hard tabs and \r characters in all sources.

Usage:

./check_sources.py

It prints summaries and if chosen, line-by-line info of where \\t or \\r
characters can be found in our source tree.
"""

# Config
# If true, all lines that have tabs are printed, with line number
full_report_tabs = True
# If true, all lines that have tabs are printed, with line number
full_report_rets = False

# Code begins
from IPython.external.path import path

rets = []
tabs = []

for f in path('..').walkfiles('*.py'):
    errs = ''
    cont = f.bytes()
    if '\t' in cont:
        errs+='t'
        tabs.append(f)

    if '\r' in cont:
        errs+='r'
        rets.append(f)
        
    if errs:
        print("%3s" % errs, f)

    if 't' in errs and full_report_tabs:
        for ln,line in enumerate(f.lines()):
            if '\t' in line:
                print('TAB:',ln,':',line, end=' ')

    if 'r' in errs and full_report_rets:
        for ln,line in enumerate(open(f.abspath(),'rb')):
            if '\r' in line:
                print('RET:',ln,':',line, end=' ')

# Summary at the end, to call cleanup tools if necessary
if tabs:
    print('Hard tabs found. These can be cleaned with untabify:')
    for f in tabs: print(f, end=' ')
if rets:
    print('Carriage returns (\\r) found in:')
    for f in rets: print(f, end=' ')
