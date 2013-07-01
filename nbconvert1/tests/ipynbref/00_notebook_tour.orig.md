# A brief tour of the IPython notebook

This document will give you a brief tour of the capabilities of the IPython notebook.  
You can view its contents by scrolling around, or execute each cell by typing `Shift-Enter`.
After you conclude this brief high-level tour, you should read the accompanying notebook 
titled `01_notebook_introduction`, which takes a more step-by-step approach to the features of the
system.  

The rest of the notebooks in this directory illustrate various other aspects and 
capabilities of the IPython notebook; some of them may require additional libraries to be executed.

**NOTE:** This notebook *must* be run from its own directory, so you must ``cd``
to this directory and then start the notebook, but do *not* use the ``--notebook-dir``
option to run it from another location.

The first thing you need to know is that you are still controlling the same old IPython you're used to,
so things like shell aliases and magic commands still work:

<div class="highlight"><pre><span class="n">pwd</span>
</pre></div>


<pre>
    u'/Users/minrk/dev/ip/mine/docs/examples/notebooks'
</pre>


<div class="highlight"><pre><span class="n">ls</span>
</pre></div>


    00_notebook_tour.ipynb          callbacks.ipynb                 python-logo.svg
    01_notebook_introduction.ipynb  cython_extension.ipynb          rmagic_extension.ipynb
    Animations_and_Progress.ipynb   display_protocol.ipynb          sympy.ipynb
    Capturing Output.ipynb          formatting.ipynb                sympy_quantum_computing.ipynb
    Script Magics.ipynb             octavemagic_extension.ipynb     trapezoid_rule.ipynb
    animation.m4v                   progbar.ipynb


<div class="highlight"><pre><span class="n">message</span> <span class="o">=</span> <span class="s">&#39;The IPython notebook is great!&#39;</span>
<span class="c"># note: the echo command does not run on Windows, it&#39;s a unix command.</span>
<span class="o">!</span><span class="nb">echo</span> <span class="nv">$message</span>
</pre></div>


    The IPython notebook is great!


## Plots with matplotlib

IPython adds an 'inline' matplotlib backend,
which embeds any matplotlib figures into the notebook.

<div class="highlight"><pre><span class="o">%</span><span class="k">pylab</span> <span class="n">inline</span>
</pre></div>


    
    Welcome to pylab, a matplotlib-based Python environment [backend: module://IPython.zmq.pylab.backend_inline].
    For more information, type 'help(pylab)'.


<div class="highlight"><pre><span class="n">x</span> <span class="o">=</span> <span class="n">linspace</span><span class="p">(</span><span class="mi">0</span><span class="p">,</span> <span class="mi">3</span><span class="o">*</span><span class="n">pi</span><span class="p">,</span> <span class="mi">500</span><span class="p">)</span>
<span class="n">plot</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="n">sin</span><span class="p">(</span><span class="n">x</span><span class="o">**</span><span class="mi">2</span><span class="p">))</span>
<span class="n">title</span><span class="p">(</span><span class="s">&#39;A simple chirp&#39;</span><span class="p">);</span>
</pre></div>



![](tests/ipynbref/00_notebook_tour_orig_files/00_notebook_tour_orig_fig_00.png)


You can paste blocks of input with prompt markers, such as those from
[the official Python tutorial](http://docs.python.org/tutorial/interpreter.html#interactive-mode)

<div class="highlight"><pre><span class="o">&gt;&gt;&gt;</span> <span class="n">the_world_is_flat</span> <span class="o">=</span> <span class="mi">1</span>
<span class="o">&gt;&gt;&gt;</span> <span class="k">if</span> <span class="n">the_world_is_flat</span><span class="p">:</span>
<span class="o">...</span>     <span class="k">print</span> <span class="s">&quot;Be careful not to fall off!&quot;</span>
</pre></div>


    Be careful not to fall off!


Errors are shown in informative ways:

<div class="highlight"><pre><span class="o">%</span><span class="k">run</span> <span class="n">non_existent_file</span>
</pre></div>


    ERROR: File `u'non_existent_file.py'` not found.

<div class="highlight"><pre><span class="n">x</span> <span class="o">=</span> <span class="mi">1</span>
<span class="n">y</span> <span class="o">=</span> <span class="mi">4</span>
<span class="n">z</span> <span class="o">=</span> <span class="n">y</span><span class="o">/</span><span class="p">(</span><span class="mi">1</span><span class="o">-</span><span class="n">x</span><span class="p">)</span>
</pre></div>


    ---------------------------------------------------------------------------
    ZeroDivisionError                         Traceback (most recent call last)
    <ipython-input-8-dc39888fd1d2> in <module>()
          1 x = 1
          2 y = 4
    ----> 3 z = y/(1-x)
    
    ZeroDivisionError: integer division or modulo by zero


When IPython needs to display additional information (such as providing details on an object via `x?`
it will automatically invoke a pager at the bottom of the screen:

<div class="highlight"><pre><span class="n">magic</span>
</pre></div>



## Non-blocking output of kernel

If you execute the next cell, you will see the output arriving as it is generated, not all at the end.

<div class="highlight"><pre><span class="kn">import</span> <span class="nn">time</span><span class="o">,</span> <span class="nn">sys</span>
<span class="k">for</span> <span class="n">i</span> <span class="ow">in</span> <span class="nb">range</span><span class="p">(</span><span class="mi">8</span><span class="p">):</span>
    <span class="k">print</span> <span class="n">i</span><span class="p">,</span>
    <span class="n">time</span><span class="o">.</span><span class="n">sleep</span><span class="p">(</span><span class="mf">0.5</span><span class="p">)</span>
</pre></div>


    0 
    1 
    2 
    3 
    4 
    5 
    6 
    7


## Clean crash and restart

We call the low-level system libc.time routine with the wrong argument via
ctypes to segfault the Python interpreter:

<div class="highlight"><pre><span class="kn">import</span> <span class="nn">sys</span>
<span class="kn">from</span> <span class="nn">ctypes</span> <span class="kn">import</span> <span class="n">CDLL</span>
<span class="c"># This will crash a Linux or Mac system; equivalent calls can be made on Windows</span>
<span class="n">dll</span> <span class="o">=</span> <span class="s">&#39;dylib&#39;</span> <span class="k">if</span> <span class="n">sys</span><span class="o">.</span><span class="n">platform</span> <span class="o">==</span> <span class="s">&#39;darwin&#39;</span> <span class="k">else</span> <span class="s">&#39;.so.6&#39;</span>
<span class="n">libc</span> <span class="o">=</span> <span class="n">CDLL</span><span class="p">(</span><span class="s">&quot;libc.</span><span class="si">%s</span><span class="s">&quot;</span> <span class="o">%</span> <span class="n">dll</span><span class="p">)</span> 
<span class="n">libc</span><span class="o">.</span><span class="n">time</span><span class="p">(</span><span class="o">-</span><span class="mi">1</span><span class="p">)</span>  <span class="c"># BOOM!!</span>
</pre></div>



## Markdown cells can contain formatted text and code

You can *italicize*, **boldface**

* build
* lists

and embed code meant for illustration instead of execution in Python:

    def f(x):
        """a docstring"""
        return x**2

or other languages:

    if (i=0; i<n; i++) {
      printf("hello %d\n", i);
      x += 4;
    }

Courtesy of MathJax, you can include mathematical expressions both inline: 
$e^{i\pi} + 1 = 0$  and displayed:

$$e^x=\sum_{i=0}^\infty \frac{1}{i!}x^i$$

## Rich displays: include anyting a browser can show

Note that we have an actual protocol for this, see the `display_protocol` notebook for further details.

### Images

<div class="highlight"><pre><span class="kn">from</span> <span class="nn">IPython.display</span> <span class="kn">import</span> <span class="n">Image</span>
<span class="n">Image</span><span class="p">(</span><span class="n">filename</span><span class="o">=</span><span class="s">&#39;../../source/_static/logo.png&#39;</span><span class="p">)</span>
</pre></div>


<pre>
    <IPython.core.display.Image at 0x10faeafd0>
</pre>


An image can also be displayed from raw data or a url

<div class="highlight"><pre><span class="n">Image</span><span class="p">(</span><span class="n">url</span><span class="o">=</span><span class="s">&#39;http://python.org/images/python-logo.gif&#39;</span><span class="p">)</span>
</pre></div>


<pre>
    <IPython.core.display.Image at 0x1060e7410>
</pre>


SVG images are also supported out of the box (since modern browsers do a good job of rendering them):

<div class="highlight"><pre><span class="kn">from</span> <span class="nn">IPython.display</span> <span class="kn">import</span> <span class="n">SVG</span>
<span class="n">SVG</span><span class="p">(</span><span class="n">filename</span><span class="o">=</span><span class="s">&#39;python-logo.svg&#39;</span><span class="p">)</span>
</pre></div>


<pre>
    <IPython.core.display.SVG at 0x10fb998d0>
</pre>


#### Embedded vs Non-embedded Images

As of IPython 0.13, images are embedded by default for compatibility with QtConsole, and the ability to still be displayed offline.

Let's look at the differences:

<div class="highlight"><pre><span class="c"># by default Image data are embedded</span>
<span class="n">Embed</span>      <span class="o">=</span> <span class="n">Image</span><span class="p">(</span>    <span class="s">&#39;http://scienceview.berkeley.edu/view/images/newview.jpg&#39;</span><span class="p">)</span>

<span class="c"># if kwarg `url` is given, the embedding is assumed to be false</span>
<span class="n">SoftLinked</span> <span class="o">=</span> <span class="n">Image</span><span class="p">(</span><span class="n">url</span><span class="o">=</span><span class="s">&#39;http://scienceview.berkeley.edu/view/images/newview.jpg&#39;</span><span class="p">)</span>

<span class="c"># In each case, embed can be specified explicitly with the `embed` kwarg</span>
<span class="c"># ForceEmbed = Image(url=&#39;http://scienceview.berkeley.edu/view/images/newview.jpg&#39;, embed=True)</span>
</pre></div>



Today's image from a webcam at Berkeley, (at the time I created this notebook). This should also work in the Qtconsole.
Drawback is that the saved notebook will be larger, but the image will still be present offline.

<div class="highlight"><pre><span class="n">Embed</span>
</pre></div>


<pre>
    <IPython.core.display.Image at 0x10fb99b50>
</pre>


Today's image from same webcam at Berkeley, (refreshed every minutes, if you reload the notebook), visible only with an active internet connexion, that should be different from the previous one. This will not work on Qtconsole.
Notebook saved with this kind of image will be lighter and always reflect the current version of the source, but the image won't display offline.

<div class="highlight"><pre><span class="n">SoftLinked</span>
</pre></div>


<pre>
    <IPython.core.display.Image at 0x10fb99b10>
</pre>


Of course, if you re-run the all notebook, the two images will be the same again.

### Video

And more exotic objects can also be displayed, as long as their representation supports 
the IPython display protocol.

For example, videos hosted externally on YouTube are easy to load (and writing a similar wrapper for other
hosted content is trivial):

<div class="highlight"><pre><span class="kn">from</span> <span class="nn">IPython.display</span> <span class="kn">import</span> <span class="n">YouTubeVideo</span>
<span class="c"># a talk about IPython at Sage Days at U. Washington, Seattle.</span>
<span class="c"># Video credit: William Stein.</span>
<span class="n">YouTubeVideo</span><span class="p">(</span><span class="s">&#39;1j_HxD4iLn8&#39;</span><span class="p">)</span>
</pre></div>


<pre>
    <IPython.lib.display.YouTubeVideo at 0x10fba2190>
</pre>


Using the nascent video capabilities of modern browsers, you may also be able to display local
videos.  At the moment this doesn't work very well in all browsers, so it may or may not work for you;
we will continue testing this and looking for ways to make it more robust.  

The following cell loads a local file called  `animation.m4v`, encodes the raw video as base64 for http
transport, and uses the HTML5 video tag to load it. On Chrome 15 it works correctly, displaying a control
bar at the bottom with a play/pause button and a location slider.

<div class="highlight"><pre><span class="kn">from</span> <span class="nn">IPython.display</span> <span class="kn">import</span> <span class="n">HTML</span>
<span class="n">video</span> <span class="o">=</span> <span class="nb">open</span><span class="p">(</span><span class="s">&quot;animation.m4v&quot;</span><span class="p">,</span> <span class="s">&quot;rb&quot;</span><span class="p">)</span><span class="o">.</span><span class="n">read</span><span class="p">()</span>
<span class="n">video_encoded</span> <span class="o">=</span> <span class="n">video</span><span class="o">.</span><span class="n">encode</span><span class="p">(</span><span class="s">&quot;base64&quot;</span><span class="p">)</span>
<span class="n">video_tag</span> <span class="o">=</span> <span class="s">&#39;&lt;video controls alt=&quot;test&quot; src=&quot;data:video/x-m4v;base64,{0}&quot;&gt;&#39;</span><span class="o">.</span><span class="n">format</span><span class="p">(</span><span class="n">video_encoded</span><span class="p">)</span>
<span class="n">HTML</span><span class="p">(</span><span class="n">data</span><span class="o">=</span><span class="n">video_tag</span><span class="p">)</span>
</pre></div>


<pre>
    <IPython.core.display.HTML at 0x10fba28d0>
</pre>


## Local Files

The above examples embed images and video from the notebook filesystem in the output
areas of code cells.  It is also possible to request these files directly in markdown cells
if they reside in the notebook directory via relative urls prefixed with `files/`:

    files/[subdirectory/]<filename>


For example, in the example notebook folder, we have the Python logo, addressed as:

    <img src="files/python-logo.svg" />

<img src="python-logo.svg" />

and a video with the HTML5 video tag:

    <video controls src="files/animation.m4v" />

<video controls src="animation.m4v" />

These do not embed the data into the notebook file,
and require that the files exist when you are viewing the notebook.

### Security of local files

Note that this means that the IPython notebook server also acts as a generic file server
for files inside the same tree as your notebooks.  Access is not granted outside the
notebook folder so you have strict control over what files are visible, but for this
reason it is highly recommended that you do not run the notebook server with a notebook
directory at a high level in your filesystem (e.g. your home directory).

When you run the notebook in a password-protected manner, local file access is restricted
to authenticated users unless read-only views are active.

## Linking to files and directories for viewing in the browser

It is also possible to link directly to files or directories so they can be opened in the browser. This is especially convenient if you're interacting with a tool within IPython that generates HTML pages, and you'd like to easily be able to open those in a new browser window. Alternatively, if your IPython notebook server is on a remote system, creating links provides an easy way to download any files that get generated.

As we saw above, there are a bunch of `.ipynb` files in our current directory.

<div class="highlight"><pre><span class="n">ls</span>
</pre></div>


    00_notebook_tour.ipynb          formatting.ipynb
    01_notebook_introduction.ipynb  octavemagic_extension.ipynb
    Animations_and_Progress.ipynb   publish_data.ipynb
    Capturing Output.ipynb          python-logo.svg
    Script Magics.ipynb             rmagic_extension.ipynb
    animation.m4v                   sympy.ipynb
    cython_extension.ipynb          sympy_quantum_computing.ipynb
    display_protocol.ipynb          trapezoid_rule.ipynb


If we want to create a link to one of them, we can call use the `FileLink` object.

<div class="highlight"><pre><span class="kn">from</span> <span class="nn">IPython.display</span> <span class="kn">import</span> <span class="n">FileLink</span>
<span class="n">FileLink</span><span class="p">(</span><span class="s">&#39;00_notebook_tour.ipynb&#39;</span><span class="p">)</span>
</pre></div>


<pre>
    <IPython.lib.display.FileLink at 0x10f7ea3d0>
</pre>


Alternatively, if we want to link to all of them, we can use the `FileLinks` object, passing `'.'` to indicate that we want links generated for the current working directory. Note that if there were other directories under the current directory, `FileLinks` would work in a recursive manner creating links to files in all sub-directories as well.

<div class="highlight"><pre><span class="kn">from</span> <span class="nn">IPython.display</span> <span class="kn">import</span> <span class="n">FileLinks</span>
<span class="n">FileLinks</span><span class="p">(</span><span class="s">&#39;.&#39;</span><span class="p">)</span>
</pre></div>


<pre>
    <IPython.lib.display.FileLinks at 0x10f7eaad0>
</pre>


### External sites

You can even embed an entire page from another site in an iframe; for example this is today's Wikipedia
page for mobile users:

<div class="highlight"><pre><span class="n">HTML</span><span class="p">(</span><span class="s">&#39;&lt;iframe src=http://en.mobile.wikipedia.org/?useformat=mobile width=700 height=350&gt;&lt;/iframe&gt;&#39;</span><span class="p">)</span>
</pre></div>


<pre>
    <IPython.core.display.HTML at 0x1094900d0>
</pre>


### Mathematics

And we also support the display of mathematical expressions typeset in LaTeX, which is rendered
in the browser thanks to the [MathJax library](http://mathjax.org).  

Note that this is *different* from the above examples.  Above we were typing mathematical expressions
in Markdown cells (along with normal text) and letting the browser render them; now we are displaying
the output of a Python computation as a LaTeX expression wrapped by the `Math()` object so the browser
renders it.  The `Math` object will add the needed LaTeX delimiters (`$$`) if they are not provided:

<div class="highlight"><pre><span class="kn">from</span> <span class="nn">IPython.display</span> <span class="kn">import</span> <span class="n">Math</span>
<span class="n">Math</span><span class="p">(</span><span class="s">r&#39;F(k) = \int_{-\infty}^{\infty} f(x) e^{2\pi i k} dx&#39;</span><span class="p">)</span>
</pre></div>


<pre>
    <IPython.core.display.Math at 0x10fba26d0>
</pre>


With the `Latex` class, you have to include the delimiters yourself.  This allows you to use other LaTeX modes such as `eqnarray`:

<div class="highlight"><pre><span class="kn">from</span> <span class="nn">IPython.display</span> <span class="kn">import</span> <span class="n">Latex</span>
<span class="n">Latex</span><span class="p">(</span><span class="s">r&quot;&quot;&quot;\begin{eqnarray}</span>
<span class="s">\nabla \times \vec{\mathbf{B}} -\, \frac1c\, \frac{\partial\vec{\mathbf{E}}}{\partial t} &amp; = \frac{4\pi}{c}\vec{\mathbf{j}} \\</span>
<span class="s">\nabla \cdot \vec{\mathbf{E}} &amp; = 4 \pi \rho \\</span>
<span class="s">\nabla \times \vec{\mathbf{E}}\, +\, \frac1c\, \frac{\partial\vec{\mathbf{B}}}{\partial t} &amp; = \vec{\mathbf{0}} \\</span>
<span class="s">\nabla \cdot \vec{\mathbf{B}} &amp; = 0 </span>
<span class="s">\end{eqnarray}&quot;&quot;&quot;</span><span class="p">)</span>
</pre></div>


<pre>
    <IPython.core.display.Latex at 0x10fba2c10>
</pre>


Or you can enter latex directly with the `%%latex` cell magic:

<div class="highlight"><pre><span class="o">%%</span><span class="k">latex</span>
\<span class="n">begin</span><span class="p">{</span><span class="n">aligned</span><span class="p">}</span>
\<span class="n">nabla</span> \<span class="n">times</span> \<span class="n">vec</span><span class="p">{</span>\<span class="n">mathbf</span><span class="p">{</span><span class="n">B</span><span class="p">}}</span> <span class="o">-</span>\<span class="p">,</span> \<span class="n">frac1c</span>\<span class="p">,</span> \<span class="n">frac</span><span class="p">{</span>\<span class="n">partial</span>\<span class="n">vec</span><span class="p">{</span>\<span class="n">mathbf</span><span class="p">{</span><span class="n">E</span><span class="p">}}}{</span>\<span class="n">partial</span> <span class="n">t</span><span class="p">}</span> <span class="o">&amp;</span> <span class="o">=</span> \<span class="n">frac</span><span class="p">{</span><span class="mi">4</span>\<span class="n">pi</span><span class="p">}{</span><span class="n">c</span><span class="p">}</span>\<span class="n">vec</span><span class="p">{</span>\<span class="n">mathbf</span><span class="p">{</span><span class="n">j</span><span class="p">}}</span> \\
\<span class="n">nabla</span> \<span class="n">cdot</span> \<span class="n">vec</span><span class="p">{</span>\<span class="n">mathbf</span><span class="p">{</span><span class="n">E</span><span class="p">}}</span> <span class="o">&amp;</span> <span class="o">=</span> <span class="mi">4</span> \<span class="n">pi</span> \<span class="n">rho</span> \\
\<span class="n">nabla</span> \<span class="n">times</span> \<span class="n">vec</span><span class="p">{</span>\<span class="n">mathbf</span><span class="p">{</span><span class="n">E</span><span class="p">}}</span>\<span class="p">,</span> <span class="o">+</span>\<span class="p">,</span> \<span class="n">frac1c</span>\<span class="p">,</span> \<span class="n">frac</span><span class="p">{</span>\<span class="n">partial</span>\<span class="n">vec</span><span class="p">{</span>\<span class="n">mathbf</span><span class="p">{</span><span class="n">B</span><span class="p">}}}{</span>\<span class="n">partial</span> <span class="n">t</span><span class="p">}</span> <span class="o">&amp;</span> <span class="o">=</span> \<span class="n">vec</span><span class="p">{</span>\<span class="n">mathbf</span><span class="p">{</span><span class="mi">0</span><span class="p">}}</span> \\
\<span class="n">nabla</span> \<span class="n">cdot</span> \<span class="n">vec</span><span class="p">{</span>\<span class="n">mathbf</span><span class="p">{</span><span class="n">B</span><span class="p">}}</span> <span class="o">&amp;</span> <span class="o">=</span> <span class="mi">0</span>
\<span class="n">end</span><span class="p">{</span><span class="n">aligned</span><span class="p">}</span>
</pre></div>


    <IPython.core.display.Latex at 0x10a617c90>

There is also a `%%javascript` cell magic for running javascript directly,
and `%%svg` for manually entering SVG content.

# Loading external codes
* Drag and drop a ``.py`` in the dashboard
* Use ``%load`` with any local or remote url: [the Matplotlib Gallery!](http://matplotlib.sourceforge.net/gallery.html)

In this notebook we've kept the output saved so you can see the result, but you should run the next
cell yourself (with an active internet connection).

Let's make sure we have pylab again, in case we have restarted the kernel due to the crash demo above

<div class="highlight"><pre><span class="o">%</span><span class="k">pylab</span> <span class="n">inline</span>
</pre></div>


    
    Welcome to pylab, a matplotlib-based Python environment [backend: module://IPython.zmq.pylab.backend_inline].
    For more information, type 'help(pylab)'.


<div class="highlight"><pre><span class="o">%</span><span class="k">load</span> <span class="n">http</span><span class="p">:</span><span class="o">//</span><span class="n">matplotlib</span><span class="o">.</span><span class="n">sourceforge</span><span class="o">.</span><span class="n">net</span><span class="o">/</span><span class="n">mpl_examples</span><span class="o">/</span><span class="n">pylab_examples</span><span class="o">/</span><span class="n">integral_demo</span><span class="o">.</span><span class="n">py</span>
</pre></div>



<div class="highlight"><pre><span class="c">#!/usr/bin/env python</span>

<span class="c"># implement the example graphs/integral from pyx</span>
<span class="kn">from</span> <span class="nn">pylab</span> <span class="kn">import</span> <span class="o">*</span>
<span class="kn">from</span> <span class="nn">matplotlib.patches</span> <span class="kn">import</span> <span class="n">Polygon</span>

<span class="k">def</span> <span class="nf">func</span><span class="p">(</span><span class="n">x</span><span class="p">):</span>
    <span class="k">return</span> <span class="p">(</span><span class="n">x</span><span class="o">-</span><span class="mi">3</span><span class="p">)</span><span class="o">*</span><span class="p">(</span><span class="n">x</span><span class="o">-</span><span class="mi">5</span><span class="p">)</span><span class="o">*</span><span class="p">(</span><span class="n">x</span><span class="o">-</span><span class="mi">7</span><span class="p">)</span><span class="o">+</span><span class="mi">85</span>

<span class="n">ax</span> <span class="o">=</span> <span class="n">subplot</span><span class="p">(</span><span class="mi">111</span><span class="p">)</span>

<span class="n">a</span><span class="p">,</span> <span class="n">b</span> <span class="o">=</span> <span class="mi">2</span><span class="p">,</span> <span class="mi">9</span> <span class="c"># integral area</span>
<span class="n">x</span> <span class="o">=</span> <span class="n">arange</span><span class="p">(</span><span class="mi">0</span><span class="p">,</span> <span class="mi">10</span><span class="p">,</span> <span class="mf">0.01</span><span class="p">)</span>
<span class="n">y</span> <span class="o">=</span> <span class="n">func</span><span class="p">(</span><span class="n">x</span><span class="p">)</span>
<span class="n">plot</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="n">y</span><span class="p">,</span> <span class="n">linewidth</span><span class="o">=</span><span class="mi">1</span><span class="p">)</span>

<span class="c"># make the shaded region</span>
<span class="n">ix</span> <span class="o">=</span> <span class="n">arange</span><span class="p">(</span><span class="n">a</span><span class="p">,</span> <span class="n">b</span><span class="p">,</span> <span class="mf">0.01</span><span class="p">)</span>
<span class="n">iy</span> <span class="o">=</span> <span class="n">func</span><span class="p">(</span><span class="n">ix</span><span class="p">)</span>
<span class="n">verts</span> <span class="o">=</span> <span class="p">[(</span><span class="n">a</span><span class="p">,</span><span class="mi">0</span><span class="p">)]</span> <span class="o">+</span> <span class="nb">zip</span><span class="p">(</span><span class="n">ix</span><span class="p">,</span><span class="n">iy</span><span class="p">)</span> <span class="o">+</span> <span class="p">[(</span><span class="n">b</span><span class="p">,</span><span class="mi">0</span><span class="p">)]</span>
<span class="n">poly</span> <span class="o">=</span> <span class="n">Polygon</span><span class="p">(</span><span class="n">verts</span><span class="p">,</span> <span class="n">facecolor</span><span class="o">=</span><span class="s">&#39;0.8&#39;</span><span class="p">,</span> <span class="n">edgecolor</span><span class="o">=</span><span class="s">&#39;k&#39;</span><span class="p">)</span>
<span class="n">ax</span><span class="o">.</span><span class="n">add_patch</span><span class="p">(</span><span class="n">poly</span><span class="p">)</span>

<span class="n">text</span><span class="p">(</span><span class="mf">0.5</span> <span class="o">*</span> <span class="p">(</span><span class="n">a</span> <span class="o">+</span> <span class="n">b</span><span class="p">),</span> <span class="mi">30</span><span class="p">,</span>
     <span class="s">r&quot;$\int_a^b f(x)\mathrm{d}x$&quot;</span><span class="p">,</span> <span class="n">horizontalalignment</span><span class="o">=</span><span class="s">&#39;center&#39;</span><span class="p">,</span>
     <span class="n">fontsize</span><span class="o">=</span><span class="mi">20</span><span class="p">)</span>

<span class="n">axis</span><span class="p">([</span><span class="mi">0</span><span class="p">,</span><span class="mi">10</span><span class="p">,</span> <span class="mi">0</span><span class="p">,</span> <span class="mi">180</span><span class="p">])</span>
<span class="n">figtext</span><span class="p">(</span><span class="mf">0.9</span><span class="p">,</span> <span class="mf">0.05</span><span class="p">,</span> <span class="s">&#39;x&#39;</span><span class="p">)</span>
<span class="n">figtext</span><span class="p">(</span><span class="mf">0.1</span><span class="p">,</span> <span class="mf">0.9</span><span class="p">,</span> <span class="s">&#39;y&#39;</span><span class="p">)</span>
<span class="n">ax</span><span class="o">.</span><span class="n">set_xticks</span><span class="p">((</span><span class="n">a</span><span class="p">,</span><span class="n">b</span><span class="p">))</span>
<span class="n">ax</span><span class="o">.</span><span class="n">set_xticklabels</span><span class="p">((</span><span class="s">&#39;a&#39;</span><span class="p">,</span><span class="s">&#39;b&#39;</span><span class="p">))</span>
<span class="n">ax</span><span class="o">.</span><span class="n">set_yticks</span><span class="p">([])</span>
<span class="n">show</span><span class="p">()</span>
</pre></div>



![](tests/ipynbref/00_notebook_tour_orig_files/00_notebook_tour_orig_fig_01.png)

