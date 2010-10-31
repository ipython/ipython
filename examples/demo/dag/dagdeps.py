"""Example for generating an arbitrary DAG as a dependency map.

This demo uses networkx to generate the graph.

Authors
-------
* MinRK
"""
import networkx as nx
from random import randint, random
from IPython.zmq.parallel import client as cmod

def randomwait():
    import time
    from random import random
    time.sleep(random())
    return time.time()


def random_dag(nodes, edges):
    """Generate a random Directed Acyclic Graph (DAG) with a given number of nodes and edges."""
    G = nx.DiGraph()
    for i in range(nodes):
        G.add_node(i)
    while edges > 0:
        a = randint(0,nodes-1)
        b=a
        while b==a:
            b = randint(0,nodes-1)
        G.add_edge(a,b)
        if nx.is_directed_acyclic_graph(G):
            edges -= 1
        else:
            # we closed a loop!
            G.remove_edge(a,b)
    return G

def add_children(G, parent, level, n=2):
    """Add children recursively to a binary tree."""
    if level == 0:
        return
    for i in range(n):
        child = parent+str(i)
        G.add_node(child)
        G.add_edge(parent,child)
        add_children(G, child, level-1, n)

def make_bintree(levels):
    """Make a symmetrical binary tree with @levels"""
    G = nx.DiGraph()
    root = '0'
    G.add_node(root)
    add_children(G, root, levels, 2)
    return G

def submit_jobs(client, G, jobs):
    """Submit jobs via client where G describes the time dependencies."""
    msg_ids = {}
    for node in nx.topological_sort(G):
        deps = [ msg_ids[n] for n in G.predecessors(node) ]
        msg_ids[node] = client.apply(jobs[node], after=deps)
    return msg_ids

def validate_tree(G, times):
    """Validate that jobs executed after their dependencies."""
    for node in G:
        t = times[node]
        for parent in G.predecessors(node):
            pt = times[parent]
            assert t > pt, "%s should have happened after %s"%(node, parent)

def main(nodes, edges):
    """Generate a random graph, submit jobs, then validate that the
    dependency order was enforced.
    Finally, plot the graph, with time on the x-axis, and
    in-degree on the y (just for spread).  All arrows must
    point at least slightly to the right if the graph is valid.
    """
    G = random_dag(nodes, edges)
    jobs = {}
    msg_ids = {}
    times = {}
    pos = {}
    for node in G:
        jobs[node] = randomwait
    
    client = cmod.Client('tcp://127.0.0.1:10101')

    msg_ids = submit_jobs(client, G, jobs)
    client.barrier()
    for node in G:
        times[node] = client.results[msg_ids[node]]
        pos[node] = (times[node], G.in_degree(node)+random())
    
    validate_tree(G, times)
    nx.draw(G, pos)
    return G,times,msg_ids

if __name__ == '__main__':
    import pylab
    main(32,128)
    pylab.show()
    