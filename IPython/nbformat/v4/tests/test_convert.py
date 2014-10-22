# -*- coding: utf-8 -*-
import copy

import nose.tools as nt

from IPython.nbformat import validate
from .. import convert

from . import nbexamples
from IPython.nbformat.v3.tests import nbexamples as v3examples
from IPython.nbformat import v3, v4

def test_upgrade_notebook():
    nb03 = copy.deepcopy(v3examples.nb0)
    validate(nb03)
    nb04 = convert.upgrade(nb03)
    validate(nb04)

def test_downgrade_notebook():
    nb04 = copy.deepcopy(nbexamples.nb0)
    validate(nb04)
    nb03 = convert.downgrade(nb04)
    validate(nb03)

def test_upgrade_heading():
    v3h = v3.new_heading_cell
    v4m = v4.new_markdown_cell
    for v3cell, expected in [
        (
            v3h(source='foo', level=1),
            v4m(source='# foo'),
        ),
        (
            v3h(source='foo\nbar\nmulti-line\n', level=4),
            v4m(source='#### foo bar multi-line'),
        ),
        (
            v3h(source=u'ünìcö∂e–cønvërsioñ', level=4),
            v4m(source=u'#### ünìcö∂e–cønvërsioñ'),
        ),
    ]:
        upgraded = convert.upgrade_cell(v3cell)
        nt.assert_equal(upgraded, expected)

def test_downgrade_heading():
    v3h = v3.new_heading_cell
    v4m = v4.new_markdown_cell
    v3m = lambda source: v3.new_text_cell('markdown', source)
    for v4cell, expected in [
        (
            v4m(source='# foo'),
            v3h(source='foo', level=1),
        ),
        (
            v4m(source='#foo'),
            v3h(source='foo', level=1),
        ),
        (
            v4m(source='#\tfoo'),
            v3h(source='foo', level=1),
        ),
        (
            v4m(source='# \t  foo'),
            v3h(source='foo', level=1),
        ),
        (
            v4m(source='# foo\nbar'),
            v3m(source='# foo\nbar'),
        ),
    ]:
        downgraded = convert.downgrade_cell(v4cell)
        nt.assert_equal(downgraded, expected)
