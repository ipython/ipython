# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function
import json
import os
import warnings

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

def _relax_additional_properties(obj):
    """relax any `additionalProperties`"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == 'additionalProperties':
                value = True
            else:
                value = _relax_additional_properties(value)
            obj[key] = value
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            obj[i] = _relax_additional_properties(value)
    return obj

def _allow_undefined(schema):
    schema['definitions']['cell']['oneOf'].append(
        {"$ref": "#/definitions/unrecognized_cell"}
    )
    schema['definitions']['output']['oneOf'].append(
        {"$ref": "#/definitions/unrecognized_output"}
    )
    return schema

def get_validator(version=None, version_minor=None):
    """Load the JSON schema into a Validator"""
    if version is None:
        from .. import current_nbformat
        version = current_nbformat

    v = import_item("IPython.nbformat.v%s" % version)
    current_minor = v.nbformat_minor
    if version_minor is None:
        version_minor = current_minor

    version_tuple = (version, version_minor)

    if version_tuple not in validators:
        try:
            v.nbformat_schema
        except AttributeError:
            # no validator
            return None
        schema_path = os.path.join(os.path.dirname(v.__file__), v.nbformat_schema)
        with open(schema_path) as f:
            schema_json = json.load(f)

        if current_minor < version_minor:
            # notebook from the future, relax all `additionalProperties: False` requirements
            schema_json = _relax_additional_properties(schema_json)
            # and allow undefined cell types and outputs
            schema_json = _allow_undefined(schema_json)

        validators[version_tuple] = Validator(schema_json)
    return validators[version_tuple]

def isvalid(nbjson, ref=None, version=None, version_minor=None):
    """Checks whether the given notebook JSON conforms to the current
    notebook format schema. Returns True if the JSON is valid, and
    False otherwise.

    To see the individual errors that were encountered, please use the
    `validate` function instead.
    """
    try:
        validate(nbjson, ref, version, version_minor)
    except ValidationError:
        return False
    else:
        return True


def better_validation_error(error, version, version_minor):
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
                    version=version,
                    version_minor=version_minor,
                )
            except ValidationError as e:
                return better_validation_error(e, version, version_minor)
            except:
                # if it fails for some reason,
                # let the original error through
                pass

    return error


def validate(nbjson, ref=None, version=None, version_minor=None):
    """Checks whether the given notebook JSON conforms to the current
    notebook format schema.

    Raises ValidationError if not valid.
    """
    if version is None:
        from .reader import get_version
        (version, version_minor) = get_version(nbjson)

    validator = get_validator(version, version_minor)

    if validator is None:
        # no validator
        warnings.warn("No schema for validating v%s notebooks" % version, UserWarning)
        return

    try:
        if ref:
            return validator.validate(nbjson, {'$ref' : '#/definitions/%s' % ref})
        else:
            return validator.validate(nbjson)
    except ValidationError as e:
        raise better_validation_error(e, version, version_minor)

