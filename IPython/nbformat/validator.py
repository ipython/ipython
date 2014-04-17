from __future__ import print_function
#!/usr/bin/env python
# -*- coding: utf8 -*-
import json
import os

from IPython.external.jsonschema import Draft3Validator
import IPython.external.jsonpointer as jsonpointer
from IPython.utils.py3compat import iteritems


from .current import nbformat, nbformat_schema
schema = os.path.join(
    os.path.split(__file__)[0], "v%d" % nbformat, nbformat_schema)


def validate(nbjson, key='/', verbose=True):
    v3schema = resolve_ref(json.load(open(schema, 'r')))
    if key:
        v3schema = jsonpointer.resolve_pointer(v3schema, key)
    errors = 0
    v = Draft3Validator(v3schema)
    for error in v.iter_errors(nbjson):
        errors = errors + 1
        if verbose:
            print(error)
    return errors


def resolve_ref(json, base=None):
    """return a json with resolved internal references

    only support local reference to the same json
    """
    if not base:
        base = json

    temp = None
    if type(json) is list:
        temp = []
        for item in json:
            temp.append(resolve_ref(item, base=base))
    elif type(json) is dict:
        temp = {}
        for key, value in iteritems(json):
            if key == '$ref':
                return resolve_ref(
                    jsonpointer.resolve_pointer(base, value), base=base)
            else:
                temp[key] = resolve_ref(value, base=base)
    else:
        return json
    return temp


def convert(namein, nameout, indent=2):
    """resolve the references of namein, save the result in nameout"""
    jsn = None
    with open(namein) as file:
        jsn = json.load(file)
    v = resolve_ref(jsn, base=jsn)
    x = jsonpointer.resolve_pointer(v, '/notebook')
    with open(nameout, 'w') as file:
        json.dump(x, file, indent=indent)
