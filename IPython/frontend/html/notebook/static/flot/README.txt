About
-----

Flot is a Javascript plotting library for jQuery. Read more at the
website:

  http://code.google.com/p/flot/

Take a look at the examples linked from above, they should give a good
impression of what Flot can do and the source code of the examples is
probably the fastest way to learn how to use Flot.
  

Installation
------------

Just include the Javascript file after you've included jQuery.

Generally, all browsers that support the HTML5 canvas tag are
supported.

For support for Internet Explorer < 9, you can use Excanvas, a canvas
emulator; this is used in the examples bundled with Flot. You just
include the excanvas script like this:

  <!--[if lte IE 8]><script language="javascript" type="text/javascript" src="excanvas.min.js"></script><![endif]-->

If it's not working on your development IE 6.0, check that it has
support for VML which Excanvas is relying on. It appears that some
stripped down versions used for test environments on virtual machines
lack the VML support.

You can also try using Flashcanvas (see
http://code.google.com/p/flashcanvas/), which uses Flash to do the
emulation. Although Flash can be a bit slower to load than VML, if
you've got a lot of points, the Flash version can be much faster
overall. Flot contains some wrapper code for activating Excanvas which
Flashcanvas is compatible with.

You need at least jQuery 1.2.6, but try at least 1.3.2 for interactive
charts because of performance improvements in event handling.


Basic usage
-----------

Create a placeholder div to put the graph in:

   <div id="placeholder"></div>

You need to set the width and height of this div, otherwise the plot
library doesn't know how to scale the graph. You can do it inline like
this:

   <div id="placeholder" style="width:600px;height:300px"></div>

You can also do it with an external stylesheet. Make sure that the
placeholder isn't within something with a display:none CSS property -
in that case, Flot has trouble measuring label dimensions which
results in garbled looks and might have trouble measuring the
placeholder dimensions which is fatal (it'll throw an exception).

Then when the div is ready in the DOM, which is usually on document
ready, run the plot function:

  $.plot($("#placeholder"), data, options);

Here, data is an array of data series and options is an object with
settings if you want to customize the plot. Take a look at the
examples for some ideas of what to put in or look at the reference
in the file "API.txt". Here's a quick example that'll draw a line from
(0, 0) to (1, 1):

  $.plot($("#placeholder"), [ [[0, 0], [1, 1]] ], { yaxis: { max: 1 } });

The plot function immediately draws the chart and then returns a plot
object with a couple of methods.


What's with the name?
---------------------

First: it's pronounced with a short o, like "plot". Not like "flawed".

So "Flot" rhymes with "plot".

And if you look up "flot" in a Danish-to-English dictionary, some up
the words that come up are "good-looking", "attractive", "stylish",
"smart", "impressive", "extravagant". One of the main goals with Flot
is pretty looks.
