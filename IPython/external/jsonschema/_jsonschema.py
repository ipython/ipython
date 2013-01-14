"""
An implementation of JSON Schema for Python

The main functionality is provided by the validator classes for each of the
supported JSON Schema versions.

Most commonly, the :function:`validate` function is the quickest way to simply
validate a given instance under a schema, and will create a validator for you.

"""

from __future__ import division, unicode_literals

import collections
import itertools
import operator
import re
import sys
import warnings


__version__ = "0.7"

FLOAT_TOLERANCE = 10 ** -15
PY3 = sys.version_info[0] >= 3

if PY3:
    basestring = unicode = str
    iteritems = operator.methodcaller("items")
    from urllib.parse import unquote
else:
    from itertools import izip as zip
    iteritems = operator.methodcaller("iteritems")
    from urllib import unquote


class UnknownType(Exception):
    """
    An unknown type was given.

    """


class InvalidRef(Exception):
    """
    An invalid reference was given.

    """


class SchemaError(Exception):
    """
    The provided schema is malformed.

    The same attributes exist for ``SchemaError``s as for ``ValidationError``s.

    """

    validator = None

    def __init__(self, message):
        super(SchemaError, self).__init__(message)
        self.message = message
        self.path = []


class ValidationError(Exception):
    """
    The instance didn't properly validate with the provided schema.

    Relevant attributes are:
        * ``message`` : a human readable message explaining the error
        * ``path`` : a list containing the path to the offending element (or []
                     if the error happened globally) in *reverse* order (i.e.
                     deepest index first).

    """

    # the failing validator will be set externally at whatever recursion level
    # is immediately above the validation failure
    validator = None

    def __init__(self, message):
        super(ValidationError, self).__init__(message)
        self.message = message

        # Any validator that recurses must append to the ValidationError's
        # path (e.g., properties and items)
        self.path = []


class Draft3Validator(object):
    """
    A validator for JSON Schema draft 3.

    """

    DEFAULT_TYPES = {
        "array" : list, "boolean" : bool, "integer" : int, "null" : type(None),
        "number" : (int, float), "object" : dict, "string" : basestring,
    }

    def __init__(self, schema, types=()):
        """
        Initialize a validator.

        ``schema`` should be a *valid* JSON Schema object already converted to
        a native Python object (typically a dict via ``json.load``).

        ``types`` is a mapping (or iterable of 2-tuples) containing additional
        types or alternate types to verify via the 'type' property. For
        instance, the default types for the 'number' JSON Schema type are
        ``int`` and ``float``.  To override this behavior (e.g. for also
        allowing ``decimal.Decimal``), pass ``types={"number" : (int, float,
        decimal.Decimal)} *including* the default types if so desired, which
        are fairly obvious but can be accessed via the ``DEFAULT_TYPES``
        attribute on this class if necessary.

        """

        self._types = dict(self.DEFAULT_TYPES)
        self._types.update(types)
        self._types["any"] = tuple(self._types.values())

        self.schema = schema

    def is_type(self, instance, type):
        """
        Check if an ``instance`` is of the provided (JSON Schema) ``type``.

        """

        if type not in self._types:
            raise UnknownType(type)
        type = self._types[type]

        # bool inherits from int, so ensure bools aren't reported as integers
        if isinstance(instance, bool):
            type = _flatten(type)
            if int in type and bool not in type:
                return False
        return isinstance(instance, type)

    def is_valid(self, instance, _schema=None):
        """
        Check if the ``instance`` is valid under the current schema.

        Returns a bool indicating whether validation succeeded.

        """

        error = next(self.iter_errors(instance, _schema), None)
        return error is None

    @classmethod
    def check_schema(cls, schema):
        """
        Validate a ``schema`` against the meta-schema to see if it is valid.

        """

        for error in cls(cls.META_SCHEMA).iter_errors(schema):
            s = SchemaError(error.message)
            s.path = error.path
            s.validator = error.validator
            # I think we're safer raising these always, not yielding them
            raise s

    def iter_errors(self, instance, _schema=None):
        """
        Lazily yield each of the errors in the given ``instance``.

        """

        if _schema is None:
            _schema = self.schema

        for k, v in iteritems(_schema):
            validator = getattr(self, "validate_%s" % (k.lstrip("$"),), None)

            if validator is None:
                continue

            errors = validator(v, instance, _schema) or ()
            for error in errors:
                # if the validator hasn't already been set (due to recursion)
                # make sure to set it
                error.validator = error.validator or k
                yield error

    def validate(self, *args, **kwargs):
        """
        Validate an ``instance`` under the given ``schema``.

        """

        for error in self.iter_errors(*args, **kwargs):
            raise error

    def validate_type(self, types, instance, schema):
        types = _list(types)

        for type in types:
            # Ouch. Brain hurts. Two paths here, either we have a schema, then
            # check if the instance is valid under it
            if ((
                self.is_type(type, "object") and
                self.is_valid(instance, type)

            # Or we have a type as a string, just check if the instance is that
            # type. Also, HACK: we can reach the `or` here if skip_types is
            # something other than error. If so, bail out.

            ) or (
                self.is_type(type, "string") and
                (self.is_type(instance, type) or type not in self._types)
            )):
                return
        else:
            yield ValidationError(_types_msg(instance, types))

    def validate_properties(self, properties, instance, schema):
        if not self.is_type(instance, "object"):
            return

        for property, subschema in iteritems(properties):
            if property in instance:
                for error in self.iter_errors(instance[property], subschema):
                    error.path.append(property)
                    yield error
            elif subschema.get("required", False):
                error = ValidationError(
                    "%r is a required property" % (property,)
                )
                error.path.append(property)
                error.validator = "required"
                yield error

    def validate_patternProperties(self, patternProperties, instance, schema):
        for pattern, subschema in iteritems(patternProperties):
            for k, v in iteritems(instance):
                if re.match(pattern, k):
                    for error in self.iter_errors(v, subschema):
                        yield error

    def validate_additionalProperties(self, aP, instance, schema):
        if not self.is_type(instance, "object"):
            return

        extras = set(_find_additional_properties(instance, schema))

        if self.is_type(aP, "object"):
            for extra in extras:
                for error in self.iter_errors(instance[extra], aP):
                    yield error
        elif not aP and extras:
            error = "Additional properties are not allowed (%s %s unexpected)"
            yield ValidationError(error % _extras_msg(extras))

    def validate_dependencies(self, dependencies, instance, schema):
        if not self.is_type(instance, "object"):
            return

        for property, dependency in iteritems(dependencies):
            if property not in instance:
                continue

            if self.is_type(dependency, "object"):
                for error in self.iter_errors(instance, dependency):
                    yield error
            else:
                dependencies = _list(dependency)
                for dependency in dependencies:
                    if dependency not in instance:
                        yield ValidationError(
                            "%r is a dependency of %r" % (dependency, property)
                        )

    def validate_items(self, items, instance, schema):
        if not self.is_type(instance, "array"):
            return

        if self.is_type(items, "object"):
            for index, item in enumerate(instance):
                for error in self.iter_errors(item, items):
                    error.path.append(index)
                    yield error
        else:
            for (index, item), subschema in zip(enumerate(instance), items):
                for error in self.iter_errors(item, subschema):
                    error.path.append(index)
                    yield error

    def validate_additionalItems(self, aI, instance, schema):
        if not self.is_type(instance, "array"):
            return
        if not self.is_type(schema.get("items"), "array"):
            return

        if self.is_type(aI, "object"):
            for item in instance[len(schema):]:
                for error in self.iter_errors(item, aI):
                    yield error
        elif not aI and len(instance) > len(schema.get("items", [])):
            error = "Additional items are not allowed (%s %s unexpected)"
            yield ValidationError(
                error % _extras_msg(instance[len(schema.get("items", [])):])
            )

    def validate_minimum(self, minimum, instance, schema):
        if not self.is_type(instance, "number"):
            return

        instance = float(instance)
        if schema.get("exclusiveMinimum", False):
            failed = instance <= minimum
            cmp = "less than or equal to"
        else:
            failed = instance < minimum
            cmp = "less than"

        if failed:
            yield ValidationError(
                "%r is %s the minimum of %r" % (instance, cmp, minimum)
            )

    def validate_maximum(self, maximum, instance, schema):
        if not self.is_type(instance, "number"):
            return

        instance = float(instance)
        if schema.get("exclusiveMaximum", False):
            failed = instance >= maximum
            cmp = "greater than or equal to"
        else:
            failed = instance > maximum
            cmp = "greater than"

        if failed:
            yield ValidationError(
                "%r is %s the maximum of %r" % (instance, cmp, maximum)
            )

    def validate_minItems(self, mI, instance, schema):
        if self.is_type(instance, "array") and len(instance) < mI:
            yield ValidationError("%r is too short" % (instance,))

    def validate_maxItems(self, mI, instance, schema):
        if self.is_type(instance, "array") and len(instance) > mI:
            yield ValidationError("%r is too long" % (instance,))

    def validate_uniqueItems(self, uI, instance, schema):
        if uI and self.is_type(instance, "array") and not _uniq(instance):
            yield ValidationError("%r has non-unique elements" % instance)

    def validate_pattern(self, patrn, instance, schema):
        if self.is_type(instance, "string") and not re.match(patrn, instance):
            yield ValidationError("%r does not match %r" % (instance, patrn))

    def validate_minLength(self, mL, instance, schema):
        if self.is_type(instance, "string") and len(instance) < mL:
            yield ValidationError("%r is too short" % (instance,))

    def validate_maxLength(self, mL, instance, schema):
        if self.is_type(instance, "string") and len(instance) > mL:
            yield ValidationError("%r is too long" % (instance,))

    def validate_enum(self, enums, instance, schema):
        if instance not in enums:
            yield ValidationError("%r is not one of %r" % (instance, enums))

    def validate_divisibleBy(self, dB, instance, schema):
        if not self.is_type(instance, "number"):
            return

        if isinstance(dB, float):
            mod = instance % dB
            failed = (mod > FLOAT_TOLERANCE) and (dB - mod) > FLOAT_TOLERANCE
        else:
            failed = instance % dB

        if failed:
            yield ValidationError("%r is not divisible by %r" % (instance, dB))

    def validate_disallow(self, disallow, instance, schema):
        for disallowed in _list(disallow):
            if self.is_valid(instance, {"type" : [disallowed]}):
                yield ValidationError(
                    "%r is disallowed for %r" % (disallowed, instance)
                )

    def validate_extends(self, extends, instance, schema):
        if self.is_type(extends, "object"):
            extends = [extends]
        for subschema in extends:
            for error in self.iter_errors(instance, subschema):
                yield error

    def validate_ref(self, ref, instance, schema):
        if ref != "#" and not ref.startswith("#/"):
            warnings.warn("jsonschema only supports json-pointer $refs")
            return

        resolved = resolve_json_pointer(self.schema, ref)
        for error in self.iter_errors(instance, resolved):
            yield error


Draft3Validator.META_SCHEMA = {
    "$schema" : "http://json-schema.org/draft-03/schema#",
    "id" : "http://json-schema.org/draft-03/schema#",
    "type" : "object",

    "properties" : {
        "type" : {
            "type" : ["string", "array"],
            "items" : {"type" : ["string", {"$ref" : "#"}]},
            "uniqueItems" : True,
            "default" : "any"
        },
        "properties" : {
            "type" : "object",
            "additionalProperties" : {"$ref" : "#", "type": "object"},
            "default" : {}
        },
        "patternProperties" : {
            "type" : "object",
            "additionalProperties" : {"$ref" : "#"},
            "default" : {}
        },
        "additionalProperties" : {
            "type" : [{"$ref" : "#"}, "boolean"], "default" : {}
        },
        "items" : {
            "type" : [{"$ref" : "#"}, "array"],
            "items" : {"$ref" : "#"},
            "default" : {}
        },
        "additionalItems" : {
            "type" : [{"$ref" : "#"}, "boolean"], "default" : {}
        },
        "required" : {"type" : "boolean", "default" : False},
        "dependencies" : {
            "type" : ["string", "array", "object"],
            "additionalProperties" : {
                "type" : ["string", "array", {"$ref" : "#"}],
                "items" : {"type" : "string"}
            },
            "default" : {}
        },
        "minimum" : {"type" : "number"},
        "maximum" : {"type" : "number"},
        "exclusiveMinimum" : {"type" : "boolean", "default" : False},
        "exclusiveMaximum" : {"type" : "boolean", "default" : False},
        "minItems" : {"type" : "integer", "minimum" : 0, "default" : 0},
        "maxItems" : {"type" : "integer", "minimum" : 0},
        "uniqueItems" : {"type" : "boolean", "default" : False},
        "pattern" : {"type" : "string", "format" : "regex"},
        "minLength" : {"type" : "integer", "minimum" : 0, "default" : 0},
        "maxLength" : {"type" : "integer"},
        "enum" : {"type" : "array", "minItems" : 1, "uniqueItems" : True},
        "default" : {"type" : "any"},
        "title" : {"type" : "string"},
        "description" : {"type" : "string"},
        "format" : {"type" : "string"},
        "maxDecimal" : {"type" : "number", "minimum" : 0},
        "divisibleBy" : {
            "type" : "number",
            "minimum" : 0,
            "exclusiveMinimum" : True,
            "default" : 1
        },
        "disallow" : {
            "type" : ["string", "array"],
            "items" : {"type" : ["string", {"$ref" : "#"}]},
            "uniqueItems" : True
        },
        "extends" : {
            "type" : [{"$ref" : "#"}, "array"],
            "items" : {"$ref" : "#"},
            "default" : {}
        },
        "id" : {"type" : "string", "format" : "uri"},
        "$ref" : {"type" : "string", "format" : "uri"},
        "$schema" : {"type" : "string", "format" : "uri"},
    },
    "dependencies" : {
        "exclusiveMinimum" : "minimum", "exclusiveMaximum" : "maximum"
    },
}


class Validator(Draft3Validator):
    """
    Deprecated: Use :class:`Draft3Validator` instead.

    """

    def __init__(
        self, version=None, unknown_type="skip", unknown_property="skip",
        *args, **kwargs
    ):
        super(Validator, self).__init__({}, *args, **kwargs)
        warnings.warn(
            "Validator is deprecated and will be removed. "
            "Use Draft3Validator instead.",
            DeprecationWarning, stacklevel=2,
        )


class ErrorTree(object):
    """
    ErrorTrees make it easier to check which validations failed.

    """

    def __init__(self, errors=()):
        self.errors = {}
        self._contents = collections.defaultdict(self.__class__)

        for error in errors:
            container = self
            for element in reversed(error.path):
                container = container[element]
            container.errors[error.validator] = error

    def __contains__(self, k):
        return k in self._contents

    def __getitem__(self, k):
        return self._contents[k]

    def __setitem__(self, k, v):
        self._contents[k] = v

    def __iter__(self):
        return iter(self._contents)

    def __len__(self):
        child_errors = sum(len(tree) for _, tree in iteritems(self._contents))
        return len(self.errors) + child_errors

    def __repr__(self):
        return "<%s (%s errors)>" % (self.__class__.__name__, len(self))


def resolve_json_pointer(schema, ref):
    """
    Resolve a local reference ``ref`` within the given root ``schema``.

    ``ref`` should be a local ref whose ``#`` is still present.

    """

    if ref == "#":
        return schema

    parts = ref.lstrip("#/").split("/")

    parts = map(unquote, parts)
    parts = [part.replace('~1', '/').replace('~0', '~') for part in parts]

    try:
        for part in parts:
            schema = schema[part]
    except KeyError:
        raise InvalidRef("Unresolvable json-pointer %r" % ref)
    else:
        return schema


def _find_additional_properties(instance, schema):
    """
    Return the set of additional properties for the given ``instance``.

    Weeds out properties that should have been validated by ``properties`` and
    / or ``patternProperties``.

    Assumes ``instance`` is dict-like already.

    """

    properties = schema.get("properties", {})
    patterns = "|".join(schema.get("patternProperties", {}))
    for property in instance:
        if property not in properties:
            if patterns and re.search(patterns, property):
                continue
            yield property


def _extras_msg(extras):
    """
    Create an error message for extra items or properties.

    """

    if len(extras) == 1:
        verb = "was"
    else:
        verb = "were"
    return ", ".join(repr(extra) for extra in extras), verb


def _types_msg(instance, types):
    """
    Create an error message for a failure to match the given types.

    If the ``instance`` is an object and contains a ``name`` property, it will
    be considered to be a description of that object and used as its type.

    Otherwise the message is simply the reprs of the given ``types``.

    """

    reprs = []
    for type in types:
        try:
            reprs.append(repr(type["name"]))
        except Exception:
            reprs.append(repr(type))
    return "%r is not of type %s" % (instance, ", ".join(reprs))


def _flatten(suitable_for_isinstance):
    """
    isinstance() can accept a bunch of really annoying different types:
        * a single type
        * a tuple of types
        * an arbitrary nested tree of tuples

    Return a flattened tuple of the given argument.

    """

    types = set()

    if not isinstance(suitable_for_isinstance, tuple):
        suitable_for_isinstance = (suitable_for_isinstance,)
    for thing in suitable_for_isinstance:
        if isinstance(thing, tuple):
            types.update(_flatten(thing))
        else:
            types.add(thing)
    return tuple(types)


def _list(thing):
    """
    Wrap ``thing`` in a list if it's a single str.

    Otherwise, return it unchanged.

    """

    if isinstance(thing, basestring):
        return [thing]
    return thing


def _delist(thing):
    """
    Unwrap ``thing`` to a single element if its a single str in a list.

    Otherwise, return it unchanged.

    """

    if (
        isinstance(thing, list) and
        len(thing) == 1
        and isinstance(thing[0], basestring)
    ):
        return thing[0]
    return thing


def _uniq(container):
    """
    Check if all of a container's elements are unique.

    Successively tries first to rely that the elements are hashable, then
    falls back on them being sortable, and finally falls back on brute
    force.

    """

    try:
        return len(set(container)) == len(container)
    except TypeError:
        try:
            sort = sorted(container)
            sliced = itertools.islice(container, 1, None)
            for i, j in zip(container, sliced):
                if i == j:
                    return False
        except (NotImplementedError, TypeError):
            seen = []
            for e in container:
                if e in seen:
                    return False
                seen.append(e)
    return True


def validate(instance, schema, cls=Draft3Validator, *args, **kwargs):
    """
    Validate an ``instance`` under the given ``schema``.

    First verifies that the provided schema is itself valid, since not doing so
    can lead to less obvious failures when validating. If you know it is or
    don't care, use ``YourValidator(schema).validate(instance)`` directly
    instead (e.g. ``Draft3Validator``).

    ``cls`` is a validator class that will be used to validate the instance.
    By default this is a draft 3 validator.  Any other provided positional and
    keyword arguments will be provided to this class when constructing a
    validator.

    """


    meta_validate = kwargs.pop("meta_validate", None)

    if meta_validate is not None:
        warnings.warn(
            "meta_validate is deprecated and will be removed. If you do not "
            "want to validate a schema, use Draft3Validator.validate instead.",
            DeprecationWarning, stacklevel=2,
        )

    if meta_validate is not False:  # yes this is needed since True was default
        cls.check_schema(schema)
    cls(schema, *args, **kwargs).validate(instance)
