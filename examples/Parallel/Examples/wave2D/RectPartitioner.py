#!/usr/bin/env python
"""A rectangular domain partitioner and associated communication
functionality for solving PDEs in (1D,2D) using FDM
written in the python language

The global solution domain is assumed to be of rectangular shape,
where the number of cells in each direction is stored in nx, ny, nz

The numerical scheme is fully explicit

Authors
-------

 * Xing Cai
 * Min Ragan-Kelley

"""
from __future__ import print_function
import time

from numpy import zeros, ascontiguousarray, frombuffer
try:
    from mpi4py import MPI
except ImportError:
    pass
else:
    mpi = MPI.COMM_WORLD

class RectPartitioner:
    """
    Responsible for a rectangular partitioning of a global domain,
    which is expressed as the numbers of cells in the different
    spatial directions. The partitioning info is expressed as an
    array of integers, each indicating the number of subdomains in
    one spatial direction.
    """

    def __init__(self, my_id=-1, num_procs=-1, \
                 global_num_cells=[], num_parts=[]):
        self.nsd = 0
        self.my_id = my_id
        self.num_procs = num_procs
        self.redim (global_num_cells, num_parts)

    def redim (self, global_num_cells, num_parts):
        nsd_ = len(global_num_cells)
#        print("Inside the redim function, nsd=%d" %nsd_)

        if nsd_<1 | nsd_>3 | nsd_!=len(num_parts):
            print('The input global_num_cells is not ok!')
            return

        self.nsd = nsd_
        self.global_num_cells = global_num_cells
        self.num_parts = num_parts

    def prepare_communication (self):
        """
        Find the subdomain rank (tuple) for each processor and
        determine the neighbor info.
        """
        
        nsd_ = self.nsd
        if nsd_<1:
            print('Number of space dimensions is %d, nothing to do' %nsd_)
            return
        
        self.subd_rank = [-1,-1,-1]
        self.subd_lo_ix = [-1,-1,-1]
        self.subd_hi_ix = [-1,-1,-1]
        self.lower_neighbors = [-1,-1,-1]
        self.upper_neighbors = [-1,-1,-1]

        num_procs = self.num_procs
        my_id = self.my_id

        num_subds = 1
        for i in range(nsd_):
            num_subds = num_subds*self.num_parts[i]
        if my_id==0:
            print("# subds=", num_subds)
            # should check num_subds againt num_procs

        offsets = [1, 0, 0]

        # find the subdomain rank
        self.subd_rank[0] = my_id%self.num_parts[0]
        if nsd_>=2:
            offsets[1] = self.num_parts[0]
            self.subd_rank[1] = my_id/offsets[1]
        if nsd_==3:
            offsets[1] = self.num_parts[0]
            offsets[2] = self.num_parts[0]*self.num_parts[1]
            self.subd_rank[1] = (my_id%offsets[2])/self.num_parts[0]
            self.subd_rank[2] = my_id/offsets[2]
                    
        print("my_id=%d, subd_rank: "%my_id, self.subd_rank)
        if my_id==0:
            print("offsets=", offsets)

        # find the neighbor ids
        for i in range(nsd_):
            rank = self.subd_rank[i]
            if rank>0:
                self.lower_neighbors[i] = my_id-offsets[i]
            if rank<self.num_parts[i]-1:
                self.upper_neighbors[i] = my_id+offsets[i]
                
            k = self.global_num_cells[i]/self.num_parts[i]
            m = self.global_num_cells[i]%self.num_parts[i]
            
            ix = rank*k+max(0,rank+m-self.num_parts[i])
            self.subd_lo_ix[i] = ix
            
            ix = ix+k
            if rank>=(self.num_parts[i]-m):
                ix = ix+1  # load balancing
            if rank<self.num_parts[i]-1:
                ix = ix+1  # one cell of overlap
            self.subd_hi_ix[i] = ix

        print("subd_rank:",self.subd_rank,\
              "lower_neig:", self.lower_neighbors, \
              "upper_neig:", self.upper_neighbors)
        print("subd_rank:",self.subd_rank,"subd_lo_ix:", self.subd_lo_ix, \
              "subd_hi_ix:", self.subd_hi_ix)

        
class RectPartitioner1D(RectPartitioner):
    """
    Subclass of RectPartitioner, for 1D problems
    """
    def prepare_communication (self):
        """
        Prepare the buffers to be used for later communications
        """
        
        RectPartitioner.prepare_communication (self)
        
        if self.lower_neighbors[0]>=0:
            self.in_lower_buffers = [zeros(1, float)]
            self.out_lower_buffers = [zeros(1, float)]
        if self.upper_neighbors[0]>=0:
            self.in_upper_buffers = [zeros(1, float)]
            self.out_upper_buffers = [zeros(1, float)]

    def get_num_loc_cells(self):
        return [self.subd_hi_ix[0]-self.subd_lo_ix[0]]


class RectPartitioner2D(RectPartitioner):
    """
    Subclass of RectPartitioner, for 2D problems
    """
    def prepare_communication (self):
        """
        Prepare the buffers to be used for later communications
        """
        
        RectPartitioner.prepare_communication (self)
        
        self.in_lower_buffers = [[], []]
        self.out_lower_buffers = [[], []]
        self.in_upper_buffers = [[], []]
        self.out_upper_buffers = [[], []]

        size1 = self.subd_hi_ix[1]-self.subd_lo_ix[1]+1
        if self.lower_neighbors[0]>=0:
            self.in_lower_buffers[0] = zeros(size1, float)
            self.out_lower_buffers[0] = zeros(size1, float)
        if self.upper_neighbors[0]>=0:
            self.in_upper_buffers[0] = zeros(size1, float)
            self.out_upper_buffers[0] = zeros(size1, float)

        size0 = self.subd_hi_ix[0]-self.subd_lo_ix[0]+1
        if self.lower_neighbors[1]>=0:
            self.in_lower_buffers[1] = zeros(size0, float)
            self.out_lower_buffers[1] = zeros(size0, float)
        if self.upper_neighbors[1]>=0:
            self.in_upper_buffers[1] = zeros(size0, float)
            self.out_upper_buffers[1] = zeros(size0, float)

    def get_num_loc_cells(self):
        return [self.subd_hi_ix[0]-self.subd_lo_ix[0],\
                self.subd_hi_ix[1]-self.subd_lo_ix[1]]


class MPIRectPartitioner2D(RectPartitioner2D):
    """
    Subclass of RectPartitioner2D, which uses MPI via mpi4py for communication
    """
    
    def __init__(self, my_id=-1, num_procs=-1,
                 global_num_cells=[], num_parts=[],
                 slice_copy=True):
        RectPartitioner.__init__(self, my_id, num_procs,
                                 global_num_cells, num_parts)
        self.slice_copy = slice_copy
        
    def update_internal_boundary (self, solution_array):
        nsd_ = self.nsd
        if nsd_!=len(self.in_lower_buffers) | nsd_!=len(self.out_lower_buffers):
            print("Buffers for communicating with lower neighbors not ready")
            return
        if nsd_!=len(self.in_upper_buffers) | nsd_!=len(self.out_upper_buffers):
            print("Buffers for communicating with upper neighbors not ready")
            return

        loc_nx = self.subd_hi_ix[0]-self.subd_lo_ix[0]
        loc_ny = self.subd_hi_ix[1]-self.subd_lo_ix[1]

        lower_x_neigh = self.lower_neighbors[0]
        upper_x_neigh = self.upper_neighbors[0]
        lower_y_neigh = self.lower_neighbors[1]
        upper_y_neigh = self.upper_neighbors[1]

        # communicate in the x-direction first
        if lower_x_neigh>-1:
            if self.slice_copy:
                self.out_lower_buffers[0] = ascontiguousarray(solution_array[1,:])
            else:
                for i in xrange(0,loc_ny+1):
                    self.out_lower_buffers[0][i] = solution_array[1,i]
            mpi.Isend(self.out_lower_buffers[0], lower_x_neigh)
            
        if upper_x_neigh>-1:
            mpi.Recv(self.in_upper_buffers[0], upper_x_neigh)
            if self.slice_copy:
                solution_array[loc_nx,:] = self.in_upper_buffers[0]
                self.out_upper_buffers[0] = ascontiguousarray(solution_array[loc_nx-1,:])
            else:
                for i in xrange(0,loc_ny+1):
                    solution_array[loc_nx,i] = self.in_upper_buffers[0][i]
                    self.out_upper_buffers[0][i] = solution_array[loc_nx-1,i]
            mpi.Isend(self.out_upper_buffers[0], upper_x_neigh)

        if lower_x_neigh>-1:
            mpi.Recv(self.in_lower_buffers[0], lower_x_neigh)
            if self.slice_copy:
                solution_array[0,:] = self.in_lower_buffers[0]
            else:
                for i in xrange(0,loc_ny+1):
                    solution_array[0,i] = self.in_lower_buffers[0][i]

        # communicate in the y-direction afterwards
        if lower_y_neigh>-1:
            if self.slice_copy:
                self.out_lower_buffers[1] = ascontiguousarray(solution_array[:,1])
            else:
                for i in xrange(0,loc_nx+1):
                    self.out_lower_buffers[1][i] = solution_array[i,1]
            mpi.Isend(self.out_lower_buffers[1], lower_y_neigh)
            
        if upper_y_neigh>-1:
            mpi.Recv(self.in_upper_buffers[1], upper_y_neigh)
            if self.slice_copy:
                solution_array[:,loc_ny] = self.in_upper_buffers[1]
                self.out_upper_buffers[1] = ascontiguousarray(solution_array[:,loc_ny-1])
            else:
                for i in xrange(0,loc_nx+1):
                    solution_array[i,loc_ny] = self.in_upper_buffers[1][i]
                    self.out_upper_buffers[1][i] = solution_array[i,loc_ny-1]
            mpi.Isend(self.out_upper_buffers[1], upper_y_neigh)
            
        if lower_y_neigh>-1:
            mpi.Recv(self.in_lower_buffers[1], lower_y_neigh)
            if self.slice_copy:
                solution_array[:,0] = self.in_lower_buffers[1]
            else:
                for i in xrange(0,loc_nx+1):
                    solution_array[i,0] = self.in_lower_buffers[1][i]

class ZMQRectPartitioner2D(RectPartitioner2D):
    """
    Subclass of RectPartitioner2D, which uses 0MQ via pyzmq for communication
    The first two arguments must be `comm`, an EngineCommunicator object,
    and `addrs`, a dict of connection information for other EngineCommunicator
    objects.
    """

    def __init__(self, comm, addrs, my_id=-1, num_procs=-1,
                 global_num_cells=[], num_parts=[],
                 slice_copy=True):
        RectPartitioner.__init__(self, my_id, num_procs,
                                 global_num_cells, num_parts)
        self.slice_copy = slice_copy
        self.comm = comm # an Engine
        self.addrs = addrs
    
    def prepare_communication(self):
        RectPartitioner2D.prepare_communication(self)
        # connect west/south to east/north
        west_id,south_id = self.lower_neighbors[:2]
        west = self.addrs.get(west_id, None)
        south = self.addrs.get(south_id, None)
        self.comm.connect(south, west)
    
    def update_internal_boundary_x_y (self, solution_array):
        """update the inner boundary with the same send/recv pattern as the MPIPartitioner"""
        nsd_ = self.nsd
        dtype = solution_array.dtype
        if nsd_!=len(self.in_lower_buffers) | nsd_!=len(self.out_lower_buffers):
            print("Buffers for communicating with lower neighbors not ready")
            return
        if nsd_!=len(self.in_upper_buffers) | nsd_!=len(self.out_upper_buffers):
            print("Buffers for communicating with upper neighbors not ready")
            return

        loc_nx = self.subd_hi_ix[0]-self.subd_lo_ix[0]
        loc_ny = self.subd_hi_ix[1]-self.subd_lo_ix[1]

        lower_x_neigh = self.lower_neighbors[0]
        upper_x_neigh = self.upper_neighbors[0]
        lower_y_neigh = self.lower_neighbors[1]
        upper_y_neigh = self.upper_neighbors[1]
        trackers = []
        flags = dict(copy=False, track=False)
        # communicate in the x-direction first
        if lower_x_neigh>-1:
            if self.slice_copy:
                self.out_lower_buffers[0] = ascontiguousarray(solution_array[1,:])
            else:
                for i in xrange(0,loc_ny+1):
                    self.out_lower_buffers[0][i] = solution_array[1,i]
            t = self.comm.west.send(self.out_lower_buffers[0], **flags)
            trackers.append(t)
            
        if upper_x_neigh>-1:
            msg = self.comm.east.recv(copy=False)
            self.in_upper_buffers[0] = frombuffer(msg, dtype=dtype)
            if self.slice_copy:
                solution_array[loc_nx,:] = self.in_upper_buffers[0]
                self.out_upper_buffers[0] = ascontiguousarray(solution_array[loc_nx-1,:])
            else:
                for i in xrange(0,loc_ny+1):
                    solution_array[loc_nx,i] = self.in_upper_buffers[0][i]
                    self.out_upper_buffers[0][i] = solution_array[loc_nx-1,i]
            t = self.comm.east.send(self.out_upper_buffers[0], **flags)
            trackers.append(t)
            

        if lower_x_neigh>-1:
            msg = self.comm.west.recv(copy=False)
            self.in_lower_buffers[0] = frombuffer(msg, dtype=dtype)
            if self.slice_copy:
                solution_array[0,:] = self.in_lower_buffers[0]
            else:
                for i in xrange(0,loc_ny+1):
                    solution_array[0,i] = self.in_lower_buffers[0][i]
        
        # communicate in the y-direction afterwards
        if lower_y_neigh>-1:
            if self.slice_copy:
                self.out_lower_buffers[1] = ascontiguousarray(solution_array[:,1])
            else:
                for i in xrange(0,loc_nx+1):
                    self.out_lower_buffers[1][i] = solution_array[i,1]
            t = self.comm.south.send(self.out_lower_buffers[1], **flags)
            trackers.append(t)
            
            
        if upper_y_neigh>-1:
            msg = self.comm.north.recv(copy=False)
            self.in_upper_buffers[1] = frombuffer(msg, dtype=dtype)
            if self.slice_copy:
                solution_array[:,loc_ny] = self.in_upper_buffers[1]
                self.out_upper_buffers[1] = ascontiguousarray(solution_array[:,loc_ny-1])
            else:
                for i in xrange(0,loc_nx+1):
                    solution_array[i,loc_ny] = self.in_upper_buffers[1][i]
                    self.out_upper_buffers[1][i] = solution_array[i,loc_ny-1]
            t = self.comm.north.send(self.out_upper_buffers[1], **flags)
            trackers.append(t)
            
        if lower_y_neigh>-1:
            msg = self.comm.south.recv(copy=False)
            self.in_lower_buffers[1] = frombuffer(msg, dtype=dtype)
            if self.slice_copy:
                solution_array[:,0] = self.in_lower_buffers[1]
            else:
                for i in xrange(0,loc_nx+1):
                    solution_array[i,0] = self.in_lower_buffers[1][i]
        
        # wait for sends to complete:
        if flags['track']:
            for t in trackers:
                t.wait()

    def update_internal_boundary_send_recv (self, solution_array):
        """update the inner boundary, sending first, then recving"""
        nsd_ = self.nsd
        dtype = solution_array.dtype
        if nsd_!=len(self.in_lower_buffers) | nsd_!=len(self.out_lower_buffers):
            print("Buffers for communicating with lower neighbors not ready")
            return
        if nsd_!=len(self.in_upper_buffers) | nsd_!=len(self.out_upper_buffers):
            print("Buffers for communicating with upper neighbors not ready")
            return

        loc_nx = self.subd_hi_ix[0]-self.subd_lo_ix[0]
        loc_ny = self.subd_hi_ix[1]-self.subd_lo_ix[1]

        lower_x_neigh = self.lower_neighbors[0]
        upper_x_neigh = self.upper_neighbors[0]
        lower_y_neigh = self.lower_neighbors[1]
        upper_y_neigh = self.upper_neighbors[1]
        trackers = []
        flags = dict(copy=False, track=False)
        
        # send in all directions first
        if lower_x_neigh>-1:
            if self.slice_copy:
                self.out_lower_buffers[0] = ascontiguousarray(solution_array[1,:])
            else:
                for i in xrange(0,loc_ny+1):
                    self.out_lower_buffers[0][i] = solution_array[1,i]
            t = self.comm.west.send(self.out_lower_buffers[0], **flags)
            trackers.append(t)
        
        if lower_y_neigh>-1:
            if self.slice_copy:
                self.out_lower_buffers[1] = ascontiguousarray(solution_array[:,1])
            else:
                for i in xrange(0,loc_nx+1):
                    self.out_lower_buffers[1][i] = solution_array[i,1]
            t = self.comm.south.send(self.out_lower_buffers[1], **flags)
            trackers.append(t)
            
        if upper_x_neigh>-1:
            if self.slice_copy:
                self.out_upper_buffers[0] = ascontiguousarray(solution_array[loc_nx-1,:])
            else:
                for i in xrange(0,loc_ny+1):
                    self.out_upper_buffers[0][i] = solution_array[loc_nx-1,i]
            t = self.comm.east.send(self.out_upper_buffers[0], **flags)
            trackers.append(t)
        
        if upper_y_neigh>-1:
            if self.slice_copy:
                self.out_upper_buffers[1] = ascontiguousarray(solution_array[:,loc_ny-1])
            else:
                for i in xrange(0,loc_nx+1):
                    self.out_upper_buffers[1][i] = solution_array[i,loc_ny-1]
            t = self.comm.north.send(self.out_upper_buffers[1], **flags)
            trackers.append(t)
        
        
        # now start receiving
        if upper_x_neigh>-1:
            msg = self.comm.east.recv(copy=False)
            self.in_upper_buffers[0] = frombuffer(msg, dtype=dtype)
            if self.slice_copy:
                solution_array[loc_nx,:] = self.in_upper_buffers[0]
            else:
                for i in xrange(0,loc_ny+1):
                    solution_array[loc_nx,i] = self.in_upper_buffers[0][i]

        if lower_x_neigh>-1:
            msg = self.comm.west.recv(copy=False)
            self.in_lower_buffers[0] = frombuffer(msg, dtype=dtype)
            if self.slice_copy:
                solution_array[0,:] = self.in_lower_buffers[0]
            else:
                for i in xrange(0,loc_ny+1):
                    solution_array[0,i] = self.in_lower_buffers[0][i]
        
        if upper_y_neigh>-1:
            msg = self.comm.north.recv(copy=False)
            self.in_upper_buffers[1] = frombuffer(msg, dtype=dtype)
            if self.slice_copy:
                solution_array[:,loc_ny] = self.in_upper_buffers[1]
            else:
                for i in xrange(0,loc_nx+1):
                    solution_array[i,loc_ny] = self.in_upper_buffers[1][i]
            
        if lower_y_neigh>-1:
            msg = self.comm.south.recv(copy=False)
            self.in_lower_buffers[1] = frombuffer(msg, dtype=dtype)
            if self.slice_copy:
                solution_array[:,0] = self.in_lower_buffers[1]
            else:
                for i in xrange(0,loc_nx+1):
                    solution_array[i,0] = self.in_lower_buffers[1][i]
        
        # wait for sends to complete:
        if flags['track']:
            for t in trackers:
                t.wait()
    
    # use send/recv pattern instead of x/y sweeps
    update_internal_boundary = update_internal_boundary_send_recv

