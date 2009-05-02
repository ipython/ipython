from IPython.demo import Demo,IPythonDemo,LineDemo,IPythonLineDemo,ClearDemo,ClearIPDemo
import tempfile, os, StringIO, shutil

"""This is meant to be run from the IPython prompt:
run demo-exercizer.py
-- it will created demo objects of the example that is
embedded in demo.py in a number of ways and allow you
to see how they work, just follow the printed directions."""

example1 = """
'''A simple interactive demo to illustrate the use of IPython's Demo class.'''

print 'Hello, welcome to an interactive IPython demo.'

# The mark below defines a block boundary, which is a point where IPython will
# stop execution and return to the interactive prompt. The dashes are actually
# optional and used only as a visual aid to clearly separate blocks while
# editing the demo code.
# <demo> stop

x = 1
y = 2

# <demo> stop

# the mark below makes this block as silent
# <demo> silent

print 'This is a silent block, which gets executed but not printed.'

# <demo> stop
# <demo> auto
print 'This is an automatic block.'
print 'It is executed without asking for confirmation, but printed.'
z = x+y

print 'z=',x

# <demo> stop
# This is just another normal block.
print 'z is now:', z

print 'bye!'
"""
fp = tempfile.mkdtemp(prefix = 'DemoTmp')
fd, filename = tempfile.mkstemp(prefix = 'demoExample1File', suffix = '.py', dir = fp)
f = os.fdopen(fd, 'wt')

f.write(example1)
f.close()

my_d = Demo(filename)
my_cd = ClearDemo(filename)

fobj = StringIO.StringIO(example1)
str_d = Demo(fobj, title='via stringio')
#~ def tmpcleanup():
    #~ global my_d, my_cd, fp
    #~ del my_d
    #~ del my_cd    
    #~ shutil.rmtree(fp, False)

print '''
The example that is embeded in demo.py file has been used to create 
the following 3 demos, and should now be available to use:
   my_d()    -- created from a file
   my_cd()   -- created from a file, a ClearDemo
   str_d()   -- same as above, but created via a stringi\o object 
Call by typing their name, (with parentheses), at the 
ipython prompt, interact with the block, then call again
to run the next block.
'''
# call tmpcleanup to delete the temporary files created. -not implemented

