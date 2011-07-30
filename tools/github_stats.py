#!/usr/bin/env python
"""Simple tools to query github.com and gather stats about issues.
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import print_function

import json
import sys

from datetime import datetime, timedelta
from urllib import urlopen

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def get_issues(project="ipython/ipython/", state="open"):
    """Get a list of the issues from the Github API."""
    f = urlopen("http://github.com/api/v2/json/issues/list/%s%s" % (project,
                                                                    state))
    return json.load(f)['issues']


def _parse_datetime(s):
    """Parse dates in the format returned by the Github API."""
    return datetime.strptime(s.rpartition(" ")[0], "%Y/%m/%d %H:%M:%S")


def issues2dict(issues):
    """Convert a list of issues to a dict, keyed by issue number."""
    idict = {}
    for i in issues:
        idict[i['number']] = i
    return idict


def is_pull_request(issue):
    """Return True if the given issue is a pull request."""
    return 'pull_request_url' in issue


def issues_closed_since(period=timedelta(days=365), project="ipython/ipython/"):
    """Get all issues closed since a particular point in time. period
can either be a datetime object, or a timedelta object. In the
latter case, it is used as a time before the present."""
    allclosed = get_issues(project=project, state='closed')
    if isinstance(period, timedelta):
        period = datetime.now() - period
    return [i for i in allclosed if _parse_datetime(i['closed_at']) > period]


def sorted_by_field(issues, field='closed_at', reverse=False):
    """Return a list of issues sorted by closing date date."""
    return sorted(issues, key = lambda i:i[field], reverse=reverse)


def report(issues, show_urls=False):
    """Summary report about a list of issues, printing number and title.
    """
    # titles may have unicode in them, so we must encode everything below
    if show_urls:
        for i in issues:
            print('* `%d <%s>`_: %s' % (i['number'],
                                        i['html_url'].encode('utf-8'),
                                        i['title'].encode('utf-8')))
    else:
        for i in issues:
            print('* %d: %s' % (i['number'], i['title'].encode('utf-8')))

#-----------------------------------------------------------------------------
# Main script
#-----------------------------------------------------------------------------

if __name__ == "__main__":
    # Whether to add reST urls for all issues in printout.
    show_urls = True

    # By default, search one month back
    if len(sys.argv) > 1:
        days = int(sys.argv[1])
    else:
        days = 30

    # turn off to play interactively without redownloading, use %run -i
    if 1:
        issues = issues_closed_since(timedelta(days=days))

    # For regular reports, it's nice to show them in reverse chronological order
    issues = sorted_by_field(issues, reverse=True)

    # Break up into pull requests and regular issues
    pulls = filter(is_pull_request, issues)
    regular = filter(lambda i: not is_pull_request(i), issues)
    n_issues, n_pulls, n_regular = map(len, (issues, pulls, regular))

    # Print summary report we can directly include into release notes.
    print("Github stats for the last  %d days." % days)
    print("We closed a total of %d issues, %d pull requests and %d regular \n"
          "issues; this is the full list (generated with the script \n"
          "`tools/github_stats.py`):" % (n_issues, n_pulls, n_regular))
    print()
    print('Pull requests (%d):\n' % n_pulls)
    report(pulls, show_urls)
    print()
    print('Regular issues (%d):\n' % n_regular)
    report(regular, show_urls)
