"""Example showing how to merge multiple remote data streams.
"""
# Slightly modified version of:
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/511509

import heapq
from IPython.kernel.error import CompositeError

def mergesort(list_of_lists, key=None):
    """ Perform an N-way merge operation on sorted lists.

    @param list_of_lists: (really iterable of iterable) of sorted elements
    (either by naturally or by C{key})
    @param key: specify sort key function (like C{sort()}, C{sorted()})

    Yields tuples of the form C{(item, iterator)}, where the iterator is the
    built-in list iterator or something you pass in, if you pre-generate the
    iterators.

    This is a stable merge; complexity O(N lg N)

    Examples::

    >>> print list(mergesort([[1,2,3,4],
    ...                      [2,3.25,3.75,4.5,6,7],
    ...                      [2.625,3.625,6.625,9]]))
    [1, 2, 2, 2.625, 3, 3.25, 3.625, 3.75, 4, 4.5, 6, 6.625, 7, 9]

    # note stability
    >>> print list(mergesort([[1,2,3,4],
    ...                      [2,3.25,3.75,4.5,6,7],
    ...                      [2.625,3.625,6.625,9]],
    ...                      key=int))
    [1, 2, 2, 2.625, 3, 3.25, 3.75, 3.625, 4, 4.5, 6, 6.625, 7, 9]


    >>> print list(mergesort([[4, 3, 2, 1],
    ...                      [7, 6, 4.5, 3.75, 3.25, 2],
    ...                      [9, 6.625, 3.625, 2.625]],
    ...                      key=lambda x: -x))
    [9, 7, 6.625, 6, 4.5, 4, 3.75, 3.625, 3.25, 3, 2.625, 2, 2, 1]
    """

    heap = []
    for i, itr in enumerate(iter(pl) for pl in list_of_lists):
        try:
            item = itr.next()
            if key:
                toadd = (key(item), i, item, itr)
            else:
                toadd = (item, i, itr)
            heap.append(toadd)
        except StopIteration:
            pass
    heapq.heapify(heap)

    if key:
        while heap:
            _, idx, item, itr = heap[0]
            yield item
            try:
                item = itr.next()
                heapq.heapreplace(heap, (key(item), idx, item, itr) )
            except StopIteration:
                heapq.heappop(heap)

    else:
        while heap:
            item, idx, itr = heap[0]
            yield item
            try:
                heapq.heapreplace(heap, (itr.next(), idx, itr))
            except StopIteration:
                heapq.heappop(heap)


def remote_iterator(rc,engine,name):
    """Return an iterator on an object living on a remote engine.
    """
    # Check that the object exists on the engine and pin a reference to it
    iter_name = '_%s_rmt_iter_' % name
    rc.execute('%s = iter(%s)' % (iter_name,name), targets=engine)
    tpl = '_tmp = %s.next()' % iter_name
    while True:
        try:
            rc.execute(tpl, targets=engine)
            result = rc.pull('_tmp', targets=engine)[0]
        # This causes the StopIteration exception to be raised.
        except CompositeError, e:
            e.raise_exception()
        else:
            yield result

# Main, interactive testing
if __name__ == '__main__':

    from IPython.kernel import client
    ipc = client.MultiEngineClient()
    print 'Engine IDs:',ipc.get_ids()

    # Make a set of 'sorted datasets'
    a0 = range(5,20)
    a1 = range(10)
    a2 = range(15,25)

    # Now, imagine these had been created in the remote engines by some long
    # computation.  In this simple example, we just send them over into the
    # remote engines.  They will all be called 'a' in each engine.
    ipc.push(dict(a=a0), targets=0)
    ipc.push(dict(a=a1), targets=1)
    ipc.push(dict(a=a2), targets=2)

    # And we now make a local object which represents the remote iterator
    aa0 = remote_iterator(ipc,0,'a')
    aa1 = remote_iterator(ipc,1,'a')
    aa2 = remote_iterator(ipc,2,'a')

    # Let's merge them, both locally and remotely:
    print 'Merge the local datasets:'
    print list(mergesort([a0,a1,a2]))
    
    print 'Locally merge the remote sets:'
    print list(mergesort([aa0,aa1,aa2]))
