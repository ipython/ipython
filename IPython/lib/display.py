"""Various display related classes.

Authors : MinRK
"""
from datetime import timedelta

class YouTubeVideo(object):
    """Class for embedding a YouTube Video in an IPython session, based on its video id.

    e.g. to embed the video on this page:

    http://www.youtube.com/watch?v=foo

    you would do:

    vid = YouTubeVideo("foo")
    display(vid)
    
    To start from a particular time offset:
    
    vid = YouTubeVideo("abc", start=timedelta(hours=1, minutes=47, seconds=3))
    display(vid)
    """

    def __init__(self, id, width=400, height=300, start=timedelta()):
        self.id = id
        self.width = width
        self.height = height
        self.start = start.total_seconds()

    def _repr_html_(self):
        """return YouTube embed iframe for this video id"""
        return """
            <iframe
                width="%i"
                height="%i"
                src="http://www.youtube.com/embed/%s?start=%i"
                frameborder="0"
                allowfullscreen
            ></iframe>
        """%(self.width, self.height, self.id, self.start)

