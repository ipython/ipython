'''Tests of the magics from core.magics.namespace.'''
import math

import pytest

from IPython.testing import tools as tt


@pytest.fixture
def variables(ipython):
    '''Populate the user namespace with variables of different types.
       Returns a list of tuples (variable name, variable value, variable type).
       The variables are removed from the namespace on teardown.'''
    def named_function():
        return 42

    added_variables = [
        ('int1', 1, 'int'),
        ('int2', 5 + 6, 'int'),
        ('float1', 1.0, 'float'),
        ('float2', math.pi, 'float'),
        ('str1', "string", 'str'),
        ('str2', "", 'str'),
        ('function1', lambda: None, 'function'),
        ('function2', named_function, 'function'),
        ('list1', [], 'list'),
        ('list2', [1, 2, 3], 'list'),
        ('list3', [1, '2', None], 'list'),
        ('module', math, 'module'),
    ]

    for var_name, var_value, _var_type in added_variables:
        ipython.user_ns[var_name] = var_value

    yield added_variables

    for var_name, _var_value, _var_type in added_variables:
        ipython.user_ns.pop(var_name)


class TestWhoLs:
    '''Tests for the %who_ls line magic.'''

    def test_no_args_no_vars(self, ipython):
        '''No arguments passed to the magic, no variables in the namespace.'''
        variables = ipython.run_line_magic('who_ls', '')
        assert variables == []

    def test_type_filtering(self, ipython, variables):
        '''Variables of different types in the namespace, filtering based on a certain type.'''
        ints_and_modules = sorted(var[0] for var in variables if var[2] in ('int', 'module'))
        assert ipython.run_line_magic('who_ls', 'int module') == ints_and_modules

    def test_all_vars(self, ipython, variables):
        all_variables = sorted(var[0] for var in variables)
        assert ipython.run_line_magic('who_ls', '') == all_variables
