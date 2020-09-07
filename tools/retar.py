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

from pathlib import Path

if len(sys.argv) > 2:
    raise ValueError("Too many arguments")


timestamp = int(os.environ["SOURCE_DATE_EPOCH"])

path = Path(sys.argv[1])
old_buf = io.BytesIO()
with open(path, "rb") as f:
    old_buf.write(f.read())
old_buf.seek(0)
old = tarfile.open(fileobj=old_buf, mode="r:gz")

buf = io.BytesIO()
new = tarfile.open(fileobj=buf, mode="w", format=tarfile.GNU_FORMAT)
for i, m in enumerate(old):
    data = None
    # mutation does not work, copy
    if m.name.endswith('.DS_Store'):
        continue
    m2 = tarfile.TarInfo(m.name)
    m2.mtime = min(timestamp, m.mtime)
    m2.size = m.size
    m2.type = m.type
    m2.linkname = m.linkname
    m2.mode = m.mode
    if m.isdir():
        new.addfile(m2)
    else:
        data = old.extractfile(m)
        new.addfile(m2, data)
new.close()
old.close()

buf.seek(0)
with open(path, "wb") as f:
    with gzip.GzipFile('', "wb", fileobj=f, mtime=timestamp) as gzf:
        gzf.write(buf.read())

# checks the archive is valid.
archive = tarfile.open(path)
names = archive.getnames()
