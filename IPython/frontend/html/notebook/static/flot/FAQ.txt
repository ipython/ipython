Frequently asked questions
--------------------------

Q: How much data can Flot cope with?

A: Flot will happily draw everything you send to it so the answer
depends on the browser. The excanvas emulation used for IE (built with
VML) makes IE by far the slowest browser so be sure to test with that
if IE users are in your target group.

1000 points is not a problem, but as soon as you start having more
points than the pixel width, you should probably start thinking about
downsampling/aggregation as this is near the resolution limit of the
chart anyway. If you downsample server-side, you also save bandwidth.


Q: Flot isn't working when I'm using JSON data as source!

A: Actually, Flot loves JSON data, you just got the format wrong.
Double check that you're not inputting strings instead of numbers,
like [["0", "-2.13"], ["5", "4.3"]]. This is most common mistake, and
the error might not show up immediately because Javascript can do some
conversion automatically.


Q: Can I export the graph?

A: This is a limitation of the canvas technology. There's a hook in
the canvas object for getting an image out, but you won't get the tick
labels. And it's not likely to be supported by IE. At this point, your
best bet is probably taking a screenshot, e.g. with PrtScn.


Q: The bars are all tiny in time mode?

A: It's not really possible to determine the bar width automatically.
So you have to set the width with the barWidth option which is NOT in
pixels, but in the units of the x axis (or the y axis for horizontal
bars). For time mode that's milliseconds so the default value of 1
makes the bars 1 millisecond wide.


Q: Can I use Flot with libraries like Mootools or Prototype?

A: Yes, Flot supports it out of the box and it's easy! Just use jQuery
instead of $, e.g. call jQuery.plot instead of $.plot and use
jQuery(something) instead of $(something). As a convenience, you can
put in a DOM element for the graph placeholder where the examples and
the API documentation are using jQuery objects.

Depending on how you include jQuery, you may have to add one line of
code to prevent jQuery from overwriting functions from the other
libraries, see the documentation in jQuery ("Using jQuery with other
libraries") for details.


Q: Flot doesn't work with [insert name of Javascript UI framework]!

A: The only non-standard thing used by Flot is the canvas tag;
otherwise it is simply a series of absolute positioned divs within the
placeholder tag you put in. If this is not working, it's probably
because the framework you're using is doing something weird with the
DOM, or you're using it the wrong way.

A common problem is that there's display:none on a container until the
user does something. Many tab widgets work this way, and there's
nothing wrong with it - you just can't call Flot inside a display:none
container as explained in the README so you need to hold off the Flot
call until the container is actually displayed (or use
visibility:hidden instead of display:none or move the container
off-screen).

If you find there's a specific thing we can do to Flot to help, feel
free to submit a bug report. Otherwise, you're welcome to ask for help
on the forum/mailing list, but please don't submit a bug report to
Flot.
