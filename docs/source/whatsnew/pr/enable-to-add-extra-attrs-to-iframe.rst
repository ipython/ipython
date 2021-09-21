``YouTubeVideo`` autoplay and the ability to add extra attributes to ``IFrame``
===============================================================================

You can add any extra attributes to the ``<iframe>`` tag using the new
``extras`` argument in the ``IFrame`` class. For example::

    In [1]: from IPython.display import IFrame

    In [2]: IFrame(src="src", width=300, height=300, extras=['loading="eager"'])

The above cells will result in the following HTML code being displayed in a
notebook::

    <iframe
        width="300"
        height="300"
        src="src"
        frameborder="0"
        allowfullscreen
        loading="eager"
    ></iframe>

Related to the above, the ``YouTubeVideo`` class now takes an
``allow_autoplay`` flag, which sets up the iframe of the embedded YouTube video
such that it allows autoplay.

.. note::
    Whether this works depends on the autoplay policy of the browser rendering
    the HTML allowing it. It also could get blocked by some browser extensions.

Try it out!
::

    In [1]: from IPython.display import YouTubeVideo

    In [2]: YouTubeVideo("dQw4w9WgXcQ", allow_autoplay=True)

🙃
