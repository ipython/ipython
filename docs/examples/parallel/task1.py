# <nbformat>2</nbformat>

# <markdowncell>

# # Simple task farming example

# <codecell>

from IPython.parallel import Client

# <markdowncell>

# A `Client.load_balanced_view` is used to get the object used for working with load balanced tasks.

# <codecell>

rc = Client()
v = rc.load_balanced_view()

# <markdowncell>

# Set the variable `d` on all engines:

# <codecell>

rc[:]['d'] = 30

# <markdowncell>

# Define a function that will be our task:

# <codecell>

def task(a):
    return a, 10*d, a*10*d

# <markdowncell>

# Run the task once:

# <codecell>

ar = v.apply(task, 5)

# <markdowncell>

# Print the results:

# <codecell>

print "a, b, c: ", ar.get()

