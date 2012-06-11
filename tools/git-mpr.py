#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage:
    python git-mpr.py -m 1657
"""
from __future__ import print_function

import argparse
from subprocess import check_call, CalledProcessError

import gh_api

ipy_repository = 'git://github.com/ipython/ipython.git'
gh_project = "ipython/ipython"
not_merged = {}

def merge_branch(repo, branch ):
    """try to merge the givent branch into the current one
    
    If something does not goes smoothly, merge is aborted
    
    Returns True if merge sucessfull, False otherwise
    """
    # Delete the branch first
    try :
        check_call(['git', 'pull', '--no-edit', repo, branch])
    except CalledProcessError :
        check_call(['git', 'merge', '--abort'])
        return False
    return True


def merge_pr(num, github_api=3):
    """ try to merge the branch of PR `num` into current branch
    
    github_api : use github api v2 (to bypass https and issues with proxy) to find the
             remote branch that should be merged by it's number
    """
    # Get Github authorisation first, so that the user is prompted straight away
    # if their login is needed.
    
    pr = gh_api.get_pull_request(gh_project, num, github_api)
    if github_api == 2:
        repo = pr['head']['repository']['url']
    elif github_api == 3 :
        repo = pr['head']['repo']['clone_url']


    branch = pr['head']['ref']
    mergeable = merge_branch(repo=repo, 
                 branch=branch,
              )
    if not mergeable :
        cmd = "git pull "+repo+" "+branch
        not_merged[str(num)] = cmd
        print("==============================================================================")
        print("Something went wrong merging this branch, you can try it manually by runngin :")
        print(cmd)
        print("==============================================================================")
        
    
def main(*args):
    parser = argparse.ArgumentParser(
            description="""
                Merge (one|many) github pull request by their number.\
                
                If pull request can't be merge as is, cancel merge,
                and continue to the next if any.
                """
            )
    parser.add_argument('-v2', '--githubapiv2', action='store_const', const=2)

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
    grp.add_argument('-m',
            '--merge',
            type=int,
            help="The pull request numbers",
            nargs='*',
            metavar='pr-number')
    args = parser.parse_args()
    if args.githubapiv2 == 2 :
        github_api = 2
    else  :
        github_api = 3

    if(args.list):
        pr_list = gh_api.get_pulls_list(gh_project, github_api)
        for pr in pr_list :
            mergeable = gh_api.get_pull_request(gh_project, pr['number'], github_api=github_api)['mergeable']

            ismgb = u"√" if mergeable else " "
            print(u"* #{number} [{ismgb}]:  {title}".format(
                number=pr['number'],
                title=pr['title'],
                ismgb=ismgb))

    if(args.merge_all):
        pr_list = gh_api.get_pulls_list(gh_project)
        for pr in pr_list :
            merge_pr(pr['number'])


    elif args.merge:
        for num in args.merge :
            merge_pr(num, github_api=github_api)

    if not_merged :
        print('*************************************************************************************')
        print('the following branch have not been merged automatically, considere doing it by hand :')
        for num, cmd in not_merged.items() :
            print( "PR {num}: {cmd}".format(num=num, cmd=cmd))
        print('*************************************************************************************')

if __name__ == '__main__':
    main()
