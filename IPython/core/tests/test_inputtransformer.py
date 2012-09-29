import unittest
import nose.tools as nt

from IPython.testing import tools as tt
from IPython.utils import py3compat

from IPython.core import inputtransformer
from IPython.core.tests.test_inputsplitter import syntax

def wrap_transform(transformer):
    def transform(inp):
        results = []
        for line in inp:
            res = transformer.push(line)
            if res is not None:
                results.append(res)
        transformer.reset()
        return results
    
    return transform

cellmagic_tests = [
(['%%foo a', None], ["get_ipython().run_cell_magic('foo', 'a', '')"]),
(['%%bar 123', 'hello', ''], ["get_ipython().run_cell_magic('bar', '123', 'hello')"]),
]

def test_transform_cellmagic():
    tt.check_pairs(wrap_transform(inputtransformer.cellmagic), cellmagic_tests)

esctransform_tests = [(i, [py3compat.u_format(ol) for ol in o]) for i,o in [
(['%pdef zip'], ["get_ipython().magic({u}'pdef zip')"]),
(['%abc def \\', 'ghi'], ["get_ipython().magic({u}'abc def  ghi')"]),
(['%abc def \\', 'ghi\\', None], ["get_ipython().magic({u}'abc def  ghi')"]),
]]

def test_transform_escaped():
    tt.check_pairs(wrap_transform(inputtransformer.escaped_transformer), esctransform_tests)

def endhelp_test():
    tt.check_pairs(inputtransformer.transform_help_end.push, syntax['end_help'])

classic_prompt_tests = [
(['>>> a=1'], ['a=1']),
(['>>> a="""','... 123"""'], ['a="""', '123"""']),
(['a="""','... 123"""'], ['a="""', '... 123"""']),
]

def test_classic_prompt():
    tt.check_pairs(wrap_transform(inputtransformer.classic_prompt), classic_prompt_tests)

ipy_prompt_tests = [
(['In [1]: a=1'], ['a=1']),
(['In [2]: a="""','   ...: 123"""'], ['a="""', '123"""']),
(['a="""','   ...: 123"""'], ['a="""', '   ...: 123"""']),
]

def test_ipy_prompt():
    tt.check_pairs(wrap_transform(inputtransformer.ipy_prompt), ipy_prompt_tests)

leading_indent_tests = [
(['    print "hi"'], ['print "hi"']),
(['  for a in range(5):', '    a*2'], ['for a in range(5):', '  a*2']),
(['    a="""','    123"""'], ['a="""', '123"""']),
(['a="""','    123"""'], ['a="""', '    123"""']),
]

def test_leading_indent():
    tt.check_pairs(wrap_transform(inputtransformer.leading_indent), leading_indent_tests)
