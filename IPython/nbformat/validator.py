from __future__ import print_function
import json
import os

try:
    from jsonschema import SchemaError
    from jsonschema import Draft3Validator as Validator
except ImportError as e:
    verbose_msg = """

    IPython depends on the jsonschema package: https://pypi.python.org/pypi/jsonschema
    
    Please install it first.
    """
    raise ImportError(str(e) + verbose_msg)

try:
    import jsonpointer as jsonpointer
except ImportError as e:
    verbose_msg = """

    IPython depends on the jsonpointer package: https://pypi.python.org/pypi/jsonpointer
    
    Please install it first.
    """
    raise ImportError(str(e) + verbose_msg)

from IPython.utils.py3compat import iteritems


from .current import nbformat, nbformat_schema
schema_path = os.path.join(
    os.path.dirname(__file__), "v%d" % nbformat, nbformat_schema)


def isvalid(nbjson):
    """Checks whether the given notebook JSON conforms to the current
    notebook format schema. Returns True if the JSON is valid, and
    False otherwise.

    To see the individual errors that were encountered, please use the
    `validate` function instead.

    """

    errors = validate(nbjson)
    return errors == []


def validate(nbjson):
    """Checks whether the given notebook JSON conforms to the current
    notebook format schema, and returns the list of errors.

    """

    # load the schema file
    with open(schema_path, 'r') as fh:
        schema_json = json.load(fh)

    # resolve internal references
    schema = resolve_ref(schema_json)
    schema = jsonpointer.resolve_pointer(schema, '/notebook')

    # count how many errors there are
    v = Validator(schema)
    errors = list(v.iter_errors(nbjson))
    return errors


def resolve_ref(json, schema=None):
    """Resolve internal references within the given JSON. This essentially
    means that dictionaries of this form:

    {"$ref": "/somepointer"}

    will be replaced with the resolved reference to `/somepointer`.
    This only supports local reference to the same JSON file.

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
                if len(json) != 1:
                    raise SchemaError(
                        "objects containing a $ref should only have one item")
                pointer = jsonpointer.resolve_pointer(schema, ref)
                resolved = resolve_ref(pointer, schema=schema)

            else:
                resolved[key] = resolve_ref(ref, schema=schema)

    # otherwise it's a normal object, so just return it
    else:
        resolved = json

    return resolved
