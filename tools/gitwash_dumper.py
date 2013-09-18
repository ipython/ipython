#!/usr/bin/env python
""" Checkout gitwash repo into directory and do search replace on name """

import os
from os.path import join as pjoin
import shutil
import sys
import re
import glob
import fnmatch
import tempfile
from subprocess import call


verbose = False


def clone_repo(url, branch):
    cwd = os.getcwdu()
    tmpdir = tempfile.mkdtemp()
    try:
        cmd = 'git clone %s %s' % (url, tmpdir)
        call(cmd, shell=True)
        os.chdir(tmpdir)
        cmd = 'git checkout %s' % branch
        call(cmd, shell=True)
    except:
        shutil.rmtree(tmpdir)
        raise
    finally:
        os.chdir(cwd)
    return tmpdir


def cp_files(in_path, globs, out_path):
    try:
        os.makedirs(out_path)
    except OSError:
        pass
    out_fnames = []
    for in_glob in globs:
        in_glob_path = pjoin(in_path, in_glob)
        for in_fname in glob.glob(in_glob_path):
            out_fname = in_fname.replace(in_path, out_path)
            pth, _ = os.path.split(out_fname)
            if not os.path.isdir(pth):
                os.makedirs(pth)
            shutil.copyfile(in_fname, out_fname)
            out_fnames.append(out_fname)
    return out_fnames


def filename_search_replace(sr_pairs, filename, backup=False):
    """ Search and replace for expressions in files

    """
    in_txt = open(filename, 'rt').read(-1)
    out_txt = in_txt[:]
    for in_exp, out_exp in sr_pairs:
        in_exp = re.compile(in_exp)
        out_txt = in_exp.sub(out_exp, out_txt)
    if in_txt == out_txt:
        return False
    open(filename, 'wt').write(out_txt)
    if backup:
        open(filename + '.bak', 'wt').write(in_txt)
    return True

        
def copy_replace(replace_pairs,
                 out_path,
                 repo_url,
                 repo_branch = 'master',
                 cp_globs=('*',),
                 rep_globs=('*',),
                 renames = ()):
    repo_path = clone_repo(repo_url, repo_branch)
    try:
        out_fnames = cp_files(repo_path, cp_globs, out_path)
    finally:
        shutil.rmtree(repo_path)
    renames = [(re.compile(in_exp), out_exp) for in_exp, out_exp in renames]
    fnames = []
    for rep_glob in rep_globs:
        fnames += fnmatch.filter(out_fnames, rep_glob)
    if verbose:
        print '\n'.join(fnames)
    for fname in fnames:
        filename_search_replace(replace_pairs, fname, False)
        for in_exp, out_exp in renames:
            new_fname, n = in_exp.subn(out_exp, fname)
            if n:
                os.rename(fname, new_fname)
                break

            
USAGE = ''' <output_directory> <project_name>

If not set with options, the repository name is the same as the <project
name>

If not set with options, the main github user is the same as the
repository name.'''


GITWASH_CENTRAL = 'git://github.com/matthew-brett/gitwash.git'
GITWASH_BRANCH = 'master'


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.set_usage(parser.get_usage().strip() + USAGE)
    parser.add_option("--repo-name", dest="repo_name",
                      help="repository name - e.g. nitime",
                      metavar="REPO_NAME")
    parser.add_option("--github-user", dest="main_gh_user",
                      help="github username for main repo - e.g fperez",
                      metavar="MAIN_GH_USER")
    parser.add_option("--gitwash-url", dest="gitwash_url",
                      help="URL to gitwash repository - default %s"
                      % GITWASH_CENTRAL, 
                      default=GITWASH_CENTRAL,
                      metavar="GITWASH_URL")
    parser.add_option("--gitwash-branch", dest="gitwash_branch",
                      help="branch in gitwash repository - default %s"
                      % GITWASH_BRANCH,
                      default=GITWASH_BRANCH,
                      metavar="GITWASH_BRANCH")
    parser.add_option("--source-suffix", dest="source_suffix",
                      help="suffix of ReST source files - default '.rst'",
                      default='.rst',
                      metavar="SOURCE_SUFFIX")
    (options, args) = parser.parse_args()
    if len(args) < 2:
        parser.print_help()
        sys.exit()
    out_path, project_name = args
    if options.repo_name is None:
        options.repo_name = project_name
    if options.main_gh_user is None:
        options.main_gh_user = options.repo_name
    copy_replace((('PROJECTNAME', project_name),
                  ('REPONAME', options.repo_name),
                  ('MAIN_GH_USER', options.main_gh_user)),
                 out_path,
                 options.gitwash_url,
                 options.gitwash_branch,
                 cp_globs=(pjoin('gitwash', '*'),),
                 rep_globs=('*.rst',),
                 renames=(('\.rst$', options.source_suffix),))
