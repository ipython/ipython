# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function
import json
import os

try:
    from jsonschema import ValidationError
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

validator = None

def _load_schema():
    """Load the JSON schema into the global Validator"""
    global validator
    if validator is None:
        # load the schema file
        with open(schema_path, 'r') as fh:
            schema_json = json.load(fh)

        # create the validator
        validator = Validator(schema_json)
    return validator

def isvalid(nbjson, ref=None):
    """Checks whether the given notebook JSON conforms to the current
    notebook format schema. Returns True if the JSON is valid, and
    False otherwise.

    To see the individual errors that were encountered, please use the
    `validate` function instead.
    """
    try:
        validate(nbjson, ref)
    except ValidationError:
        return False
    else:
        return True


def validate(nbjson, ref=None):
    """Checks whether the given notebook JSON conforms to the current
    notebook format schema.

    Raises ValidationError if not valid.
    """
    _load_schema()

    if ref:
        return validator.validate(nbjson, {'$ref' : '#/definitions/%s' % ref})
    else:
        return validator.validate(nbjson)
