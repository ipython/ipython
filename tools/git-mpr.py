#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage:
    python test_pr.py 1657
"""
from __future__ import print_function

import re
import requests
from subprocess import call, check_call, check_output, CalledProcessError
import sys

import gh_api

ipy_repository = 'git://github.com/ipython/ipython.git'
gh_project="ipython/ipython"
not_merged={}

def get_branch(repo, branch, owner, mergeable):
    merged_branch = "%s-%s" % (owner, branch)
    # Delete the branch first
    try :
        check_call(['git', 'pull','--no-edit',repo, branch])
    except CalledProcessError :
        check_call(['git', 'merge', '--abort'])
        return False
    return True

def merge_pr(num,httpv2=False):
    # Get Github authorisation first, so that the user is prompted straight away
    # if their login is needed.
    
    pr = gh_api.get_pull_request(gh_project, num, httpv2)
    if(httpv2):
        repo = pr['head']['repository']['url']
        owner=pr['head']['user']['name'],
    else :
        repo=pr['head']['repo']['clone_url']
        owner=pr['head']['repo']['owner']['login'],

    branch=pr['head']['ref']
    mergeable = get_branch(repo=repo, 
                 branch=branch,
                 owner=owner,
                 mergeable=pr['mergeable'],
              )
    if not mergeable :
        cmd = "git pull "+repo+" "+branch
        not_merged[str(num)]=cmd
        print("==============================================================================")
        print("Something went wrong merging this branch, you can try it manually by runngin :")
        print(cmd)
        print("==============================================================================")
        
    

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
            description="""
                Merge (one|many) github pull request by their number.\
                
                If pull request can't be merge as is, cancel merge,
                and continue to the next if any.
                """
            )
    parser.add_argument('-v2','--githubapiv2', action='store_const', const=True)

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
    not_merged = {}; 
    args = parser.parse_args()
    ghv2 = args.githubapiv2
    if(args.list):
        pr_list = gh_api.get_pulls_list(gh_project, ghv2)
        for pr in pr_list :
            mergeable = gh_api.get_pull_request(gh_project, pr['number'],httpv2=ghv2)['mergeable']

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
            merge_pr(num,httpv2=ghv2)

    if not_merged :
        print('*************************************************************************************')
        print('the following branch have not been merged automatically, considere doing it by hand :')
        for num,cmd in not_merged.items() :
            print( "PR {num}: {cmd}".format(num=num,cmd=cmd))
        print('*************************************************************************************')
