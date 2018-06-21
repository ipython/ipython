#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage:
    git-mpr [-h] [-l | -a] [pr-number [pr-number ...]]

Type `git mpr -h` for details.
"""


import io, os
import argparse
from subprocess import check_call, CalledProcessError

import gh_api

ipy_repository = 'git://github.com/ipython/ipython.git'
gh_project = "ipython/ipython"
not_merged = {}

def merge_branch(repo, branch ):
    """try to merge the givent branch into the current one
    
    If something does not goes smoothly, merge is aborted
    
    Returns True if merge successful, False otherwise
    """
    # Delete the branch first
    try :
        check_call(['git', 'pull', repo, branch], stdin=io.open(os.devnull))
    except CalledProcessError :
        check_call(['git', 'merge', '--abort'])
        return False
    return True

    
def git_new_branch(name):
    """Create a new branch with the given name and check it out.
    """
    check_call(['git', 'checkout', '-b', name])

    
def merge_pr(num):
    """ try to merge the branch of PR `num` into current branch
    """
    # Get Github authorisation first, so that the user is prompted straight away
    # if their login is needed.
    
    pr = gh_api.get_pull_request(gh_project, num)
    repo = pr['head']['repo']['clone_url']


    branch = pr['head']['ref']
    mergeable = merge_branch(repo=repo, 
                 branch=branch,
              )
    if not mergeable :
        cmd = "git pull "+repo+" "+branch
        not_merged[str(num)] = cmd
        print("==============================================================================")
        print("Something went wrong merging this branch, you can try it manually by running :")
        print(cmd)
        print("==============================================================================")
        
    
def main(*args):
    parser = argparse.ArgumentParser(
            description="""
                Merge one or more github pull requests by their number. If any
                one pull request can't be merged as is, its merge is ignored
                and the process continues with the next ones (if any).
                """
            )

    grp = parser.add_mutually_exclusive_group()
    grp.add_argument(
            '-l',
            '--list',
            action='store_const',
            const=True,
            help='list PR, their number and their mergeability')
    grp.add_argument('-a',
            '--merge-all',
            action='store_const',
            const=True ,
            help='try to merge as many PR as possible, one by one')
    parser.add_argument('merge',
            type=int,
            help="The pull request numbers",
            nargs='*',
            metavar='pr-number')
    args = parser.parse_args()

    if(args.list):
        pr_list = gh_api.get_pulls_list(gh_project)
        for pr in pr_list :
            mergeable = gh_api.get_pull_request(gh_project, pr['number'])['mergeable']

            ismgb = u"√" if mergeable else " "
            print(u"* #{number} [{ismgb}]:  {title}".format(
                number=pr['number'],
                title=pr['title'],
                ismgb=ismgb))

    if(args.merge_all):
        branch_name = 'merge-' + '-'.join(str(pr['number']) for pr in pr_list)
        git_new_branch(branch_name)
        pr_list = gh_api.get_pulls_list(gh_project)
        for pr in pr_list :
            merge_pr(pr['number'])


    elif args.merge:
        branch_name = 'merge-' + '-'.join(map(str, args.merge))
        git_new_branch(branch_name)
        for num in args.merge :
            merge_pr(num)

    if not_merged :
        print('*************************************************************************************')
        print('The following branch has not been merged automatically, consider doing it by hand   :')
        for num, cmd in not_merged.items() :
            print( "PR {num}: {cmd}".format(num=num, cmd=cmd))
        print('*************************************************************************************')

if __name__ == '__main__':
    main()
