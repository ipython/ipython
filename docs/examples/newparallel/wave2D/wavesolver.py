#!/usr/bin/env python
"""
A simple WaveSolver class for evolving the wave equation in 2D.
This works in parallel by using a RectPartitioner object.

Authors
-------

 * Xing Cai
 * Min Ragan-Kelley

"""
import time

from numpy import exp, zeros, newaxis, sqrt, arange

def iseq(start=0, stop=None, inc=1):
    """
    Generate integers from start to (and including!) stop,
    with increment of inc. Alternative to range/xrange.
    """
    if stop is None: # allow isequence(3) to be 0, 1, 2, 3
        # take 1st arg as stop, start as 0, and inc=1
        stop = start; start = 0; inc = 1
    return arange(start, stop+inc, inc)

class WaveSolver(object):
    """
    Solve the 2D wave equation u_tt = u_xx + u_yy + f(x,y,t) with
    u = bc(x,y,t) on the boundary and initial condition du/dt = 0.

    Parallelization by using a RectPartitioner object 'partitioner'

    nx and ny are the total number of global grid cells in the x and y
    directions. The global grid points are numbered as (0,0), (1,0), (2,0),
    ..., (nx,0), (0,1), (1,1), ..., (nx, ny).

    dt is the time step. If dt<=0, an optimal time step is used.

    tstop is the stop time for the simulation.

    I, f are functions: I(x,y), f(x,y,t)

    user_action: function of (u, x, y, t) called at each time
    level (x and y are one-dimensional coordinate vectors).
    This function allows the calling code to plot the solution,
    compute errors, etc.

    implementation: a dictionary specifying how the initial
    condition ('ic'), the scheme over inner points ('inner'),
    and the boundary conditions ('bc') are to be implemented.
    Normally, values are legal: 'scalar' or 'vectorized'.
    'scalar' means straight loops over grid points, while
    'vectorized' means special NumPy vectorized operations.

    If a key in the implementation dictionary is missing, it
    defaults in this function to 'scalar' (the safest strategy).
    Note that if 'vectorized' is specified, the functions I, f,
    and bc must work in vectorized mode. It is always recommended
    to first run the 'scalar' mode and then compare 'vectorized'
    results with the 'scalar' results to check that I, f, and bc
    work.

    verbose: true if a message at each time step is written,
    false implies no output during the simulation.

    final_test: true means the discrete L2-norm of the final solution is
    to be computed.
    """

    def __init__(self, I, f, c, bc, Lx, Ly, partitioner=None, dt=-1,
                user_action=None,
                implementation={'ic': 'vectorized',  # or 'scalar'
                                'inner': 'vectorized',
                                'bc': 'vectorized'}):

        nx = partitioner.global_num_cells[0]  # number of global cells in x dir
        ny = partitioner.global_num_cells[1]  # number of global cells in y dir
        dx = Lx/float(nx)
        dy = Ly/float(ny)
        loc_nx, loc_ny = partitioner.get_num_loc_cells()
        nx = loc_nx; ny = loc_ny              # now use loc_nx and loc_ny instead
        lo_ix0 = partitioner.subd_lo_ix[0]
        lo_ix1 = partitioner.subd_lo_ix[1]
        hi_ix0 = partitioner.subd_hi_ix[0]
        hi_ix1 = partitioner.subd_hi_ix[1]
        x = iseq(dx*lo_ix0, dx*hi_ix0, dx) # local grid points in x dir
        y = iseq(dy*lo_ix1, dy*hi_ix1, dy) # local grid points in y dir
        self.x = x
        self.y = y
        xv = x[:,newaxis]   # for vectorized expressions with f(xv,yv)
        yv = y[newaxis,:]   # -- " --
        if dt <= 0:
            dt = (1/float(c))*(1/sqrt(1/dx**2 + 1/dy**2))  # max time step
        Cx2 = (c*dt/dx)**2;  Cy2 = (c*dt/dy)**2;  dt2 = dt**2  # help variables

        u = zeros((nx+1,ny+1))   # solution array
        u_1 = u.copy()           # solution at t-dt
        u_2 = u.copy()           # solution at t-2*dt

        # preserve for self.solve
        implementation=dict(implementation) # copy

        if 'ic' not in implementation:
            implementation['ic'] = 'scalar'
        if 'bc' not in implementation:
            implementation['bc'] = 'scalar'
        if 'inner' not in implementation:
            implementation['inner'] = 'scalar'

        self.implementation = implementation
        self.Lx = Lx
        self.Ly = Ly
        self.I=I
        self.f=f
        self.c=c
        self.bc=bc
        self.user_action = user_action
        self.partitioner=partitioner

        # set initial condition (pointwise - allows straight if-tests in I(x,y)):
        t=0.0
        if implementation['ic'] == 'scalar':
            for i in xrange(0,nx+1):
                for j in xrange(0,ny+1):
                    u_1[i,j] = I(x[i], y[j])

            for i in xrange(1,nx):
                for j in xrange(1,ny):
                    u_2[i,j] = u_1[i,j] + \
                           0.5*Cx2*(u_1[i-1,j] - 2*u_1[i,j] + u_1[i+1,j]) + \
                           0.5*Cy2*(u_1[i,j-1] - 2*u_1[i,j] + u_1[i,j+1]) + \
                           dt2*f(x[i], y[j], 0.0)

            # boundary values of u_2 (equals u(t=dt) due to du/dt=0)
            i = 0
            for j in xrange(0,ny+1):
                u_2[i,j] = bc(x[i], y[j], t+dt)
            j = 0
            for i in xrange(0,nx+1):
                u_2[i,j] = bc(x[i], y[j], t+dt)
            i = nx
            for j in xrange(0,ny+1):
                u_2[i,j] = bc(x[i], y[j], t+dt)
            j = ny
            for i in xrange(0,nx+1):
                u_2[i,j] = bc(x[i], y[j], t+dt)

        elif implementation['ic'] == 'vectorized':
            u_1 = I(xv,yv)
            u_2[1:nx,1:ny] = u_1[1:nx,1:ny] + \
            0.5*Cx2*(u_1[0:nx-1,1:ny] - 2*u_1[1:nx,1:ny] + u_1[2:nx+1,1:ny]) + \
            0.5*Cy2*(u_1[1:nx,0:ny-1] - 2*u_1[1:nx,1:ny] + u_1[1:nx,2:ny+1]) + \
            dt2*(f(xv[1:nx,1:ny], yv[1:nx,1:ny], 0.0))
            # boundary values (t=dt):
            i = 0;  u_2[i,:] = bc(x[i], y, t+dt)
            j = 0;  u_2[:,j] = bc(x, y[j], t+dt)
            i = nx; u_2[i,:] = bc(x[i], y, t+dt)
            j = ny; u_2[:,j] = bc(x, y[j], t+dt)

        if user_action is not None:
            user_action(u_1, x, y, t)  # allow user to plot etc.
        # print list(self.us[2][2])
        self.us = (u,u_1,u_2)


    def solve(self, tstop, dt=-1, user_action=None, verbose=False, final_test=False):
        t0=time.time()
        f=self.f
        c=self.c
        bc=self.bc
        partitioner = self.partitioner
        implementation = self.implementation
        nx = partitioner.global_num_cells[0]  # number of global cells in x dir
        ny = partitioner.global_num_cells[1]  # number of global cells in y dir
        dx = self.Lx/float(nx)
        dy = self.Ly/float(ny)
        loc_nx, loc_ny = partitioner.get_num_loc_cells()
        nx = loc_nx; ny = loc_ny              # now use loc_nx and loc_ny instead
        x = self.x
        y = self.y
        xv = x[:,newaxis]   # for vectorized expressions with f(xv,yv)
        yv = y[newaxis,:]   # -- " --
        if dt <= 0:
            dt = (1/float(c))*(1/sqrt(1/dx**2 + 1/dy**2))  # max time step
        Cx2 = (c*dt/dx)**2;  Cy2 = (c*dt/dy)**2;  dt2 = dt**2  # help variables
        # id for the four possible neighbor subdomains
        lower_x_neigh = partitioner.lower_neighbors[0]
        upper_x_neigh = partitioner.upper_neighbors[0]
        lower_y_neigh = partitioner.lower_neighbors[1]
        upper_y_neigh = partitioner.upper_neighbors[1]
        u,u_1,u_2 = self.us
        # u_1 = self.u_1

        t = 0.0
        while t <= tstop:
            t_old = t;  t += dt
            if verbose:
                print 'solving (%s version) at t=%g' % \
                      (implementation['inner'], t)
            # update all inner points:
            if implementation['inner'] == 'scalar':
                for i in xrange(1, nx):
                    for j in xrange(1, ny):
                        u[i,j] = - u_2[i,j] + 2*u_1[i,j] + \
                           Cx2*(u_1[i-1,j] - 2*u_1[i,j] + u_1[i+1,j]) + \
                           Cy2*(u_1[i,j-1] - 2*u_1[i,j] + u_1[i,j+1]) + \
                           dt2*f(x[i], y[j], t_old)
            elif implementation['inner'] == 'vectorized':
                u[1:nx,1:ny] = - u_2[1:nx,1:ny] + 2*u_1[1:nx,1:ny] + \
               Cx2*(u_1[0:nx-1,1:ny] - 2*u_1[1:nx,1:ny] + u_1[2:nx+1,1:ny]) + \
               Cy2*(u_1[1:nx,0:ny-1] - 2*u_1[1:nx,1:ny] + u_1[1:nx,2:ny+1]) + \
               dt2*f(xv[1:nx,1:ny], yv[1:nx,1:ny], t_old)

            # insert boundary conditions (if there's no neighbor):
            if lower_x_neigh < 0:
                if implementation['bc'] == 'scalar':
                    i = 0
                    for j in xrange(0, ny+1):
                        u[i,j] = bc(x[i], y[j], t)
                elif implementation['bc'] == 'vectorized':
                    u[0,:] = bc(x[0], y, t)
            if upper_x_neigh < 0:
                if implementation['bc'] == 'scalar':
                    i = nx
                    for j in xrange(0, ny+1):
                        u[i,j] = bc(x[i], y[j], t)
                elif implementation['bc'] == 'vectorized':
                    u[nx,:] = bc(x[nx], y, t)
            if lower_y_neigh < 0:
                if implementation['bc'] == 'scalar':
                    j = 0
                    for i in xrange(0, nx+1):
                        u[i,j] = bc(x[i], y[j], t)
                elif implementation['bc'] == 'vectorized':
                    u[:,0] = bc(x, y[0], t)
            if upper_y_neigh < 0:
                if implementation['bc'] == 'scalar':
                    j = ny
                    for i in xrange(0, nx+1):
                        u[i,j] = bc(x[i], y[j], t)
                elif implementation['bc'] == 'vectorized':
                    u[:,ny] = bc(x, y[ny], t)

            # communication
            partitioner.update_internal_boundary (u)

            if user_action is not None:
                user_action(u, x, y, t)
            # update data structures for next step
            u_2, u_1, u = u_1, u, u_2

        t1 = time.time()
        print 'my_id=%2d, dt=%g, %s version, slice_copy=%s, net Wtime=%g'\
              %(partitioner.my_id,dt,implementation['inner'],\
                partitioner.slice_copy,t1-t0)
        # save the us
        self.us = u,u_1,u_2
        # check final results; compute discrete L2-norm of the solution
        if final_test:
            loc_res = 0.0
            for i in iseq(start=1, stop=nx-1):
                for j in iseq(start=1, stop=ny-1):
                    loc_res += u_1[i,j]**2
            return loc_res
        return dt

