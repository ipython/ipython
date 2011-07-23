import json
from datetime import datetime, timedelta
import sys
from urllib import urlopen

def get_issues(project="ipython/ipython/", state="open"):
    """Get a list of the issues from the Github API."""
    f = urlopen("http://github.com/api/v2/json/issues/list/%s%s" % (project, state))
    return json.load(f)['issues']

def _parse_datetime(s):
    """Parse dates in the format returned by the Github API."""
    return datetime.strptime(s.rpartition(" ")[0], "%Y/%m/%d %H:%M:%S")

def issues_closed_since(period=timedelta(days=365), project="ipython/ipython/"):
    """Get all issues closed since a particular point in time. period
can either be a datetime object, or a timedelta object. In the
latter case, it is used as a time before the present."""
    allclosed = get_issues(project=project, state='closed')
    if isinstance(period, timedelta):
        period = datetime.now() - period
    return [i for i in allclosed if _parse_datetime(i['closed_at']) > period]

if __name__ == "__main__":
    # Demo
    if len(sys.argv) > 1:
        days = int(sys.argv[1])
    else:
        days = 365
    n = len(issues_closed_since(timedelta(days=days)))
    print "%d issues closed in the last %d days." % (n, days)
