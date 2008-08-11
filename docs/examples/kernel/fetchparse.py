"""
An exceptionally lousy site spider
Ken Kinder <ken@kenkinder.com>

This module gives an example of how the TaskClient interface to the 
IPython controller works.  Before running this script start the IPython controller
and some engines using something like::

    ipcluster -n 4
"""
from twisted.python.failure import Failure
from IPython.kernel import client
import time

fetchParse = """
from twisted.web import microdom
import urllib2
import urlparse

def fetchAndParse(url, data=None):
    links = []
    try:
        page = urllib2.urlopen(url, data=data)
    except Exception:
        return links
    else:
        if page.headers.type == 'text/html':
            doc = microdom.parseString(page.read(), beExtremelyLenient=True)
            for node in doc.getElementsByTagName('a'):
                if node.getAttribute('href'):
                    links.append(urlparse.urljoin(url, node.getAttribute('href')))
        return links
"""

class DistributedSpider(object):
    
    # Time to wait between polling for task results.
    pollingDelay = 0.5
    
    def __init__(self, site):
        self.tc = client.TaskClient()
        self.rc = client.MultiEngineClient()
        self.rc.execute(fetchParse)
        
        self.allLinks = []
        self.linksWorking = {}
        self.linksDone = {}
        
        self.site = site
        
    def visitLink(self, url):
        if url not in self.allLinks:
            self.allLinks.append(url)
            if url.startswith(self.site):
                print '    ', url
                self.linksWorking[url] = self.tc.run(client.StringTask('links = fetchAndParse(url)', pull=['links'], push={'url': url}))
        
    def onVisitDone(self, result, url):
        print url, ':'
        self.linksDone[url] = None
        del self.linksWorking[url]
        if isinstance(result.failure, Failure):
            txt = result.failure.getTraceback()
            for line in txt.split('\n'):
                print '    ', line
        else:
            for link in result.ns.links:
                self.visitLink(link)
                
    def run(self):
        self.visitLink(self.site)
        while self.linksWorking:
            print len(self.linksWorking), 'pending...'
            self.synchronize()
            time.sleep(self.pollingDelay)
    
    def synchronize(self):
        for url, taskId in self.linksWorking.items():
            # Calling get_task_result with block=False will return None if the
            # task is not done yet.  This provides a simple way of polling.
            result = self.tc.get_task_result(taskId, block=False)
            if result is not None:
                self.onVisitDone(result, url)

def main():
    distributedSpider = DistributedSpider(raw_input('Enter site to crawl: '))
    distributedSpider.run()

if __name__ == '__main__':
    main()
