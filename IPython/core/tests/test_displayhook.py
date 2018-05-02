import sys
from IPython.testing.tools import AssertPrints, AssertNotPrints
from IPython.core.displayhook import CapturingDisplayHook
from IPython.utils.capture import CapturedIO

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

def test_capture_display_hook_format():
    """Tests that the capture display hook conforms to the CapturedIO output format"""
    hook = CapturingDisplayHook(ip)
    hook({"foo": "bar"})
    captured = CapturedIO(sys.stdout, sys.stderr, hook.outputs)
    # Should not raise with RichOutput transformation error
    captured.outputs
