""" An example of one way to embed IPython in your own application 

This basically means starting up IPython with some of your programs objects visible in the IPython 
user namespace.

"""

import sys
sys.path.insert(1,'..')

import IPython.ipapi



def test_session(shellclass):
    print "*****************\nLaunch shell for",shellclass
    my_ns = dict(a=10)
    ses = IPython.ipapi.make_session(my_ns, shellclass=shellclass)
    
    # Now get the ipapi instance, to be stored somewhere in your program for manipulation of the running 
    # IPython session. See http://ipython.scipy.org/moin/IpythonExtensionApi
    
    ip = ses.IP.getapi()   
    
    # let's play with the ipapi a bit, creating a magic function for a soon-to-be-started IPython
    def mymagic_f(self,s):
        print "mymagic says",s
    
    ip.expose_magic("mymagic",mymagic_f)
    
    # And finally, start the IPython interaction! This will block until you say Exit.
    
    ses.mainloop()
    
    print "IPython session for shell ",shellclass," finished! namespace content:"
    for k,v in my_ns.items():
        print k,':',str(v)[:80].rstrip()
    
import  IPython.Shell    

def do_test(arg_line):
    test_session(IPython.Shell._select_shell(arg_line.split()))

do_test('')
do_test('ipython -gthread')
do_test('ipython -q4thread')
do_test('ipython -pylab')
do_test('ipython -pylab -gthread')