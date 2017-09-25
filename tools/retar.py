"""
Un-targz and retargz a targz file to ensure reproducible build. 

usage: 

    $ export SOURCE_DATE_EPOCH=$(date +%s)
    ...
    $ python retar.py <tarfile.gz>

The process of creating an sdist can be non-reproducible:
  - directory created during the process get a mtime of the creation date; 
  - gziping files embed the timestamp of fo zip creation. 

This will untar-retar; ensuring that all mtime > SOURCE_DATE_EPOCH will be set
equal to SOURCE_DATE_EPOCH.

"""

import tarfile
import sys
import os
import gzip
import io

if len(sys.argv) > 2:
    raise ValueError('Too many arguments')


timestamp = int(os.environ['SOURCE_DATE_EPOCH'])

old_buf = io.BytesIO()
with open(sys.argv[1], 'rb') as f:
    old_buf.write(f.read())
old_buf.seek(0)
old = tarfile.open(fileobj=old_buf,mode='r:gz')

buf = io.BytesIO()
new = tarfile.open(fileobj=buf, mode='w')

for i,m in enumerate(old):
    data = None
    if m.mtime > timestamp: 
        m.mtime = timestamp
    if m.isdir():
        new.addfile(m)
    else:
        data = old.extractfile(m)
        new.addfile(m, data)
new.close()
old.close()

buf.seek(0)
with gzip.GzipFile(sys.argv[1],"wb", mtime=timestamp) as gzf:
    gzf.write(buf.read())
