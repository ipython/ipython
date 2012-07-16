"""Example for generating an arbitrary DAG as a dependency map.

This demo uses networkx to generate the graph.

Authors
-------
* MinRK
"""
import networkx as nx
from random import randint, random
from IPython import parallel

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

def submit_jobs(view, G, jobs):
    """Submit jobs via client where G describes the time dependencies."""
    results = {}
    for node in nx.topological_sort(G):
        with view.temp_flags(after=[ results[n] for n in G.predecessors(node) ]):
            results[node] = view.apply(jobs[node])
    return results

def validate_tree(G, results):
    """Validate that jobs executed after their dependencies."""
    for node in G:
        started = results[node].metadata.started
        for parent in G.predecessors(node):
            finished = results[parent].metadata.completed
            assert started > finished, "%s should have happened after %s"%(node, parent)

def main(nodes, edges):
    """Generate a random graph, submit jobs, then validate that the
    dependency order was enforced.
    Finally, plot the graph, with time on the x-axis, and
    in-degree on the y (just for spread).  All arrows must
    point at least slightly to the right if the graph is valid.
    """
    from matplotlib import pyplot as plt
    from matplotlib.dates import date2num
    from matplotlib.cm import gist_rainbow
    print("building DAG")
    G = random_dag(nodes, edges)
    jobs = {}
    pos = {}
    colors = {}
    for node in G:
        jobs[node] = randomwait
    
    client = parallel.Client()
    view = client.load_balanced_view()
    print("submitting %i tasks with %i dependencies"%(nodes,edges))
    results = submit_jobs(view, G, jobs)
    print("waiting for results")
    view.wait()
    print("done")
    for node in G:
        md = results[node].metadata
        start = date2num(md.started)
        runtime = date2num(md.completed) - start
        pos[node] = (start, runtime)
        colors[node] = md.engine_id
    validate_tree(G, results)
    nx.draw(G, pos, node_list=colors.keys(), node_color=colors.values(), cmap=gist_rainbow,
            with_labels=False)
    x,y = zip(*pos.values())
    xmin,ymin = map(min, (x,y))
    xmax,ymax = map(max, (x,y))
    xscale = xmax-xmin
    yscale = ymax-ymin
    plt.xlim(xmin-xscale*.1,xmax+xscale*.1)
    plt.ylim(ymin-yscale*.1,ymax+yscale*.1)
    return G,results

if __name__ == '__main__':
    from matplotlib import pyplot as plt
    # main(5,10)
    main(32,96)
    plt.show()
    
