"""
comp
"""

# The prefilter always ends in a call to some self.handle_X method.  We swap
# all of those out so that we can capture which one was called.

import sys
sys.path.append('..')
import IPython
import IPython.ipapi
    
IPython.Shell.start()

ip = IPython.ipapi.get()

completer = ip.IP.Completer

print completer

def do_test(text, line):
    def get_endix():
        idx = len(line)
        print "Call endidx =>",idx        
        return idx
    def get_line_buffer():
        print "Lbuf =>",line
        return line
    completer.get_line_buffer = get_line_buffer
    completer.get_endidx = get_endix
    l = completer.all_completions(text)
    return l
    
l = do_test ('p', 'print p')
assert 'pow' in l
l = do_test ('p', 'import p')
assert 'pprint' in l