# coding: utf-8
from IPython.nbformat import current as nbf


f = file('00_notebook_tour.ipynb')
nb1 = nbf.read(f,'ipynb')

f = file('00_notebook_tour-merge.ipynb')
nb2 = nbf.read(f,'ipynb')

cells1 = nb1['worksheets'][0]['cells']
cells2 = nb2['worksheets'][0]['cells']

known_uuid =  set([c['metadata']['uuid'] for c in cells1])


def find_familly(dct,idset):
    a = [];
    print('looking in... ',dct)
    if len(dct) == 0 :
        print('return empty')
        return []
    else :
        for l in dct:
            print('dctl', dct)
            k,v = l.items()[0]
            print('looping on parents', k,v)
            if k in idset:
                print('append k')
                a.append(k)
            else :
                print(' deepens')
                a.extend(find_familly(v,idset))
    return a

c = cells2[1]
#dd = {
#        'z' : {'a':{},'x':{}},
#        'y' : {'t':{},'b':{}}
#     }
#ki = set(['a','b'])
#find_familly(dd,ki)


f = find_familly(c['metadata']['parents_id'], known_uuid)
f
