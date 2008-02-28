""" An example of one way to embed IPython in your own application 

This basically means starting up IPython with some of your programs objects visible in the IPython 
user namespace.

"""

import sys
sys.path.append('..')

import IPython.ipapi

my_ns = dict(a=10)

ses = IPython.ipapi.make_session(my_ns)

# Now get the ipapi instance, to be stored somewhere in your program for manipulation of the running 
# IPython session. See http://ipython.scipy.org/moin/IpythonExtensionApi

ip = ses.IP.getapi()   

# let's play with the ipapi a bit, creating a magic function for a soon-to-be-started IPython
def mymagic_f(self,s):
    print "mymagic says",s

ip.expose_magic("mymagic",mymagic_f)

# And finally, start the IPython interaction! This will block until you say Exit.

ses.mainloop()

print "IPython session finished! namespace content:",my_ns
