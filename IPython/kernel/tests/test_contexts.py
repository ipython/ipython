#from __future__ import with_statement

# XXX This file is currently disabled to preserve 2.4 compatibility.

#def test_simple():
if 0:

    # XXX - for now, we need a running cluster to be started separately.  The
    # daemon work is almost finished, and will make much of this unnecessary.
    from IPython.kernel import client
    mec = client.MultiEngineClient(('127.0.0.1',10105))

    try:
        mec.get_ids()
    except ConnectionRefusedError:
        import os, time
        os.system('ipcluster -n 2 &')
        time.sleep(2)
        mec = client.MultiEngineClient(('127.0.0.1',10105))

    mec.block = False

    import itertools
    c = itertools.count()

    parallel = RemoteMultiEngine(mec)

    mec.pushAll()

    ## with parallel as pr:
    ##     # A comment
    ##     remote()  # this means the code below only runs remotely
    ##     print 'Hello remote world'
    ##     x = range(10)
    ##     # Comments are OK
    ##     # Even misindented.
    ##     y = x+1


    ## with pfor('i',sequence) as pr:
    ##     print x[i]

    print pr.x + pr.y
