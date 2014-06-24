# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function
import json
import os

try:
    from jsonschema import SchemaError
    from jsonschema import Draft4Validator as Validator
except ImportError as e:
    verbose_msg = """

    IPython notebook format depends on the jsonschema package:

        https://pypi.python.org/pypi/jsonschema

    Please install it first.
    """
    raise ImportError(str(e) + verbose_msg)


from .nbbase import nbformat, nbformat_schema
schema_path = os.path.join(
    os.path.dirname(__file__), nbformat_schema,
)


def isvalid(nbjson, ref=None):
    """Checks whether the given notebook JSON conforms to the current
    notebook format schema. Returns True if the JSON is valid, and
    False otherwise.

    To see the individual errors that were encountered, please use the
    `validate` function instead.
    """

    it = validate(nbjson, ref)
    try:
        it.next()
    except StopIteration:
        return True
    else:
        return False


def validate(nbjson, ref=None):
    """Checks whether the given notebook JSON conforms to the current
    notebook format schema.

    Returns a generator for errors.
    """

    # load the schema file
    with open(schema_path, 'r') as fh:
        schema_json = json.load(fh)

    # create the validator
    v = Validator(schema_json)

    # return the iterator on errors
    if ref:
        errors = v.iter_errors(nbjson, {'$ref' : '#/definitions/%s' % ref})
    else:
        errors = v.iter_errors(nbjson)
    return errors
