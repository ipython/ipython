# coding: utf-8
from IPython.nbformat import current as nbf
from  difflib import context_diff, ndiff, unified_diff




f = file('000-test-merge-split.ipynb')
nb1 = nbf.read(f,'ipynb')

f = file('000-test-merge-split-step3.ipynb')
nb2 = nbf.read(f,'ipynb')

cells1 = nb1['worksheets'][0]['cells']
cells2 = nb2['worksheets'][0]['cells']

known_uuid =  set([c['metadata']['uuid'] for c in cells1])


def find_cell_ancester(cell,known_ids) :
    if(cell['metadata']['uuid'] in known_ids) :
        return [cell['metadata']['uuid']]

    return find_familly(cell['metadata']['parents_id'], known_ids)

def find_familly(dct,idset):
    a = [];
    if len(dct) == 0 :
        return []
    else :
        for l in dct:
            k,v = l.items()[0]
            if k in idset:
                a.append(k)
            else :
                a.extend(find_familly(v,idset))
    return a

c = cells2[0]

cellbyid = {};
for c in cells1 : 
    cellbyid[c['metadata']['uuid']] = c

for c in cells2 :
    ancesters = find_cell_ancester(c,known_uuid)
    c.ancesters = ancesters
    s1 = c['input'].splitlines()
    s2p = '\n'.join([ cellbyid[x]['input'] for x in ancesters])
    s2 = s2p.splitlines()
    if(len(ancesters) >1):
        oldfile = '%d_old_cells'%(len(ancesters)) 
    else :
        oldfile = 'old_cell'
    print '\n'.join([ r.strip('\n') for r in unified_diff(s2, s1, fromfile=oldfile, tofile='1 new cell')])


#dd = {
#        'z' : {'a':{},'x':{}},
#        'y' : {'t':{},'b':{}}
#     }
#ki = set(['a','b'])
#find_familly(dd,ki)

#f = find_familly(c['metadata']['parents_id'], known_uuid)
