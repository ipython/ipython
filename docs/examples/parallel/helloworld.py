# <nbformat>2</nbformat>

# <markdowncell>

# # Distributed hello world
# 
# Originally by Ken Kinder (ken at kenkinder dom com)

# <codecell>

from IPython.parallel import Client

# <codecell>

rc = Client()
view = rc.load_balanced_view()

# <codecell>

def sleep_and_echo(t, msg):
    import time
    time.sleep(t)
    return msg

# <codecell>

world = view.apply_async(sleep_and_echo, 3, 'World!')
hello = view.apply_async(sleep_and_echo, 2, 'Hello')

# <codecell>

print "Submitted tasks:", hello.msg_ids, world.msg_ids
print hello.get(), world.get()

