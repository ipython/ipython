from IPython.testing.tools import AssertPrints, AssertNotPrints

def test_output_displayed():
    """Checking to make sure that output is displayed"""
  
    with AssertPrints('2'):
       ip.run_cell('1+1')
      
    with AssertPrints('2'):
        ip.run_cell('1+1 # comment with a semicolon;')
      
def test_output_quiet():
    """Checking to make sure that output is quiet"""
  
    with AssertNotPrints('2'):
        ip.run_cell('1+1;')
      
    with AssertNotPrints('2'):
        ip.run_cell('1+1; # comment with a semicolon')
