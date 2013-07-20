#!/usr/bin/env python
"""Simple tools to query github.com and gather stats about issues.
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import print_function

import json
import re
import sys

from datetime import datetime, timedelta
from subprocess import check_output
from gh_api import get_paged_request, make_auth_header, get_pull_request

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

ISO8601 = "%Y-%m-%dT%H:%M:%SZ"
PER_PAGE = 100

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def get_issues(project="ipython/ipython", state="closed", pulls=False):
    """Get a list of the issues from the Github API."""
    which = 'pulls' if pulls else 'issues'
    url = "https://api.github.com/repos/%s/%s?state=%s&per_page=%i" % (project, which, state, PER_PAGE)
    return get_paged_request(url, headers=make_auth_header())

def round_hour(dt):
    return dt.replace(minute=0,second=0,microsecond=0)

def _parse_datetime(s):
    """Parse dates in the format returned by the Github API."""
    if s:
        return datetime.strptime(s, ISO8601)
    else:
        return datetime.fromtimestamp(0)


def issues2dict(issues):
    """Convert a list of issues to a dict, keyed by issue number."""
    idict = {}
    for i in issues:
        idict[i['number']] = i
    return idict


def is_pull_request(issue):
    """Return True if the given issue is a pull request."""
    return bool(issue.get('pull_request', {}).get('html_url', None))


def split_pulls(all_issues, project="ipython/ipython"):
    """split a list of closed issues into non-PR Issues and Pull Requests"""
    pulls = []
    issues = []
    for i in all_issues:
        if is_pull_request(i):
            pull = get_pull_request(project, i['number'], auth=True)
            pulls.append(pull)
        else:
            issues.append(i)
    return issues, pulls



def issues_closed_since(period=timedelta(days=365), project="ipython/ipython", pulls=False):
    """Get all issues closed since a particular point in time. period
    can either be a datetime object, or a timedelta object. In the
    latter case, it is used as a time before the present.
    """

    which = 'pulls' if pulls else 'issues'

    if isinstance(period, timedelta):
        since = round_hour(datetime.utcnow() - period)
    else:
        since = period
    url = "https://api.github.com/repos/%s/%s?state=closed&sort=updated&since=%s&per_page=%i" % (project, which, since.strftime(ISO8601), PER_PAGE)
    allclosed = get_paged_request(url, headers=make_auth_header())
    
    filtered = [ i for i in allclosed if _parse_datetime(i['closed_at']) > since ]
    if pulls:
        filtered = [ i for i in filtered if _parse_datetime(i['merged_at']) > since ]
        # filter out PRs not against master (backports)
        filtered = [ i for i in filtered if i['base']['ref'] == 'master' ]
    else:
        filtered = [ i for i in filtered if not is_pull_request(i) ]
    
    return filtered


def sorted_by_field(issues, field='closed_at', reverse=False):
    """Return a list of issues sorted by closing date date."""
    return sorted(issues, key = lambda i:i[field], reverse=reverse)


def report(issues, show_urls=False):
    """Summary report about a list of issues, printing number and title.
    """
    # titles may have unicode in them, so we must encode everything below
    if show_urls:
        for i in issues:
            role = 'ghpull' if 'merged_at' in i else 'ghissue'
            print('* :%s:`%d`: %s' % (role, i['number'],
                                        i['title'].encode('utf-8')))
    else:
        for i in issues:
            print('* %d: %s' % (i['number'], i['title'].encode('utf-8')))

#-----------------------------------------------------------------------------
# Main script
#-----------------------------------------------------------------------------

if __name__ == "__main__":
    # deal with unicode
    import codecs
    sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    
    # Whether to add reST urls for all issues in printout.
    show_urls = True

    # By default, search one month back
    tag = None
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except:
            tag = sys.argv[1]
    else:
        tag = check_output(['git', 'describe', '--abbrev=0']).strip()
    
    if tag:
        cmd = ['git', 'log', '-1', '--format=%ai', tag]
        tagday, tz = check_output(cmd).strip().rsplit(' ', 1)
        since = datetime.strptime(tagday, "%Y-%m-%d %H:%M:%S")
        h = int(tz[1:3])
        m = int(tz[3:])
        td = timedelta(hours=h, minutes=m)
        if tz[0] == '-':
            since += td
        else:
            since -= td
    else:
        since = datetime.utcnow() - timedelta(days=days)
    
    since = round_hour(since)

    print("fetching GitHub stats since %s (tag: %s)" % (since, tag), file=sys.stderr)
    # turn off to play interactively without redownloading, use %run -i
    if 1:
        issues = issues_closed_since(since, pulls=False)
        pulls = issues_closed_since(since, pulls=True)
    
    # For regular reports, it's nice to show them in reverse chronological order
    issues = sorted_by_field(issues, reverse=True)
    pulls = sorted_by_field(pulls, reverse=True)
    
    n_issues, n_pulls = map(len, (issues, pulls))
    n_total = n_issues + n_pulls
    
    # Print summary report we can directly include into release notes.
    
    print()
    since_day = since.strftime("%Y/%m/%d")
    today = datetime.today().strftime("%Y/%m/%d")
    print("GitHub stats for %s - %s (tag: %s)" % (since_day, today, tag))
    print()
    print("These lists are automatically generated, and may be incomplete or contain duplicates.")
    print()
    if tag:
        # print git info, in addition to GitHub info:
        since_tag = tag+'..'
        cmd = ['git', 'log', '--oneline', since_tag]
        ncommits = len(check_output(cmd).splitlines())
        
        author_cmd = ['git', 'log', '--use-mailmap', "--format='* %aN'", since_tag]
        all_authors = check_output(author_cmd).decode('utf-8', 'replace').splitlines()
        unique_authors = sorted(set(all_authors), key=lambda s: s.lower())
        print("The following %i authors contributed %i commits." % (len(unique_authors), ncommits))
        print()
        print('\n'.join(unique_authors))
        print()
        
    print()
    print("We closed a total of %d issues, %d pull requests and %d regular issues;\n"
          "this is the full list (generated with the script \n"
          ":file:`tools/github_stats.py`):" % (n_total, n_pulls, n_issues))
    print()
    print('Pull Requests (%d):\n' % n_pulls)
    report(pulls, show_urls)
    print()
    print('Issues (%d):\n' % n_issues)
    report(issues, show_urls)
