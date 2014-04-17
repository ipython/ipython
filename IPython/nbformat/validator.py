from __future__ import print_function
#!/usr/bin/env python
# -*- coding: utf8 -*-
import json
import os

from IPython.external.jsonschema import Draft3Validator
import IPython.external.jsonpointer as jsonpointer
from IPython.utils.py3compat import iteritems


from .current import nbformat, nbformat_schema
schema_path = os.path.join(
    os.path.split(__file__)[0], "v%d" % nbformat, nbformat_schema)


def validate(nbjson, key='/notebook', verbose=False):
    # load the schema file
    with open(schema_path, 'r') as fh:
        schema_json = json.load(fh)

    # resolve internal references
    v3schema = resolve_ref(schema_json)
    v3schema = jsonpointer.resolve_pointer(v3schema, key)

    errors = 0
    v = Draft3Validator(v3schema)
    for error in v.iter_errors(nbjson):
        errors = errors + 1
        if verbose:
            print(error)

    return errors


def resolve_ref(json, schema=None):
    """return a json with resolved internal references

    only support local reference to the same json
    """

    if not schema:
        schema = json

    # if it's a list, resolve references for each item in the list
    if type(json) is list:
        resolved = []
        for item in json:
            resolved.append(resolve_ref(item, schema=schema))

    # if it's a dictionary, resolve references for each item in the
    # dictionary
    elif type(json) is dict:
        resolved = {}
        for key, ref in iteritems(json):
            # if the key is equal to $ref, then replace the entire
            # dictionary with the resolved value
            if key == '$ref':
                assert len(json) == 1
                pointer = jsonpointer.resolve_pointer(schema, ref)
                resolved = resolve_ref(pointer, schema=schema)

            else:
                resolved[key] = resolve_ref(ref, schema=schema)

    # otherwise it's a normal object, so just return it
    else:
        resolved = json

    return resolved
