#!/usr/bin/env python
# coding: utf-8

from IPython.nbformat import current as nbf
from  difflib import context_diff, ndiff, unified_diff
import json
import argparse

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


class Cell(object):

    def __init__(self,cell):
        self._json = cell
        self.uuid = cell['metadata']['uuid']
        if hasattr(cell,'input'):
            self.input = cell['input']
        else:
            self.input = cell['source']

class NewCell(Cell):

    def __init__(self,cell):
        super(NewCell, self).__init__(cell)
        self.ancesters = [];

    def diff(self):
        ancesters = self.ancesters
        s1 = self.input.splitlines()
        s2p = '\n'.join([ x.input for x in ancesters])
        s2 = s2p.splitlines()
        if(len(ancesters) >1):
            oldfile = '%d_old_cells'%(len(ancesters))
        else :
            oldfile = '%d_old_cell'%(len(ancesters))
        return [ r.strip('\n') for r in unified_diff(s2, s1, fromfile=oldfile, tofile='1_new_cell', n=500)]

class OldCell(Cell):
    pass


class NotebookDiffer(object):

    def __init__(self,oldfile,newfile) :
        """Create a object to generate the diff between 2 notebooks"""
        self.oldfile = oldfile
        self.newfile = newfile

        self.oldcells = [OldCell(c) for c in oldfile['worksheets'][0]['cells']]
        self.newcells = [NewCell(c) for c in newfile['worksheets'][0]['cells']]

        self.known_uuids = set(c.uuid for c in self.oldcells)
        for c in self.newcells :
            auuid =  find_cell_ancester(c._json, self.known_uuids)
            c.ancesters = [self.get_old_cell(uuid=u) for u in auuid]

    def get_cell(self,cells, number=None ,uuid=None):
        if number is None and uuid is None :
            raise ValueError('You should either give a number or an uuid to get a cell')
        if number is not None :
            cells.get(number)
        else :
            lst = [c for c in cells if c.uuid==uuid ]
            if len(lst)>1:
                raise ValueError('Got 2 cells with same id....')
            return lst[0]

    def get_old_cell(self,number=None, uuid=None):
        return self.get_cell(self.oldcells, number, uuid)

    def get_new_cell(self,number=None, uuid=None):
        return self.get_cell(self.newcells, number, uuid)

    def diff(self):
        l = []
        for i,c in enumerate(self.newcells):
            l.append('@@ diff for cell %d @@'%(i+1))
            l.extend(c.diff())
        return l

    def jsondiff(self):
        cells = []
        for i,c in enumerate(self.newcells):
            l = []
            l.append('@@ diff for cell %d @@'%(i+1))
            celldiff = c.diff()
            # keep identical cell untouched.
            if len(celldiff) == 0 :
                cells.append(c._json);
                continue
            l.extend(c.diff())
            cell = nbf.new_code_cell(input='\n'.join(l))
            cells.append(cell)

        ws = nbf.new_worksheet('u0',cells=cells)
        nb = nbf.new_notebook('mergedof', worksheets=[ws])
        return nb


def main(*args):
    parser = argparse.ArgumentParser(
            description="""
                output the diff of 2 notebooks
                """
            )

    parser.add_argument('old',
            type=str,
            help="The oldest file",
            metavar='old')
    parser.add_argument('new',
            type=str,
            help="The newest file",
            metavar='new')
    args = parser.parse_args()

    if args.old and args.new:
        f = file(args.old)
        nb1 = nbf.read(f,'ipynb')

        f = file(args.new)
        nb2 = nbf.read(f,'ipynb')

        nbdiff = NotebookDiffer(nb1,nb2)

        js = nbdiff.jsondiff()
        print json.dumps(js, sort_keys=True, indent=1)


if __name__ == '__main__':
    main()
