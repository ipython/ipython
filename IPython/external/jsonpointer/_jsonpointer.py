# -*- coding: utf-8 -*-
#
# python-json-pointer - An implementation of the JSON Pointer syntax
# https://github.com/stefankoegl/python-json-pointer
#
# Copyright (c) 2011 Stefan Kögl <stefan@skoegl.net>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

""" Identify specific nodes in a JSON document according to
http://tools.ietf.org/html/draft-ietf-appsawg-json-pointer-04 """

# Will be parsed by setup.py to determine package metadata
__author__ = 'Stefan K�gl <stefan@skoegl.net>'
__version__ = '0.3'
__website__ = 'https://github.com/stefankoegl/python-json-pointer'
__license__ = 'Modified BSD License'


import urllib
from itertools import tee, izip


class JsonPointerException(Exception):
    pass


_nothing = object()


def resolve_pointer(doc, pointer, default=_nothing):
    """
    Resolves pointer against doc and returns the referenced object

    >>> obj = {"foo": {"anArray": [ {"prop": 44}], "another prop": {"baz": "A string" }}}

    >>> resolve_pointer(obj, '') == obj
    True

    >>> resolve_pointer(obj, '/foo') == obj['foo']
    True

    >>> resolve_pointer(obj, '/foo/another%20prop') == obj['foo']['another prop']
    True

    >>> resolve_pointer(obj, '/foo/another%20prop/baz') == obj['foo']['another prop']['baz']
    True

    >>> resolve_pointer(obj, '/foo/anArray/0') == obj['foo']['anArray'][0]
    True

    >>> resolve_pointer(obj, '/some/path', None) == None
    True

    """

    pointer = JsonPointer(pointer)
    return pointer.resolve(doc, default)


def set_pointer(doc, pointer, value):
    """
    Set a field to a given value

    The field is indicates by a base location that is given in the constructor,
    and an optional relative location in the call to set. If the path doesn't
    exist, it is created if possible

    >>> obj = {"foo": 2}
    >>> pointer = JsonPointer('/bar')
    >>> pointer.set(obj, 'one', '0')
    >>> pointer.set(obj, 'two', '1')
    >>> obj
    {'foo': 2, 'bar': ['one', 'two']}

    >>> obj = {"foo": 2, "bar": []}
    >>> pointer = JsonPointer('/bar')
    >>> pointer.set(obj, 5, '0/x')
    >>> obj
    {'foo': 2, 'bar': [{'x': 5}]}

    >>> obj = {'foo': 2, 'bar': [{'x': 5}]}
    >>> pointer = JsonPointer('/bar/0')
    >>> pointer.set(obj, 10, 'y/0')
    >>> obj
    {'foo': 2, 'bar': [{'y': [10], 'x': 5}]}
    """

    pointer = JsonPointer(pointer)
    pointer.set(doc, value)


class JsonPointer(object):
    """ A JSON Pointer that can reference parts of an JSON document """

    def __init__(self, pointer):
        parts = pointer.split('/')
        if parts.pop(0) != '':
            raise JsonPointerException('location must starts with /')

        parts = map(urllib.unquote, parts)
        parts = [part.replace('~1', '/') for part in parts]
        parts = [part.replace('~0', '~') for part in parts]
        self.parts = parts



    def resolve(self, doc, default=_nothing):
        """Resolves the pointer against doc and returns the referenced object"""

        for part in self.parts:

            try:
                doc = self.walk(doc, part)
            except JsonPointerException:
                if default is _nothing:
                    raise
                else:
                    return default

        return doc


    get = resolve


    def set(self, doc, value, path=None):
        """ Sets a field of doc to value

        The location of the field is given by the pointers base location and
        the optional path which is relative to the base location """

        fullpath = list(self.parts)

        if path:
            fullpath += path.split('/')


        for part, nextpart in pairwise(fullpath):
            try:
                doc = self.walk(doc, part)
            except JsonPointerException:
                step_val = [] if nextpart.isdigit() else {}
                doc = self._set_value(doc, part, step_val)

        self._set_value(doc, fullpath[-1], value)


    @staticmethod
    def _set_value(doc, part, value):
        part = int(part) if part.isdigit() else part

        if isinstance(doc, dict):
            doc[part] = value

        if isinstance(doc, list):
            if len(doc) < part:
                doc[part] = value

            if len(doc) == part:
                doc.append(value)

            else:
                raise IndexError

        return doc[part]


    def walk(self, doc, part):
        """ Walks one step in doc and returns the referenced part """

        # Its not clear if a location "1" should be considered as 1 or "1"
        # We prefer the integer-variant if possible
        part_variants = self._try_parse(part) + [part]

        for variant in part_variants:
            try:
                return doc[variant]
            except:
                continue

        raise JsonPointerException("'%s' not found in %s" % (part, doc))


    @staticmethod
    def _try_parse(val, cls=int):
        try:
            return [cls(val)]
        except:
            return []



def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)
__author__ = 'Stefan Kögl <stefan@skoegl.net>'
