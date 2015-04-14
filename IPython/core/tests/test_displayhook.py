from IPython.testing.tools import AssertPrints, AssertNotPrints

ip = get_ipython()

def test_output_displayed():
    """Checking to make sure that output is displayed"""
  
    with AssertPrints('2'):
       ip.run_cell('1+1',store_history=True)
      
    with AssertPrints('2'):
        ip.run_cell('1+1 # comment with a semicolon;',store_history=True)
      
def test_output_quiet():
    """Checking to make sure that output is quiet"""
  
    with AssertNotPrints('2'):
        ip.run_cell('1+1;',store_history=True)
      
    with AssertNotPrints('2'):
        ip.run_cell('1+1; # comment with a semicolon',store_history=True)
