#!/usr/bin/env python
# -*- coding: utf8 -*-

from IPython.external.jsonschema import  Validator, validate, ValidationError
import IPython.external.jsonpointer as jsonpointer
import argparse
import traceback
import json

v = Validator();
def nbvalidate(nbjson, schema='v3.withref.json', key=None,verbose=True):
    v3schema = resolve_ref(json.load(open(schema,'r')))
    if key :
        v3schema = jsonpointer.resolve_pointer(v3schema,key)
    errors = 0
    for error in v.iter_errors(nbjson, v3schema):
        errors = errors + 1
        if verbose:
            print(error)
    return errors

def resolve_ref(json, base=None):
    """return a json with resolved internal references

    only support local reference to the same json
    """
    if not base :
        base = json

    temp = None
    if type(json) is list:
        temp = [];
        for item in json:
            temp.append(resolve_ref(item, base=base))
    elif type(json) is dict:
        temp = {};
        for key,value in json.iteritems():
            if key == '$ref':
                return resolve_ref(jsonpointer.resolve_pointer(base,value), base=base)
            else :
                temp[key]=resolve_ref(value, base=base)
    else :
        return json
    return temp

def convert(namein, nameout, indent=2):
    """resolve the references of namein, save the result in nameout"""
    jsn = None
    with open(namein) as file :
        jsn = json.load(file)
    v = resolve_ref(jsn, base=jsn)
    x = jsonpointer.resolve_pointer(v, '/notebook')
    with open(nameout,'w') as file:
        json.dump(x,file,indent=indent)


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


