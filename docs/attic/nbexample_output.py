from notebook.markup import rest

rest.title('This is a Python Notebook')
rest.text("""\
Some plain text, without any special formatting.

Below, we define a simple function to add two numbers.""")

def add(x,y):
    return x+y

rest.text("Let's use it with x=2,y=3:")
# This simply means that all code until the next markup call is to be executed
# as a single call.  The editing screen should mark the whole group of lines
# with a single In[NN] tag (like IPython does, but with multi-line capabilities)
rest.input()
add(2,3)
# This output would appear on-screen (in the editing window) simply marked
# with an Out[NN] tag
rest.output("5")
