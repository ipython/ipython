'''Tests of the magics from core.magics.history.'''
import pytest

from IPython.testing import tools as tt


@pytest.fixture
def history(ipython):
    '''Populate the global IPython instance with some lines of history.'''
    ipython.history_manager.reset()   # Clear any existing history.
    cmds = ['a = 1',
            'def b():\n    return a ** 2',
            'print(a, b())',
            '%recall 1']
    for cmd in cmds:
        ipython.run_cell(cmd, store_history=True)

    yield cmds

    ipython.history_manager.reset()
    ipython.user_ns.pop('a')
    ipython.user_ns.pop('b')


class TestRecall:
    '''Tests for the %recall line magic.'''

    def test_no_args(self, ipython):
        ipython.run_cell('1 + 2')
        ipython.run_line_magic('recall', '')
        assert ipython.rl_next_input == '3'

    def test_index_in_history(self, ipython, history):
        ipython.run_line_magic('recall', '1')
        assert ipython.rl_next_input == history[0]

    def test_search_in_namespace(self, ipython, history):
        with tt.AssertNotPrints("Couldn't evaluate or find in history"):
            ip.run_line_magic('recall', 'a')
        assert ipython.rl_next_input == '1'

    def test_search_in_history(self, ipython, history):
        with tt.AssertNotPrints("Couldn't evaluate or find in history"):
            ip.run_line_magic('recall', 'def')
        assert ipython.rl_next_input == history[1]

    def test_search_failed(self, ipython, history):
        with tt.AssertPrints("Couldn't evaluate or find in history"):
            ipython.run_line_magic('recall', 'not_in_ns_or_history')


class TestRerun:
    '''Tests for the %rerun line magic.'''

    error_not_found = 'No lines in history match specification'
    error_integer_expected = '-l option expects a single integer argument'

    def test_lines_zero(self, ipython):
        '''Ensure that the error message about a failed search is not printed
           when 0 last lines are requested.'''
        with tt.AssertNotPrints(self.error_not_found):
            ipython.run_line_magic('rerun', '-l 0')

    def test_lines_non_integer(self, ipython):
        '''Ensure that invalid input is gracefully handled.'''
        with tt.AssertPrints(self.error_integer_expected):
            ipython.run_line_magic('rerun', '-l one')

    def test_search(self, ipython, history):
        '''Ensure that rerunning by search term works.'''
        executing_def = '\n'.join((
            '=== Executing: ===',
            history[1],
            '=== Output: ===',
        ))
        with tt.AssertPrints(executing_def):
            ipython.run_line_magic('rerun', '-g def')

        with tt.AssertPrints(self.error_not_found):
            ipython.run_line_magic('rerun', 'non-existent')

    def test_range(self, ipython, history):
        '''Ensure that one can rerun several lines by specifying a range.'''
        executing_234 = '\n'.join((
            '=== Executing: ===',
            history[1],
            history[2],
            history[3],
            '=== Output: ===',
            '1 1',
        ))
        with tt.AssertPrints(executing_234):
            ipython.run_line_magic('rerun', '2-4')
            assert ipython.rl_next_input == history[0]

    def test_no_args(self, ipython, history):
        '''Ensure that the last line is rerun
           if the magic is called without arguments.'''
        executing_recall = '\n'.join((
            '=== Executing: ===',
            history[3],
            '=== Output: ===',
        ))
        ipython.run_line_magic('rerun', '')
        assert ipython.rl_next_input == history[0]

    @staticmethod
    @pytest.fixture
    def increment_a(ipython):
        '''Define a variable `a` and place a statement
           incrementing that variable in the history.'''
        ipython.history_manager.reset()
        ipython.run_cell('a = 0', store_history=True)
        ipython.run_cell('a += 1', store_history=True)

        yield

        ipython.user_ns.pop('a')

    def test_can_rerun_reruns(self, ipython, increment_a):
        '''Ensure that nothing prevents the user from rerunning
           other calls to %rerun.'''
        ipython.run_cell('%rerun -g a', store_history=True)

        with tt.AssertNotPrints(self.error_not_found):
            ipython.run_line_magic('rerun', '-g rerun')

        assert ipython.user_ns['a'] == 3
