"""
An exceptionally lousy site spider
Ken Kinder <ken@kenkinder.com>

Updated for newparallel by Min Ragan-Kelley <benjaminrk@gmail.com>

This module gives an example of how the task interface to the
IPython controller works.  Before running this script start the IPython controller
and some engines using something like::

    ipclusterz start -n 4
"""
import sys
from IPython.parallel import Client, error
import time
import BeautifulSoup # this isn't necessary, but it helps throw the dependency error earlier

def fetchAndParse(url, data=None):
    import urllib2
    import urlparse
    import BeautifulSoup
    links = []
    try:
        page = urllib2.urlopen(url, data=data)
    except Exception:
        return links
    else:
        if page.headers.type == 'text/html':
            doc = BeautifulSoup.BeautifulSoup(page.read())
            for node in doc.findAll('a'):
                href = node.get('href', None)
                if href:
                    links.append(urlparse.urljoin(url, href))
        return links

class DistributedSpider(object):

    # Time to wait between polling for task results.
    pollingDelay = 0.5

    def __init__(self, site):
        self.client = Client()
        self.view = self.client.load_balanced_view()
        self.mux = self.client[:]

        self.allLinks = []
        self.linksWorking = {}
        self.linksDone = {}

        self.site = site

    def visitLink(self, url):
        if url not in self.allLinks:
            self.allLinks.append(url)
            if url.startswith(self.site):
                print '    ', url
                self.linksWorking[url] = self.view.apply(fetchAndParse, url)

    def onVisitDone(self, links, url):
        print url, ':'
        self.linksDone[url] = None
        del self.linksWorking[url]
        for link in links:
            self.visitLink(link)

    def run(self):
        self.visitLink(self.site)
        while self.linksWorking:
            print len(self.linksWorking), 'pending...'
            self.synchronize()
            time.sleep(self.pollingDelay)

    def synchronize(self):
        for url, ar in self.linksWorking.items():
            # Calling get_task_result with block=False will return None if the
            # task is not done yet.  This provides a simple way of polling.
            try:
                links = ar.get(0)
            except error.TimeoutError:
                continue
            except Exception as e:
                self.linksDone[url] = None
                del self.linksWorking[url]
                print url, ':', e.traceback
            else:
                self.onVisitDone(links, url)

def main():
    if len(sys.argv) > 1:
        site = sys.argv[1]
    else:
        site = raw_input('Enter site to crawl: ')
    distributedSpider = DistributedSpider(site)
    distributedSpider.run()

if __name__ == '__main__':
    main()
