"""Various display related classes.

Authors : MinRK
"""
import urllib

class YouTubeVideo(object):
    """Class for embedding a YouTube Video in an IPython session, based on its video id.

    e.g. to embed the video on this page:

    http://www.youtube.com/watch?v=foo

    you would do:

    vid = YouTubeVideo("foo")
    display(vid)
    
    To start from 30 seconds:
    
    vid = YouTubeVideo("abc", start=30)
    display(vid)
    
    To calculate seconds from time as hours, minutes, seconds use int(timedelta(hours=1, minutes=46, seconds=40).total_seconds())

    Other parameters can be provided as documented at 
    https://developers.google.com/youtube/player_parameters#parameter-subheader
    """

    def __init__(self, id, width=400, height=300, **kwargs):
        self.id = id
        self.width = width
        self.height = height
        self.params = kwargs

    def _repr_html_(self):
        """return YouTube embed iframe for this video id"""
        if self.params:
            params = "?" + urllib.urlencode(self.params)
        else:
            params = ""
        return """
            <iframe
                width="%i"
                height="%i"
                src="http://www.youtube.com/embed/%s%s"
                frameborder="0"
                allowfullscreen
            ></iframe>
        """%(self.width, self.height, self.id, params)