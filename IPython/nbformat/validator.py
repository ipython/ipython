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

from IPython.utils.importstring import import_item


validators = {}

def get_validator(version=None):
    """Load the JSON schema into a Validator"""
    if version is None:
        from .current import nbformat as version

    if version not in validators:
        v = import_item("IPython.nbformat.v%s" % version)
        try:
            v.nbformat_schema
        except AttributeError:
            # no validator
            return None
        schema_path = os.path.join(os.path.dirname(v.__file__), v.nbformat_schema)
        with open(schema_path) as f:
            schema_json = json.load(f)
        validators[version] = Validator(schema_json)
    return validators[version]

def isvalid(nbjson, ref=None, version=None):
    """Checks whether the given notebook JSON conforms to the current
    notebook format schema. Returns True if the JSON is valid, and
    False otherwise.

    To see the individual errors that were encountered, please use the
    `validate` function instead.
    """
    try:
        validate(nbjson, ref, version)
    except ValidationError:
        return False
    else:
        return True


def better_validation_error(error, version):
    """Get better ValidationError on oneOf failures

    oneOf errors aren't informative.
    if it's a cell type or output_type error,
    try validating directly based on the type for a better error message
    """
    key = error.schema_path[-1]
    if key.endswith('Of'):

        ref = None
        if isinstance(error.instance, dict):
            if 'cell_type' in error.instance:
                ref = error.instance['cell_type'] + "_cell"
            elif 'output_type' in error.instance:
                ref = error.instance['output_type']

        if ref:
            try:
                validate(error.instance,
                    ref,
                    version=version
                )
            except ValidationError as e:
                return better_validation_error(e, version)
            except:
                # if it fails for some reason,
                # let the original error through
                pass

    return error


def validate(nbjson, ref=None, version=None):
    """Checks whether the given notebook JSON conforms to the current
    notebook format schema.

    Raises ValidationError if not valid.
    """
    if version is None:
        from .current import nbformat
        version = nbjson.get('nbformat', nbformat)

    validator = get_validator(version)

    if validator is None:
        # no validator
        return

    try:
        if ref:
            return validator.validate(nbjson, {'$ref' : '#/definitions/%s' % ref})
        else:
            return validator.validate(nbjson)
    except ValidationError as e:
        raise better_validation_error(e, version)

