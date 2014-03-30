#!/usr/bin/env python
"""
Script for setting up and using [all]reduce with a binary-tree engine interconnect.

usage: `python bintree_script.py`

This spanning tree strategy ensures that a single node node mailbox will never 
receive more that 2 messages at once. This is very important to scale to large 
clusters (e.g. 1000 nodes) since if you have many incoming messages of a couple 
of megabytes you might saturate the network interface of a single node and 
potentially its memory buffers if the messages are not consumed in a streamed 
manner.

Note that the AllReduce scheme implemented with the spanning tree strategy 
impose the aggregation function to be commutative and distributive. It might 
not be the case if you implement the naive gather / reduce / broadcast strategy 
where you can reorder the partial data before performing the reduce.
"""

from IPython.parallel import Client, Reference


# connect client and create views
rc = Client()
rc.block=True
ids = rc.ids

root_id = ids[0]
root = rc[root_id]

view = rc[:]

# run bintree.py script defining bintree functions, etc.
execfile('bintree.py')

# generate binary tree of parents
btree = bintree(ids)

print "setting up binary tree interconnect:"
print_bintree(btree)

view.run('bintree.py')
view.scatter('id', ids, flatten=True)
view['root_id'] = root_id

# create the Communicator objects on the engines
view.execute('com = BinaryTreeCommunicator(id, root = id==root_id )')
pub_url = root.apply_sync(lambda : com.pub_url)

# gather the connection information into a dict
ar = view.apply_async(lambda : com.info)
peers = ar.get_dict()
# this is a dict, keyed by engine ID, of the connection info for the EngineCommunicators

# connect the engines to each other:
def connect(com, peers, tree, pub_url, root_id):
    """this function will be called on the engines"""
    com.connect(peers, tree, pub_url, root_id)

view.apply_sync(connect, Reference('com'), peers, btree, pub_url, root_id)

# functions that can be used for reductions
# max and min builtins can be used as well
def add(a,b):
    """cumulative sum reduction"""
    return a+b

def mul(a,b):
    """cumulative product reduction"""
    return a*b

view['add'] = add
view['mul'] = mul

# scatter some data
data = range(1000)
view.scatter('data', data)

# perform cumulative sum via allreduce
view.execute("data_sum = com.allreduce(add, data, flat=False)")
print "allreduce sum of data on all engines:", view['data_sum']

# perform cumulative sum *without* final broadcast
# when not broadcasting with allreduce, the final result resides on the root node:
view.execute("ids_sum = com.reduce(add, id, flat=True)")
print "reduce sum of engine ids (not broadcast):", root['ids_sum']
print "partial result on each engine:", view['ids_sum']
