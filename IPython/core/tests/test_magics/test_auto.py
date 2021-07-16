import pytest

from IPython.testing import tools as tt


class TestAutomagic:
    '''Tests for the %automagic line magic.'''

    def test_set_true(self, ipython):
        '''Ensure that the magic works after enabling.'''
        ipython.run_line_magic('automagic', 'true')
        ipython.run_cell('1 + 1')
        ipython.run_cell('recall')
        assert ipython.rl_next_input == '2'

    def test_set_false(self, ipython):
        '''Ensure that the magic doesn't work after disabling.'''
        ipython.run_line_magic('automagic', 'false')
        ipython.run_cell('1 + 1')
        res = ipython.run_cell('recall')
        assert isinstance(res.error_in_exec, NameError)

    def test_toggle(self, ipython):
        '''Ensure that running %automagic without arguments toggles it.'''
        ipython.run_line_magic('automagic', '')
        ipython.run_cell('1 + 1')
        ipython.run_cell('recall')
        assert ipython.rl_next_input == '2'

        ipython.run_line_magic('automagic', '')
        ipython.run_cell('1 + 1')
        res = ipython.run_cell('recall')
        assert isinstance(res.error_in_exec, NameError)


class TestAutocall:
    '''Tests for the %autocall line magic.'''

    @staticmethod
    @pytest.fixture
    def autocall_smart(ipython):
        '''Set %autocall into Smart mode.'''
        previous_value = ipython.autocall
        ipython.run_line_magic('autocall', '1')

        yield

        ipython.run_line_magic('autocall', str(previous_value))

    def test_invalid_input(self, ipython):
        '''Ensure that invalid input is gracefully handled.'''
        with tt.AssertPrints('Valid modes: (0->Off, 1->Smart, 2->Full'):
            ipython.run_line_magic('autocall', 'random')

    def test_exact_value(self, ipython, autocall_smart):
        '''Ensure that the magic can be enabled with the integer value of the mode.'''
        ipython.run_line_magic('autocall', '2')
        out = ipython.run_cell('int "5"').result
        assert out == 5

    def test_toggle_already_set(self, ipython, autocall_smart):
        '''Ensure that Smart mode can be enabled by toggling while in Off mode.'''
        ipython.run_line_magic('autocall', '0')
        ipython.run_line_magic('autocall', '')
        out = ipython.run_cell('int "5"').result
        assert out == 5

    def test_toggle_not_set(self, ipython, autocall_smart):
        '''Ensure that %autocall can be disabled by toggling while in any mode
           except for Off.'''
        ipython.run_line_magic('autocall', '')
        out = ipython.run_cell('print').result
        assert out == print
