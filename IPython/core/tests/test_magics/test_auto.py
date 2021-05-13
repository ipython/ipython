from IPython.testing import tools as tt

class TestAutomagic:
    def test_set_true(self, ipython):
        ipython.run_line_magic('automagic', 'true')
        ipython.run_cell('1 + 1')
        res = ipython.run_cell('recall')
        assert ipython.rl_next_input == '2'
    
    def test_set_false(self, ipython):
        ipython.run_line_magic('automagic', 'false')
        ipython.run_cell('1 + 1')
        res = ipython.run_cell('recall')
        assert isinstance(res.error_in_exec, Exception)
    
    def test_toggle(self, ipython):
        ipython.run_line_magic('automagic', '')
        ipython.run_cell('1 + 1')
        res = ipython.run_cell('recall')
        assert ipython.rl_next_input == '2'

        ipython.run_line_magic('automagic', '')
        ipython.run_cell('1 + 1')
        res = ipython.run_cell('recall')    
        assert isinstance(res.error_in_exec, Exception)

class TestAutocall:
    def test_invalid_input(self, ipython):
        with tt.AssertPrints('Valid modes: (0->Off, 1->Smart, 2->Full'):
            ipython.run_line_magic('autocall', 'random')

    def test_exact_value(self, ipython):
        ipython.run_line_magic('autocall', '2')
        out = ipython.run_cell('int "5"').result
        assert out == 5
    
    def test_toggle_already_set(self, ipython):
        ipython.run_line_magic('autocall', '2')
        ipython.run_line_magic('autocall', '0')
        ipython.run_line_magic('autocall', '')
        out = ipython.run_cell('int "5"').result
        assert out == 5
    
    def test_toggle_not_set(self, ipython):
        ipython.run_line_magic('autocall', '')
        out = ipython.run_cell('print').result
        assert out == print