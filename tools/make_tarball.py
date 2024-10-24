#!/usr/bin/env python
"""Simple script to create a tarball with proper git info.
"""

import subprocess

from toollib import cd, sh

tag = subprocess.check_output('git describe --tags', shell=True).decode('utf8', 'replace').strip()
base_name = 'ipython-%s' % tag
tar_name = '%s.tgz' % base_name

# git archive is weird:  Even if I give it a specific path, it still won't
# archive the whole tree.  It seems the only way to get the whole tree is to cd
# to the top of the tree.  There are long threads (since 2007) on the git list
# about this and it still doesn't work in a sensible way...

cd('..')
git_tpl = 'git archive --format=tar --prefix={0}/ HEAD | gzip > {1}'
sh(git_tpl.format(base_name, tar_name))
sh('mv {0} tools/'.format(tar_name))
