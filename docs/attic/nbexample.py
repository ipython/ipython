from notebook.markup import rest

rest.title('This is a Python Notebook')
rest.heading(1,'A first-level heading')
rest.text("""\
Some plain text, without any special formatting.

Below, we define a simple function to add two numbers.""")

def add(x,y):
    return x+y
