#!/usr/bin/env python
# -*- coding: utf8 -*-

from jsonschema import  Draft3Validator, validate, ValidationError
import jsonpointer
from IPython.external import argparse
import traceback
import jsonref
import json
import os.path

def nbvalidate(nbjson, schema, key=None, verbose=False):
    if key :
        schema = jsonpointer.resolve_pointer(schema,key)
    errors = 0
    v = Draft3Validator(schema);
    for error in v.iter_errors(nbjson):
        errors = errors + 1
        if verbose:
            print(error)
    return errors

def v3schema():
    with open(os.path.join(os.path.dirname(__file__),'v3.withref.json')) as f:
        schema=jsonref.load(f)
    return schema

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--schema',
                    type=str, default='v3.withref.json')

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

    with open(args.schema) as f:
        schema=jsonref.load(f)

    for name in args.filename :
        with open(name) as notebook:
            nerror = nbvalidate(json.load(notebook),
                                schema,
                                key=args.key,
                                verbose=args.verbose)
        if nerror is 0:
            print u"[Pass]",name
        else :
            print u"[    ]",name,'(%d)'%(nerror)
        if args.verbose :
            print '=================================================='


