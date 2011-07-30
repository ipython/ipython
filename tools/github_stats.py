#!/usr/bin/env python
"""Simple tools to query github.com and gather stats about issues.
"""
from __future__ import print_function

import json
import sys

from datetime import datetime, timedelta
from urllib import urlopen


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


if __name__ == "__main__":
    # Demo, search one year back
    show_urls = True
    if len(sys.argv) > 1:
        days = int(sys.argv[1])
    else:
        days = 365

    if 1:
        issues = sorted_by_field(issues_closed_since(timedelta(days=days)),
                                 reverse=True)

    pulls = filter(is_pull_request, issues)
    regular = filter(lambda i: not is_pull_request(i), issues)
    n = len(issues)

    print("%d total issues closed in the last %d days." % (n, days))
    print("%d pull requests and %d regular issues." % (len(pulls), len(regular)))
    print()
    print('Pull requests (%d):\n' % len(pulls))
    report(pulls, show_urls)
    print()
    print('Regular issues (%d):\n' % len(regular))
    report(regular, show_urls)
