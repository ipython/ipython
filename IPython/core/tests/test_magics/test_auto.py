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
    
    def test_toggle_1(self, ipython):
        ipython.run_line_magic('automagic', '')
        ipython.run_cell('1 + 1')
        res = ipython.run_cell('recall')
        assert ipython.rl_next_input == '2'

    def test_toggle_2(self, ipython):
        ipython.run_line_magic('automagic', '')
        ipython.run_cell('1 + 1')
        res = ipython.run_cell('recall')
        assert isinstance(res.error_in_exec, Exception)

class TestAutocall:
    def test_invalid_input(self, ipython):
        ipython.run_line_magic('autocall', 'random')
    
    def test_exact_value(self, ipython):
        pass
    
    def test_toggle_already_set(self, ipython):
        pass
    
    def test_toggle_not_set(slef, ipython):
        pass