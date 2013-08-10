#!/usr/bin/env python
# -*- coding: utf8 -*-

"""
methods to validate json notebook agains a schema.

Instead of having a deep schema, top level of the schema contain subscheme
that describe individually each type of cell and can be referenced with
json references.

Thus when asking to validate a json object agains a schema you need
to specify the key

"""

from jsonschema import  Draft3Validator, validate, ValidationError
import jsonpointer
from IPython.external import argparse
import traceback
import jsonref
import json
import os.path

def nbvalidate(nbjson, schema, key='/notebook', verbose=False):
    """validate notebook versus a json schema
    
    key: json pointer to a subkey of the schema
    use if you only want to validate a sub-part of a notebook
    like a code_cell or worksheet.
    """
    if key :
        schema = jsonpointer.resolve_pointer(schema,key)
    errors = 0
    v = Draft3Validator(schema);
    for error in v.iter_errors(nbjson):
        errors = errors + 1
        if verbose:
            print(error)
    return errors

def detailed_error(nbjson):
    """try to describe errors as much as possible"""
    try :
        # loop through each cell and if code cell check
        # for prompt number
        for cell in nbjson['worksheets'][0]['cells']:
            if cell['cell_type'] == 'code':
                if "prompt_number" not in cell.keys():
                    print "          - code cell has no prompt number...."
                else :
                    if type(cell["prompt_number"]) is not int:
                        print "          - prompt number is not int"
    except Exception as e:
        print " "*8,"unknown error",e


@property
def v3schema():
    return getV3schema()

def getV3schema():
    """schema to validate v3 notebook
    """
    with open(os.path.join(os.path.dirname(__file__),'v3.withref.json')) as f:
        schema=jsonref.load(f)
    return schema

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--schema',
                    type=str, default='')

    parser.add_argument('-k', '--key',
                    type=str, default='/notebook',
                    help='subkey to extract json schema from json file')

    parser.add_argument("-v", "--verbose", action="store_true",
                    help="increase output verbosity")

    parser.add_argument('filename',
            type=str,
            help="file to validate",
            nargs='*',
            metavar='names')

    args = parser.parse_args()

    if args.schema :
        with open(args.schema) as f:
            schema=jsonref.load(f)
    else:
        schema = getV3schema()

    for name in args.filename :
        with open(name) as notebook:
            nb = json.load(notebook)
            nerror = nbvalidate(nb,
                                schema,
                                key=args.key,
                                verbose=args.verbose)
        if nerror is 0:
            print u"[Pass]",name
        else :
            print u"[    ]",name,'(%d)'%(nerror)
            detailed_error(nb)
        if args.verbose :
            print '=================================================='


