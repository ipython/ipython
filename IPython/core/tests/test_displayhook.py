from IPython.testing.tools import AssertPrints, AssertNotPrints

ip = get_ipython()

def test_output_displayed():
    """Checking to make sure that output is displayed"""
  
    with AssertPrints('2'):
       ip.run_cell('1+1', store_history=True)
      
    with AssertPrints('2'):
        ip.run_cell('1+1 # comment with a semicolon;', store_history=True)

    with AssertPrints('2'):
        ip.run_cell('1+1\n#commented_out_function();', store_history=True)

      
def test_output_quiet():
    """Checking to make sure that output is quiet"""
  
    with AssertNotPrints('2'):
        ip.run_cell('1+1;', store_history=True)
      
    with AssertNotPrints('2'):
        ip.run_cell('1+1; # comment with a semicolon', store_history=True)

    with AssertNotPrints('2'):
        ip.run_cell('1+1;\n#commented_out_function()', store_history=True)

def test_underscore_no_overrite_user():
    ip.run_cell('_ = 42', store_history=True)
    ip.run_cell('1+1', store_history=True)

    with AssertPrints('42'):
        ip.run_cell('print(_)', store_history=True)

    ip.run_cell('del _', store_history=True)
    ip.run_cell('6+6', store_history=True)
    with AssertPrints('12'):
        ip.run_cell('_', store_history=True)


def test_underscore_no_overrite_builtins():
    ip.run_cell("import gettext ; gettext.install('foo')", store_history=True)
    ip.run_cell('3+3', store_history=True)

    with AssertPrints('gettext'):
        ip.run_cell('print(_)', store_history=True)

    ip.run_cell('_ = "userset"', store_history=True)

    with AssertPrints('userset'):
        ip.run_cell('print(_)', store_history=True)
    ip.run_cell('import builtins; del builtins._')

