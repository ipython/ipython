#!/usr/bin/env python
# -*- coding: utf8 -*-

from jsonschema import  Draft3Validator, validate, ValidationError
import jsonpointer
from IPython.external import argparse
import traceback
import jsonref
import json

def nbvalidate(nbjson, schema='v3.withref.json', key=None,verbose=True):
    with open(schema) as f:
        v3schema=jsonref.load(f)
    if key :
        v3schema = jsonpointer.resolve_pointer(v3schema,key)
    errors = 0
    v = Draft3Validator(v3schema);
    for error in v.iter_errors(nbjson):
        errors = errors + 1
        if verbose:
            print(error)
    return errors


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
    for name in args.filename :
        nerror = nbvalidate(json.load(open(name,'r')),
                            schema=args.schema,
                            key=args.key,
                            verbose=args.verbose)
        if nerror is 0:
            print u"[Pass]",name
        else :
            print u"[    ]",name,'(%d)'%(nerror)
        if args.verbose :
            print '=================================================='


