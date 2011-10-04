"""Various display related classes.

Authors : MinRK
"""

class YouTubeVideo(object):
    """Class for embedding a YouTube Video in an IPython session, based on its video id.

    e.g. to embed the video on this page:

    http://www.youtube.com/watch?v=foo

    you would do:

    vid = YouTubeVideo("foo")
    display(vid)
    """

    def __init__(self, id, width=400, height=300):
        self.id = id
        self.width = width
        self.height = height

    def _repr_html_(self):
        """return YouTube embed iframe for this video id"""
        return """
            <iframe
                width="%i"
                height="%i"
                src="http://www.youtube.com/embed/%s"
                frameborder="0"
                allowfullscreen
            ></iframe>
        """%(self.width, self.height, self.id)

