"""Example of how to define a magic function for extending IPython.

The name of the function *must* begin with magic_. IPython mangles it so
that magic_foo() becomes available as %foo.

The argument list must be *exactly* (self,parameter_s='').

The single string parameter_s will have the user's input. It is the magic
function's responsability to parse this string.

That is, if the user types
>>>%foo a b c

The followinng internal call is generated:
   self.magic_foo(parameter_s='a b c').

To have any functions defined here available as magic functions in your
IPython environment, import this file in your configuration file with an
execfile = this_file.py statement. See the details at the end of the sample
ipythonrc file.  """

# first define a function with the proper form:
def magic_foo(self,parameter_s=''):
    """My very own magic!. (Use docstrings, IPython reads them)."""
    print 'Magic function. Passed parameter is between < >: <'+parameter_s+'>'
    print 'The self object is:',self

# Add the new magic function to the class dict:
from IPython.iplib import InteractiveShell
InteractiveShell.magic_foo = magic_foo

# And remove the global name to keep global namespace clean.  Don't worry, the
# copy bound to IPython stays, we're just removing the global name.
del magic_foo

#********************** End of file <example-magic.py> ***********************
