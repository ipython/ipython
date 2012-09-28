"""
An implementation of JSON Schema for Python

The main functionality is provided by the :class:`Validator` class, with the
:function:`validate` function being the most common way to quickly create a
:class:`Validator` object and validate an instance with a given schema.

The :class:`Validator` class generally attempts to be as strict as possible
under the JSON Schema specification. See its docstring for details.

"""

from __future__ import division, unicode_literals

import collections
import itertools
import operator
import re
import sys
import warnings


PY3 = sys.version_info[0] >= 3

if PY3:
    basestring = unicode = str
    iteritems = operator.methodcaller("items")
else:
    from itertools import izip as zip
    iteritems = operator.methodcaller("iteritems")


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


__version__ = "0.5"


DRAFT_3 = {
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

EPSILON = 10 ** -15


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


class Validator(object):
    """
    A JSON Schema validator.

    """

    DEFAULT_TYPES = {
        "array" : list, "boolean" : bool, "integer" : int, "null" : type(None),
        "number" : (int, float), "object" : dict, "string" : basestring,
    }

    def __init__(
        self, version=DRAFT_3, unknown_type="skip",
        unknown_property="skip", types=(),
    ):
        """
        Initialize a Validator.

        ``version`` specifies which version of the JSON Schema specification to
        validate with. Currently only draft-03 is supported (and is the
        default).

        ``unknown_type`` and ``unknown_property`` control what to do when an
        unknown type (resp. property) is encountered. By default, the
        metaschema is respected (which e.g. for draft 3 allows a schema to have
        additional properties), but if for some reason you want to modify this
        behavior, you can do so without needing to modify the metaschema by
        passing ``"error"`` or ``"warn"`` to these arguments.

        ``types`` is a mapping (or iterable of 2-tuples) containing additional
        types or alternate types to verify via the 'type' property. For
        instance, the default types for the 'number' JSON Schema type are
        ``int`` and ``float``.  To override this behavior (e.g. for also
        allowing ``decimal.Decimal``), pass ``types={"number" : (int, float,
        decimal.Decimal)} *including* the default types if so desired, which
        are fairly obvious but can be accessed via ``Validator.DEFAULT_TYPES``
        if necessary.

        """

        self._unknown_type = unknown_type
        self._unknown_property = unknown_property
        self._version = version

        self._types = dict(self.DEFAULT_TYPES)
        self._types.update(types)
        self._types["any"] = tuple(self._types.values())

    def is_type(self, instance, type):
        """
        Check if an ``instance`` is of the provided ``type``.

        """

        py_type = self._types.get(type)

        if py_type is None:
            return self.schema_error(
                self._unknown_type, "%r is not a known type" % (type,)
            )

        # the only thing we're careful about here is evading bool inheriting
        # from int, so let's be even dirtier than usual

        elif (
            # it's not a bool, so no worries
            not isinstance(instance, bool) or

            # it is a bool, but we're checking for a bool, so no worries
            (
                py_type is bool or
                isinstance(py_type, tuple) and bool in py_type
            )

        ):
            return isinstance(instance, py_type)

    def schema_error(self, level, msg):
        if level == "skip":
            return
        elif level == "warn":
            warnings.warn(msg)
        else:
            raise SchemaError(msg)

    def is_valid(self, instance, schema, meta_validate=True):
        """
        Check if the ``instance`` is valid under the ``schema``.

        Returns a bool indicating whether validation succeeded.

        """

        error = next(self.iter_errors(instance, schema, meta_validate), None)
        return error is None

    def iter_errors(self, instance, schema, meta_validate=True):
        """
        Lazily yield each of the errors in the given ``instance``.

        If you are unsure whether your schema itself is valid,
        ``meta_validate`` will first validate that the schema is valid before
        attempting to validate the instance. ``meta_validate`` is ``True`` by
        default, since setting it to ``False`` can lead to confusing error
        messages with an invalid schema. If you're sure your schema is in fact
        valid, or don't care, feel free to set this to ``False``. The meta
        validation will be done using the appropriate ``version``.

        """

        if meta_validate:
            for error in self.iter_errors(
                schema, self._version, meta_validate=False
            ):
                s = SchemaError(error.message)
                s.path = error.path
                s.validator = error.validator
                # I think we're safer raising these always, not yielding them
                raise s

        for k, v in iteritems(schema):
            validator = getattr(self, "validate_%s" % (k.lstrip("$"),), None)

            if validator is None:
                errors = self.unknown_property(k, instance, schema)
            else:
                errors = validator(v, instance, schema)

            for error in errors or ():
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

    def unknown_property(self, property, instance, schema):
        self.schema_error(
            self._unknown_property,
            "%r is not a known schema property" % (property,)
        )

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
            yield ValidationError(
                "%r is not of type %r" % (instance, _delist(types))
            )

    def validate_properties(self, properties, instance, schema):
        if not self.is_type(instance, "object"):
            return

        for property, subschema in iteritems(properties):
            if property in instance:
                dependencies = _list(subschema.get("dependencies", []))
                if self.is_type(dependencies, "object"):
                    for error in self.iter_errors(
                        instance, dependencies, meta_validate=False
                    ):
                        yield error
                else:
                    for dependency in dependencies:
                        if dependency not in instance:
                            yield ValidationError(
                            "%r is a dependency of %r" % (dependency, property)
                            )

                for error in self.iter_errors(
                    instance[property], subschema, meta_validate=False
                ):
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
                    for error in self.iter_errors(
                        v, subschema, meta_validate=False
                    ):
                        yield error

    def validate_additionalProperties(self, aP, instance, schema):
        if not self.is_type(instance, "object"):
            return

        # no viewkeys in <2.7, and pypy seems to fail on vk - vk anyhow, so...
        extras = set(instance) - set(schema.get("properties", {}))

        if self.is_type(aP, "object"):
            for extra in extras:
                for error in self.iter_errors(
                    instance[extra], aP, meta_validate=False
                ):
                    yield error
        elif not aP and extras:
            error = "Additional properties are not allowed (%s %s unexpected)"
            yield ValidationError(error % _extras_msg(extras))

    def validate_items(self, items, instance, schema):
        if not self.is_type(instance, "array"):
            return

        if self.is_type(items, "object"):
            for index, item in enumerate(instance):
                for error in self.iter_errors(
                    item, items, meta_validate=False
                ):
                    error.path.append(index)
                    yield error
        else:
            for (index, item), subschema in zip(enumerate(instance), items):
                for error in self.iter_errors(
                    item, subschema, meta_validate=False
                ):
                    error.path.append(index)
                    yield error

    def validate_additionalItems(self, aI, instance, schema):
        if not self.is_type(instance, "array"):
            return

        if self.is_type(aI, "object"):
            for item in instance[len(schema):]:
                for error in self.iter_errors(item, aI, meta_validate=False):
                    yield error
        elif not aI and len(instance) > len(schema.get("items", [])):
            error = "Additional items are not allowed (%s %s unexpected)"
            yield ValidationError(
                error % _extras_msg(instance[len(schema) - 1:])
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
            failed = (mod > EPSILON) and (dB - mod) > EPSILON
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
            for error in self.iter_errors(
                instance, subschema, meta_validate=False
            ):
                yield error


for no_op in [                                  # handled in:
    "dependencies", "required",                 # properties
    "exclusiveMinimum", "exclusiveMaximum",     # min*/max*
    "default", "description", "format", "id",   # no validation needed
    "links", "name", "title",
    "ref", "schema",                            # not yet supported
]:
    setattr(Validator, "validate_" + no_op, lambda *args, **kwargs : None)


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


def _extras_msg(extras):
    """
    Create an error message for extra items or properties.

    """

    if len(extras) == 1:
        verb = "was"
    else:
        verb = "were"
    return ", ".join(repr(extra) for extra in extras), verb


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


def validate(
    instance, schema, meta_validate=True, cls=Validator, *args, **kwargs
):
    """
    Validate an ``instance`` under the given ``schema``.

    By default, the :class:`Validator` class from this module is used to
    perform the validation. To use another validator, pass it into the ``cls``
    argument.

    Any other provided positional and keyword arguments will be provided to the
    ``cls``. See the :class:`Validator` class' docstring for details on the
    arguments it accepts.

    """

    validator = cls(*args, **kwargs)
    validator.validate(instance, schema, meta_validate=meta_validate)
