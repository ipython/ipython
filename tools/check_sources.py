from IPython.external.path import path
fs = path('..').walkfiles('*.py')

for f in fs:
    errs = ''
    cont = f.bytes()
    if '\t' in cont:
        errs+='t'

    if '\r' in cont:
        errs+='r'
        
    if errs:
        print "%3s" % errs, f
    
