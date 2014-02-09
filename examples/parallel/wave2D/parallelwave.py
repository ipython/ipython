#!/usr/bin/env python
"""
A simple python program of solving a 2D wave equation in parallel.
Domain partitioning and inter-processor communication
are done by an object of class ZMQRectPartitioner2D
(which is a subclass of RectPartitioner2D and uses 0MQ via pyzmq)

An example of running the program is (8 processors, 4x2 partition,
200x200 grid cells)::

   $ ipcluster start -n 8 # start 8 engines
   $ python parallelwave.py --grid 200 200 --partition 4 2

See also parallelwave-mpi, which runs the same program, but uses MPI
(via mpi4py) for the inter-engine communication.

Authors
-------

 * Xing Cai
 * Min Ragan-Kelley

"""
#
import sys
import time

from numpy import exp, zeros, newaxis, sqrt

from IPython.external import argparse
from IPython.parallel import Client, Reference

def setup_partitioner(comm, addrs, index, num_procs, gnum_cells, parts):
    """create a partitioner in the engine namespace"""
    global partitioner
    p = ZMQRectPartitioner2D(comm, addrs, my_id=index, num_procs=num_procs)
    p.redim(global_num_cells=gnum_cells, num_parts=parts)
    p.prepare_communication()
    # put the partitioner into the global namespace:
    partitioner=p

def setup_solver(*args, **kwargs):
    """create a WaveSolver in the engine namespace."""
    global solver
    solver = WaveSolver(*args, **kwargs)

def wave_saver(u, x, y, t):
    """save the wave state for each timestep."""
    global u_hist
    global t_hist
    t_hist.append(t)
    u_hist.append(1.0*u)


# main program:
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    paa = parser.add_argument
    paa('--grid', '-g',
        type=int, nargs=2, default=[100,100], dest='grid',
        help="Cells in the grid, e.g. --grid 100 200")
    paa('--partition', '-p',
        type=int, nargs=2, default=None,
        help="Process partition grid, e.g. --partition 4 2 for 4x2")
    paa('-c',
        type=float, default=1.,
        help="Wave speed (I think)")
    paa('-Ly',
        type=float, default=1.,
        help="system size (in y)")
    paa('-Lx',
        type=float, default=1.,
        help="system size (in x)")
    paa('-t', '--tstop',
        type=float, default=1.,
        help="Time units to run")
    paa('--profile',
        type=unicode, default=u'default',
        help="Specify the ipcluster profile for the client to connect to.")
    paa('--save',
        action='store_true',
        help="Add this flag to save the time/wave history during the run.")
    paa('--scalar',
        action='store_true',
        help="Also run with scalar interior implementation, to see vector speedup.")

    ns = parser.parse_args()
    # set up arguments
    grid = ns.grid
    partition = ns.partition
    Lx = ns.Lx
    Ly = ns.Ly
    c = ns.c
    tstop = ns.tstop
    if ns.save:
        user_action = wave_saver
    else:
        user_action = None

    num_cells = 1.0*(grid[0]-1)*(grid[1]-1)
    final_test = True

    # create the Client
    rc = Client(profile=ns.profile)
    num_procs = len(rc.ids)

    if partition is None:
        partition = [num_procs,1]
    else:
        num_procs = min(num_procs, partition[0]*partition[1])

    assert partition[0]*partition[1] == num_procs, "can't map partition %s to %i engines"%(partition, num_procs)

    # construct the View:
    view = rc[:num_procs]
    print("Running %s system on %s processes until %f"%(grid, partition, tstop))

    # functions defining initial/boundary/source conditions
    def I(x,y):
        from numpy import exp
        return 1.5*exp(-100*((x-0.5)**2+(y-0.5)**2))
    def f(x,y,t):
        return 0.0
        # from numpy import exp,sin
        # return 10*exp(-(x - sin(100*t))**2)
    def bc(x,y,t):
        return 0.0

    # initialize t_hist/u_hist for saving the state at each step (optional)
    view['t_hist'] = []
    view['u_hist'] = []

    # set vector/scalar implementation details
    impl = {}
    impl['ic'] = 'vectorized'
    impl['inner'] = 'scalar'
    impl['bc'] = 'vectorized'

    # execute some files so that the classes we need will be defined on the engines:
    view.execute('import numpy')
    view.run('communicator.py')
    view.run('RectPartitioner.py')
    view.run('wavesolver.py')

    # scatter engine IDs
    view.scatter('my_id', range(num_procs), flatten=True)

    # create the engine connectors
    view.execute('com = EngineCommunicator()')

    # gather the connection information into a single dict
    ar = view.apply_async(lambda : com.info)
    peers = ar.get_dict()
    # print peers
    # this is a dict, keyed by engine ID, of the connection info for the EngineCommunicators

    # setup remote partitioner
    # note that Reference means that the argument passed to setup_partitioner will be the
    # object named 'com' in the engine's namespace
    view.apply_sync(setup_partitioner, Reference('com'), peers, Reference('my_id'), num_procs, grid, partition)
    time.sleep(1)
    # convenience lambda to call solver.solve:
    _solve = lambda *args, **kwargs: solver.solve(*args, **kwargs)

    if ns.scalar:
        impl['inner'] = 'scalar'
        # setup remote solvers
        view.apply_sync(setup_solver, I,f,c,bc,Lx,Ly, partitioner=Reference('partitioner'), dt=0,implementation=impl)

        # run first with element-wise Python operations for each cell
        t0 = time.time()
        ar = view.apply_async(_solve, tstop, dt=0, verbose=True, final_test=final_test, user_action=user_action)
        if final_test:
            # this sum is performed element-wise as results finish
            s = sum(ar)
            # the L2 norm (RMS) of the result:
            norm = sqrt(s/num_cells)
        else:
            norm = -1
        t1 = time.time()
        print('scalar inner-version, Wtime=%g, norm=%g'%(t1-t0, norm))

    # run again with faster numpy-vectorized inner implementation:
    impl['inner'] = 'vectorized'
    # setup remote solvers
    view.apply_sync(setup_solver, I,f,c,bc,Lx,Ly,partitioner=Reference('partitioner'), dt=0,implementation=impl)

    t0 = time.time()

    ar = view.apply_async(_solve, tstop, dt=0, verbose=True, final_test=final_test, user_action=user_action)
    if final_test:
        # this sum is performed element-wise as results finish
        s = sum(ar)
        # the L2 norm (RMS) of the result:
        norm = sqrt(s/num_cells)
    else:
        norm = -1
    t1 = time.time()
    print('vector inner-version, Wtime=%g, norm=%g'%(t1-t0, norm))

    # if ns.save is True, then u_hist stores the history of u as a list
    # If the partion scheme is Nx1, then u can be reconstructed via 'gather':
    if ns.save and partition[-1] == 1:
        import matplotlib.pyplot as plt
        view.execute('u_last=u_hist[-1]')
        u_last = view.gather('u_last', block=True)
        plt.pcolor(u_last)
        plt.show()
