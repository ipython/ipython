import unittest
import nose.tools as nt

from IPython.testing import tools as tt
from IPython.utils import py3compat

from IPython.core import inputtransformer
from IPython.core.tests.test_inputsplitter import syntax

def wrap_transform(transformer):
    def transform(inp):
        for line in inp:
            res = transformer.push(line)
            if res is not None:
                return res
        return transformer.push(None)
    
    return transform

cellmagic_tests = [
(['%%foo a'], "get_ipython().run_cell_magic('foo', 'a', '')"),
(['%%bar 123', 'hello', ''], "get_ipython().run_cell_magic('bar', '123', 'hello')"),
]

def test_transform_cellmagic():
    tt.check_pairs(wrap_transform(inputtransformer.cellmagic), cellmagic_tests)

esctransform_tests = [(i, py3compat.u_format(o)) for i,o in [
(['%pdef zip'], "get_ipython().magic({u}'pdef zip')"),
(['%abc def \\', 'ghi'], "get_ipython().magic({u}'abc def  ghi')"),
]]

def test_transform_escaped():
    tt.check_pairs(wrap_transform(inputtransformer.escaped_transformer), esctransform_tests)

def endhelp_test():
    tt.check_pairs(inputtransformer.transform_help_end.push, syntax['end_help'])
