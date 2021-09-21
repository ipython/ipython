Enable to add extra attributes to iframe
========================================

You can add any extra attributes to the ``<iframe>`` tag
since the argument ``extras`` has been added to the ``IFrame`` class.
for example::

    In [1]: from IPython.display import IFrame

    In [2]: print(IFrame(src="src", width=300, height=300, extras=["hello", "world"])._repr_html_())

            <iframe
                width="300"
                height="300"
                src="src"
                frameborder="0"
                allowfullscreen
                hello world
            ></iframe>

Using it, you can autoplay ``YouTubeVideo`` by adding ``'allow="autoplay"'``,
even in browsers that disable it by default, such as Google Chrome.
And, you can write it more briefly by using the argument ``allow_autoplay``.
::

    In [1]: from IPython.display import YouTubeVideo

    In [2]: print(YouTubeVideo("video-id", allow_autoplay=True)._repr_html_())

            <iframe
                width="400"
                height="300"
                src="https://www.youtube.com/embed/video-id?autoplay=1"
                frameborder="0"
                allowfullscreen
                allow="autoplay"
            ></iframe>
