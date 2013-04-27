# XKCD plots in Matplotlib

This notebook originally appeared as a blog post at [Pythonic Perambulations](http://jakevdp.github.com/blog/2012/10/07/xkcd-style-plots-in-matplotlib/) by Jake Vanderplas.

One of the problems I've had with typical matplotlib figures is that everything in them is so precise, so perfect.  For an example of what I mean, take a look at this figure:

<div class="highlight"><pre><span class="kn">from</span> <span class="nn">IPython.display</span> <span class="kn">import</span> <span class="n">Image</span>
<span class="n">Image</span><span class="p">(</span><span class="s">&#39;http://jakevdp.github.com/figures/xkcd_version.png&#39;</span><span class="p">)</span>
</pre></div>


<pre>
    <IPython.core.display.Image at 0x2fef710>
</pre>


Sometimes when showing schematic plots, this is the type of figure I want to display.  But drawing it by hand is a pain: I'd rather just use matplotlib.  The problem is, matplotlib is a bit too precise.  Attempting to duplicate this figure in matplotlib leads to something like this:

<div class="highlight"><pre><span class="n">Image</span><span class="p">(</span><span class="s">&#39;http://jakevdp.github.com/figures/mpl_version.png&#39;</span><span class="p">)</span>
</pre></div>


<pre>
    <IPython.core.display.Image at 0x2fef0d0>
</pre>


It just doesn't have the same effect.  Matplotlib is great for scientific plots, but sometimes you don't want to be so precise.

This subject has recently come up on the matplotlib mailing list, and started some interesting discussions.
As near as I can tell, this started with a thread on a
[mathematica list](http://mathematica.stackexchange.com/questions/11350/xkcd-style-graphs)
which prompted a thread on the [matplotlib list](http://matplotlib.1069221.n5.nabble.com/XKCD-style-graphs-td39226.html)
wondering if the same could be done in matplotlib.

Damon McDougall offered a quick
[solution](http://www.mail-archive.com/matplotlib-users@lists.sourceforge.net/msg25499.html)
which was improved by Fernando Perez in [this notebook](http://nbviewer.ipython.org/3835181/), and
within a few days there was a [matplotlib pull request](https://github.com/matplotlib/matplotlib/pull/1329) offering a very general
way to create sketch-style plots in matplotlib.  Only a few days from a cool idea to a
working implementation: this is one of the most incredible aspects of package development on github.

The pull request looks really nice, but will likely not be included in a released version of
matplotlib until at least version 1.3.  In the mean-time, I wanted a way to play around with
these types of plots in a way that is compatible with the current release of matplotlib.  To do that,
I created the following code:

## The Code: XKCDify

XKCDify will take a matplotlib ``Axes`` instance, and modify the plot elements in-place to make
them look hand-drawn.
First off, we'll need to make sure we have the Humor Sans font.
It can be downloaded using the command below.

Next we'll create a function ``xkcd_line`` to add jitter to lines.  We want this to be very general, so
we'll normalize the size of the lines, and use a low-pass filter to add correlated noise, perpendicular
to the direction of the line.  There are a few parameters for this filter that can be tweaked to
customize the appearance of the jitter.

Finally, we'll create a function which accepts a matplotlib axis, and calls ``xkcd_line`` on
all lines in the axis.  Additionally, we'll switch the font of all text in the axes, and add
some background lines for a nice effect where lines cross.  We'll also draw axes, and move the
axes labels and titles to the appropriate location.

<div class="highlight"><pre><span class="sd">&quot;&quot;&quot;</span>
<span class="sd">XKCD plot generator</span>
<span class="sd">-------------------</span>
<span class="sd">Author: Jake Vanderplas</span>

<span class="sd">This is a script that will take any matplotlib line diagram, and convert it</span>
<span class="sd">to an XKCD-style plot.  It will work for plots with line &amp; text elements,</span>
<span class="sd">including axes labels and titles (but not axes tick labels).</span>

<span class="sd">The idea for this comes from work by Damon McDougall</span>
<span class="sd">  http://www.mail-archive.com/matplotlib-users@lists.sourceforge.net/msg25499.html</span>
<span class="sd">&quot;&quot;&quot;</span>
<span class="kn">import</span> <span class="nn">numpy</span> <span class="kn">as</span> <span class="nn">np</span>
<span class="kn">import</span> <span class="nn">pylab</span> <span class="kn">as</span> <span class="nn">pl</span>
<span class="kn">from</span> <span class="nn">scipy</span> <span class="kn">import</span> <span class="n">interpolate</span><span class="p">,</span> <span class="n">signal</span>
<span class="kn">import</span> <span class="nn">matplotlib.font_manager</span> <span class="kn">as</span> <span class="nn">fm</span>


<span class="c"># We need a special font for the code below.  It can be downloaded this way:</span>
<span class="kn">import</span> <span class="nn">os</span>
<span class="kn">import</span> <span class="nn">urllib2</span>
<span class="k">if</span> <span class="ow">not</span> <span class="n">os</span><span class="o">.</span><span class="n">path</span><span class="o">.</span><span class="n">exists</span><span class="p">(</span><span class="s">&#39;Humor-Sans.ttf&#39;</span><span class="p">):</span>
    <span class="n">fhandle</span> <span class="o">=</span> <span class="n">urllib2</span><span class="o">.</span><span class="n">urlopen</span><span class="p">(</span><span class="s">&#39;http://antiyawn.com/uploads/Humor-Sans.ttf&#39;</span><span class="p">)</span>
    <span class="nb">open</span><span class="p">(</span><span class="s">&#39;Humor-Sans.ttf&#39;</span><span class="p">,</span> <span class="s">&#39;wb&#39;</span><span class="p">)</span><span class="o">.</span><span class="n">write</span><span class="p">(</span><span class="n">fhandle</span><span class="o">.</span><span class="n">read</span><span class="p">())</span>

    
<span class="k">def</span> <span class="nf">xkcd_line</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="n">y</span><span class="p">,</span> <span class="n">xlim</span><span class="o">=</span><span class="bp">None</span><span class="p">,</span> <span class="n">ylim</span><span class="o">=</span><span class="bp">None</span><span class="p">,</span>
              <span class="n">mag</span><span class="o">=</span><span class="mf">1.0</span><span class="p">,</span> <span class="n">f1</span><span class="o">=</span><span class="mi">30</span><span class="p">,</span> <span class="n">f2</span><span class="o">=</span><span class="mf">0.05</span><span class="p">,</span> <span class="n">f3</span><span class="o">=</span><span class="mi">15</span><span class="p">):</span>
    <span class="sd">&quot;&quot;&quot;</span>
<span class="sd">    Mimic a hand-drawn line from (x, y) data</span>

<span class="sd">    Parameters</span>
<span class="sd">    ----------</span>
<span class="sd">    x, y : array_like</span>
<span class="sd">        arrays to be modified</span>
<span class="sd">    xlim, ylim : data range</span>
<span class="sd">        the assumed plot range for the modification.  If not specified,</span>
<span class="sd">        they will be guessed from the  data</span>
<span class="sd">    mag : float</span>
<span class="sd">        magnitude of distortions</span>
<span class="sd">    f1, f2, f3 : int, float, int</span>
<span class="sd">        filtering parameters.  f1 gives the size of the window, f2 gives</span>
<span class="sd">        the high-frequency cutoff, f3 gives the size of the filter</span>
<span class="sd">    </span>
<span class="sd">    Returns</span>
<span class="sd">    -------</span>
<span class="sd">    x, y : ndarrays</span>
<span class="sd">        The modified lines</span>
<span class="sd">    &quot;&quot;&quot;</span>
    <span class="n">x</span> <span class="o">=</span> <span class="n">np</span><span class="o">.</span><span class="n">asarray</span><span class="p">(</span><span class="n">x</span><span class="p">)</span>
    <span class="n">y</span> <span class="o">=</span> <span class="n">np</span><span class="o">.</span><span class="n">asarray</span><span class="p">(</span><span class="n">y</span><span class="p">)</span>
    
    <span class="c"># get limits for rescaling</span>
    <span class="k">if</span> <span class="n">xlim</span> <span class="ow">is</span> <span class="bp">None</span><span class="p">:</span>
        <span class="n">xlim</span> <span class="o">=</span> <span class="p">(</span><span class="n">x</span><span class="o">.</span><span class="n">min</span><span class="p">(),</span> <span class="n">x</span><span class="o">.</span><span class="n">max</span><span class="p">())</span>
    <span class="k">if</span> <span class="n">ylim</span> <span class="ow">is</span> <span class="bp">None</span><span class="p">:</span>
        <span class="n">ylim</span> <span class="o">=</span> <span class="p">(</span><span class="n">y</span><span class="o">.</span><span class="n">min</span><span class="p">(),</span> <span class="n">y</span><span class="o">.</span><span class="n">max</span><span class="p">())</span>

    <span class="k">if</span> <span class="n">xlim</span><span class="p">[</span><span class="mi">1</span><span class="p">]</span> <span class="o">==</span> <span class="n">xlim</span><span class="p">[</span><span class="mi">0</span><span class="p">]:</span>
        <span class="n">xlim</span> <span class="o">=</span> <span class="n">ylim</span>
        
    <span class="k">if</span> <span class="n">ylim</span><span class="p">[</span><span class="mi">1</span><span class="p">]</span> <span class="o">==</span> <span class="n">ylim</span><span class="p">[</span><span class="mi">0</span><span class="p">]:</span>
        <span class="n">ylim</span> <span class="o">=</span> <span class="n">xlim</span>

    <span class="c"># scale the data</span>
    <span class="n">x_scaled</span> <span class="o">=</span> <span class="p">(</span><span class="n">x</span> <span class="o">-</span> <span class="n">xlim</span><span class="p">[</span><span class="mi">0</span><span class="p">])</span> <span class="o">*</span> <span class="mf">1.</span> <span class="o">/</span> <span class="p">(</span><span class="n">xlim</span><span class="p">[</span><span class="mi">1</span><span class="p">]</span> <span class="o">-</span> <span class="n">xlim</span><span class="p">[</span><span class="mi">0</span><span class="p">])</span>
    <span class="n">y_scaled</span> <span class="o">=</span> <span class="p">(</span><span class="n">y</span> <span class="o">-</span> <span class="n">ylim</span><span class="p">[</span><span class="mi">0</span><span class="p">])</span> <span class="o">*</span> <span class="mf">1.</span> <span class="o">/</span> <span class="p">(</span><span class="n">ylim</span><span class="p">[</span><span class="mi">1</span><span class="p">]</span> <span class="o">-</span> <span class="n">ylim</span><span class="p">[</span><span class="mi">0</span><span class="p">])</span>

    <span class="c"># compute the total distance along the path</span>
    <span class="n">dx</span> <span class="o">=</span> <span class="n">x_scaled</span><span class="p">[</span><span class="mi">1</span><span class="p">:]</span> <span class="o">-</span> <span class="n">x_scaled</span><span class="p">[:</span><span class="o">-</span><span class="mi">1</span><span class="p">]</span>
    <span class="n">dy</span> <span class="o">=</span> <span class="n">y_scaled</span><span class="p">[</span><span class="mi">1</span><span class="p">:]</span> <span class="o">-</span> <span class="n">y_scaled</span><span class="p">[:</span><span class="o">-</span><span class="mi">1</span><span class="p">]</span>
    <span class="n">dist_tot</span> <span class="o">=</span> <span class="n">np</span><span class="o">.</span><span class="n">sum</span><span class="p">(</span><span class="n">np</span><span class="o">.</span><span class="n">sqrt</span><span class="p">(</span><span class="n">dx</span> <span class="o">*</span> <span class="n">dx</span> <span class="o">+</span> <span class="n">dy</span> <span class="o">*</span> <span class="n">dy</span><span class="p">))</span>

    <span class="c"># number of interpolated points is proportional to the distance</span>
    <span class="n">Nu</span> <span class="o">=</span> <span class="nb">int</span><span class="p">(</span><span class="mi">200</span> <span class="o">*</span> <span class="n">dist_tot</span><span class="p">)</span>
    <span class="n">u</span> <span class="o">=</span> <span class="n">np</span><span class="o">.</span><span class="n">arange</span><span class="p">(</span><span class="o">-</span><span class="mi">1</span><span class="p">,</span> <span class="n">Nu</span> <span class="o">+</span> <span class="mi">1</span><span class="p">)</span> <span class="o">*</span> <span class="mf">1.</span> <span class="o">/</span> <span class="p">(</span><span class="n">Nu</span> <span class="o">-</span> <span class="mi">1</span><span class="p">)</span>

    <span class="c"># interpolate curve at sampled points</span>
    <span class="n">k</span> <span class="o">=</span> <span class="nb">min</span><span class="p">(</span><span class="mi">3</span><span class="p">,</span> <span class="nb">len</span><span class="p">(</span><span class="n">x</span><span class="p">)</span> <span class="o">-</span> <span class="mi">1</span><span class="p">)</span>
    <span class="n">res</span> <span class="o">=</span> <span class="n">interpolate</span><span class="o">.</span><span class="n">splprep</span><span class="p">([</span><span class="n">x_scaled</span><span class="p">,</span> <span class="n">y_scaled</span><span class="p">],</span> <span class="n">s</span><span class="o">=</span><span class="mi">0</span><span class="p">,</span> <span class="n">k</span><span class="o">=</span><span class="n">k</span><span class="p">)</span>
    <span class="n">x_int</span><span class="p">,</span> <span class="n">y_int</span> <span class="o">=</span> <span class="n">interpolate</span><span class="o">.</span><span class="n">splev</span><span class="p">(</span><span class="n">u</span><span class="p">,</span> <span class="n">res</span><span class="p">[</span><span class="mi">0</span><span class="p">])</span> 

    <span class="c"># we&#39;ll perturb perpendicular to the drawn line</span>
    <span class="n">dx</span> <span class="o">=</span> <span class="n">x_int</span><span class="p">[</span><span class="mi">2</span><span class="p">:]</span> <span class="o">-</span> <span class="n">x_int</span><span class="p">[:</span><span class="o">-</span><span class="mi">2</span><span class="p">]</span>
    <span class="n">dy</span> <span class="o">=</span> <span class="n">y_int</span><span class="p">[</span><span class="mi">2</span><span class="p">:]</span> <span class="o">-</span> <span class="n">y_int</span><span class="p">[:</span><span class="o">-</span><span class="mi">2</span><span class="p">]</span>
    <span class="n">dist</span> <span class="o">=</span> <span class="n">np</span><span class="o">.</span><span class="n">sqrt</span><span class="p">(</span><span class="n">dx</span> <span class="o">*</span> <span class="n">dx</span> <span class="o">+</span> <span class="n">dy</span> <span class="o">*</span> <span class="n">dy</span><span class="p">)</span>

    <span class="c"># create a filtered perturbation</span>
    <span class="n">coeffs</span> <span class="o">=</span> <span class="n">mag</span> <span class="o">*</span> <span class="n">np</span><span class="o">.</span><span class="n">random</span><span class="o">.</span><span class="n">normal</span><span class="p">(</span><span class="mi">0</span><span class="p">,</span> <span class="mf">0.01</span><span class="p">,</span> <span class="nb">len</span><span class="p">(</span><span class="n">x_int</span><span class="p">)</span> <span class="o">-</span> <span class="mi">2</span><span class="p">)</span>
    <span class="n">b</span> <span class="o">=</span> <span class="n">signal</span><span class="o">.</span><span class="n">firwin</span><span class="p">(</span><span class="n">f1</span><span class="p">,</span> <span class="n">f2</span> <span class="o">*</span> <span class="n">dist_tot</span><span class="p">,</span> <span class="n">window</span><span class="o">=</span><span class="p">(</span><span class="s">&#39;kaiser&#39;</span><span class="p">,</span> <span class="n">f3</span><span class="p">))</span>
    <span class="n">response</span> <span class="o">=</span> <span class="n">signal</span><span class="o">.</span><span class="n">lfilter</span><span class="p">(</span><span class="n">b</span><span class="p">,</span> <span class="mi">1</span><span class="p">,</span> <span class="n">coeffs</span><span class="p">)</span>

    <span class="n">x_int</span><span class="p">[</span><span class="mi">1</span><span class="p">:</span><span class="o">-</span><span class="mi">1</span><span class="p">]</span> <span class="o">+=</span> <span class="n">response</span> <span class="o">*</span> <span class="n">dy</span> <span class="o">/</span> <span class="n">dist</span>
    <span class="n">y_int</span><span class="p">[</span><span class="mi">1</span><span class="p">:</span><span class="o">-</span><span class="mi">1</span><span class="p">]</span> <span class="o">+=</span> <span class="n">response</span> <span class="o">*</span> <span class="n">dx</span> <span class="o">/</span> <span class="n">dist</span>

    <span class="c"># un-scale data</span>
    <span class="n">x_int</span> <span class="o">=</span> <span class="n">x_int</span><span class="p">[</span><span class="mi">1</span><span class="p">:</span><span class="o">-</span><span class="mi">1</span><span class="p">]</span> <span class="o">*</span> <span class="p">(</span><span class="n">xlim</span><span class="p">[</span><span class="mi">1</span><span class="p">]</span> <span class="o">-</span> <span class="n">xlim</span><span class="p">[</span><span class="mi">0</span><span class="p">])</span> <span class="o">+</span> <span class="n">xlim</span><span class="p">[</span><span class="mi">0</span><span class="p">]</span>
    <span class="n">y_int</span> <span class="o">=</span> <span class="n">y_int</span><span class="p">[</span><span class="mi">1</span><span class="p">:</span><span class="o">-</span><span class="mi">1</span><span class="p">]</span> <span class="o">*</span> <span class="p">(</span><span class="n">ylim</span><span class="p">[</span><span class="mi">1</span><span class="p">]</span> <span class="o">-</span> <span class="n">ylim</span><span class="p">[</span><span class="mi">0</span><span class="p">])</span> <span class="o">+</span> <span class="n">ylim</span><span class="p">[</span><span class="mi">0</span><span class="p">]</span>
    
    <span class="k">return</span> <span class="n">x_int</span><span class="p">,</span> <span class="n">y_int</span>


<span class="k">def</span> <span class="nf">XKCDify</span><span class="p">(</span><span class="n">ax</span><span class="p">,</span> <span class="n">mag</span><span class="o">=</span><span class="mf">1.0</span><span class="p">,</span>
            <span class="n">f1</span><span class="o">=</span><span class="mi">50</span><span class="p">,</span> <span class="n">f2</span><span class="o">=</span><span class="mf">0.01</span><span class="p">,</span> <span class="n">f3</span><span class="o">=</span><span class="mi">15</span><span class="p">,</span>
            <span class="n">bgcolor</span><span class="o">=</span><span class="s">&#39;w&#39;</span><span class="p">,</span>
            <span class="n">xaxis_loc</span><span class="o">=</span><span class="bp">None</span><span class="p">,</span>
            <span class="n">yaxis_loc</span><span class="o">=</span><span class="bp">None</span><span class="p">,</span>
            <span class="n">xaxis_arrow</span><span class="o">=</span><span class="s">&#39;+&#39;</span><span class="p">,</span>
            <span class="n">yaxis_arrow</span><span class="o">=</span><span class="s">&#39;+&#39;</span><span class="p">,</span>
            <span class="n">ax_extend</span><span class="o">=</span><span class="mf">0.1</span><span class="p">,</span>
            <span class="n">expand_axes</span><span class="o">=</span><span class="bp">False</span><span class="p">):</span>
    <span class="sd">&quot;&quot;&quot;Make axis look hand-drawn</span>

<span class="sd">    This adjusts all lines, text, legends, and axes in the figure to look</span>
<span class="sd">    like xkcd plots.  Other plot elements are not modified.</span>
<span class="sd">    </span>
<span class="sd">    Parameters</span>
<span class="sd">    ----------</span>
<span class="sd">    ax : Axes instance</span>
<span class="sd">        the axes to be modified.</span>
<span class="sd">    mag : float</span>
<span class="sd">        the magnitude of the distortion</span>
<span class="sd">    f1, f2, f3 : int, float, int</span>
<span class="sd">        filtering parameters.  f1 gives the size of the window, f2 gives</span>
<span class="sd">        the high-frequency cutoff, f3 gives the size of the filter</span>
<span class="sd">    xaxis_loc, yaxis_log : float</span>
<span class="sd">        The locations to draw the x and y axes.  If not specified, they</span>
<span class="sd">        will be drawn from the bottom left of the plot</span>
<span class="sd">    xaxis_arrow, yaxis_arrow : str</span>
<span class="sd">        where to draw arrows on the x/y axes.  Options are &#39;+&#39;, &#39;-&#39;, &#39;+-&#39;, or &#39;&#39;</span>
<span class="sd">    ax_extend : float</span>
<span class="sd">        How far (fractionally) to extend the drawn axes beyond the original</span>
<span class="sd">        axes limits</span>
<span class="sd">    expand_axes : bool</span>
<span class="sd">        if True, then expand axes to fill the figure (useful if there is only</span>
<span class="sd">        a single axes in the figure)</span>
<span class="sd">    &quot;&quot;&quot;</span>
    <span class="c"># Get axes aspect</span>
    <span class="n">ext</span> <span class="o">=</span> <span class="n">ax</span><span class="o">.</span><span class="n">get_window_extent</span><span class="p">()</span><span class="o">.</span><span class="n">extents</span>
    <span class="n">aspect</span> <span class="o">=</span> <span class="p">(</span><span class="n">ext</span><span class="p">[</span><span class="mi">3</span><span class="p">]</span> <span class="o">-</span> <span class="n">ext</span><span class="p">[</span><span class="mi">1</span><span class="p">])</span> <span class="o">/</span> <span class="p">(</span><span class="n">ext</span><span class="p">[</span><span class="mi">2</span><span class="p">]</span> <span class="o">-</span> <span class="n">ext</span><span class="p">[</span><span class="mi">0</span><span class="p">])</span>

    <span class="n">xlim</span> <span class="o">=</span> <span class="n">ax</span><span class="o">.</span><span class="n">get_xlim</span><span class="p">()</span>
    <span class="n">ylim</span> <span class="o">=</span> <span class="n">ax</span><span class="o">.</span><span class="n">get_ylim</span><span class="p">()</span>

    <span class="n">xspan</span> <span class="o">=</span> <span class="n">xlim</span><span class="p">[</span><span class="mi">1</span><span class="p">]</span> <span class="o">-</span> <span class="n">xlim</span><span class="p">[</span><span class="mi">0</span><span class="p">]</span>
    <span class="n">yspan</span> <span class="o">=</span> <span class="n">ylim</span><span class="p">[</span><span class="mi">1</span><span class="p">]</span> <span class="o">-</span> <span class="n">xlim</span><span class="p">[</span><span class="mi">0</span><span class="p">]</span>

    <span class="n">xax_lim</span> <span class="o">=</span> <span class="p">(</span><span class="n">xlim</span><span class="p">[</span><span class="mi">0</span><span class="p">]</span> <span class="o">-</span> <span class="n">ax_extend</span> <span class="o">*</span> <span class="n">xspan</span><span class="p">,</span>
               <span class="n">xlim</span><span class="p">[</span><span class="mi">1</span><span class="p">]</span> <span class="o">+</span> <span class="n">ax_extend</span> <span class="o">*</span> <span class="n">xspan</span><span class="p">)</span>
    <span class="n">yax_lim</span> <span class="o">=</span> <span class="p">(</span><span class="n">ylim</span><span class="p">[</span><span class="mi">0</span><span class="p">]</span> <span class="o">-</span> <span class="n">ax_extend</span> <span class="o">*</span> <span class="n">yspan</span><span class="p">,</span>
               <span class="n">ylim</span><span class="p">[</span><span class="mi">1</span><span class="p">]</span> <span class="o">+</span> <span class="n">ax_extend</span> <span class="o">*</span> <span class="n">yspan</span><span class="p">)</span>

    <span class="k">if</span> <span class="n">xaxis_loc</span> <span class="ow">is</span> <span class="bp">None</span><span class="p">:</span>
        <span class="n">xaxis_loc</span> <span class="o">=</span> <span class="n">ylim</span><span class="p">[</span><span class="mi">0</span><span class="p">]</span>

    <span class="k">if</span> <span class="n">yaxis_loc</span> <span class="ow">is</span> <span class="bp">None</span><span class="p">:</span>
        <span class="n">yaxis_loc</span> <span class="o">=</span> <span class="n">xlim</span><span class="p">[</span><span class="mi">0</span><span class="p">]</span>

    <span class="c"># Draw axes</span>
    <span class="n">xaxis</span> <span class="o">=</span> <span class="n">pl</span><span class="o">.</span><span class="n">Line2D</span><span class="p">([</span><span class="n">xax_lim</span><span class="p">[</span><span class="mi">0</span><span class="p">],</span> <span class="n">xax_lim</span><span class="p">[</span><span class="mi">1</span><span class="p">]],</span> <span class="p">[</span><span class="n">xaxis_loc</span><span class="p">,</span> <span class="n">xaxis_loc</span><span class="p">],</span>
                      <span class="n">linestyle</span><span class="o">=</span><span class="s">&#39;-&#39;</span><span class="p">,</span> <span class="n">color</span><span class="o">=</span><span class="s">&#39;k&#39;</span><span class="p">)</span>
    <span class="n">yaxis</span> <span class="o">=</span> <span class="n">pl</span><span class="o">.</span><span class="n">Line2D</span><span class="p">([</span><span class="n">yaxis_loc</span><span class="p">,</span> <span class="n">yaxis_loc</span><span class="p">],</span> <span class="p">[</span><span class="n">yax_lim</span><span class="p">[</span><span class="mi">0</span><span class="p">],</span> <span class="n">yax_lim</span><span class="p">[</span><span class="mi">1</span><span class="p">]],</span>
                      <span class="n">linestyle</span><span class="o">=</span><span class="s">&#39;-&#39;</span><span class="p">,</span> <span class="n">color</span><span class="o">=</span><span class="s">&#39;k&#39;</span><span class="p">)</span>

    <span class="c"># Label axes3, 0.5, &#39;hello&#39;, fontsize=14)</span>
    <span class="n">ax</span><span class="o">.</span><span class="n">text</span><span class="p">(</span><span class="n">xax_lim</span><span class="p">[</span><span class="mi">1</span><span class="p">],</span> <span class="n">xaxis_loc</span> <span class="o">-</span> <span class="mf">0.02</span> <span class="o">*</span> <span class="n">yspan</span><span class="p">,</span> <span class="n">ax</span><span class="o">.</span><span class="n">get_xlabel</span><span class="p">(),</span>
            <span class="n">fontsize</span><span class="o">=</span><span class="mi">14</span><span class="p">,</span> <span class="n">ha</span><span class="o">=</span><span class="s">&#39;right&#39;</span><span class="p">,</span> <span class="n">va</span><span class="o">=</span><span class="s">&#39;top&#39;</span><span class="p">,</span> <span class="n">rotation</span><span class="o">=</span><span class="mi">12</span><span class="p">)</span>
    <span class="n">ax</span><span class="o">.</span><span class="n">text</span><span class="p">(</span><span class="n">yaxis_loc</span> <span class="o">-</span> <span class="mf">0.02</span> <span class="o">*</span> <span class="n">xspan</span><span class="p">,</span> <span class="n">yax_lim</span><span class="p">[</span><span class="mi">1</span><span class="p">],</span> <span class="n">ax</span><span class="o">.</span><span class="n">get_ylabel</span><span class="p">(),</span>
            <span class="n">fontsize</span><span class="o">=</span><span class="mi">14</span><span class="p">,</span> <span class="n">ha</span><span class="o">=</span><span class="s">&#39;right&#39;</span><span class="p">,</span> <span class="n">va</span><span class="o">=</span><span class="s">&#39;top&#39;</span><span class="p">,</span> <span class="n">rotation</span><span class="o">=</span><span class="mi">78</span><span class="p">)</span>
    <span class="n">ax</span><span class="o">.</span><span class="n">set_xlabel</span><span class="p">(</span><span class="s">&#39;&#39;</span><span class="p">)</span>
    <span class="n">ax</span><span class="o">.</span><span class="n">set_ylabel</span><span class="p">(</span><span class="s">&#39;&#39;</span><span class="p">)</span>

    <span class="c"># Add title</span>
    <span class="n">ax</span><span class="o">.</span><span class="n">text</span><span class="p">(</span><span class="mf">0.5</span> <span class="o">*</span> <span class="p">(</span><span class="n">xax_lim</span><span class="p">[</span><span class="mi">1</span><span class="p">]</span> <span class="o">+</span> <span class="n">xax_lim</span><span class="p">[</span><span class="mi">0</span><span class="p">]),</span> <span class="n">yax_lim</span><span class="p">[</span><span class="mi">1</span><span class="p">],</span>
            <span class="n">ax</span><span class="o">.</span><span class="n">get_title</span><span class="p">(),</span>
            <span class="n">ha</span><span class="o">=</span><span class="s">&#39;center&#39;</span><span class="p">,</span> <span class="n">va</span><span class="o">=</span><span class="s">&#39;bottom&#39;</span><span class="p">,</span> <span class="n">fontsize</span><span class="o">=</span><span class="mi">16</span><span class="p">)</span>
    <span class="n">ax</span><span class="o">.</span><span class="n">set_title</span><span class="p">(</span><span class="s">&#39;&#39;</span><span class="p">)</span>

    <span class="n">Nlines</span> <span class="o">=</span> <span class="nb">len</span><span class="p">(</span><span class="n">ax</span><span class="o">.</span><span class="n">lines</span><span class="p">)</span>
    <span class="n">lines</span> <span class="o">=</span> <span class="p">[</span><span class="n">xaxis</span><span class="p">,</span> <span class="n">yaxis</span><span class="p">]</span> <span class="o">+</span> <span class="p">[</span><span class="n">ax</span><span class="o">.</span><span class="n">lines</span><span class="o">.</span><span class="n">pop</span><span class="p">(</span><span class="mi">0</span><span class="p">)</span> <span class="k">for</span> <span class="n">i</span> <span class="ow">in</span> <span class="nb">range</span><span class="p">(</span><span class="n">Nlines</span><span class="p">)]</span>

    <span class="k">for</span> <span class="n">line</span> <span class="ow">in</span> <span class="n">lines</span><span class="p">:</span>
        <span class="n">x</span><span class="p">,</span> <span class="n">y</span> <span class="o">=</span> <span class="n">line</span><span class="o">.</span><span class="n">get_data</span><span class="p">()</span>

        <span class="n">x_int</span><span class="p">,</span> <span class="n">y_int</span> <span class="o">=</span> <span class="n">xkcd_line</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="n">y</span><span class="p">,</span> <span class="n">xlim</span><span class="p">,</span> <span class="n">ylim</span><span class="p">,</span>
                                 <span class="n">mag</span><span class="p">,</span> <span class="n">f1</span><span class="p">,</span> <span class="n">f2</span><span class="p">,</span> <span class="n">f3</span><span class="p">)</span>

        <span class="c"># create foreground and background line</span>
        <span class="n">lw</span> <span class="o">=</span> <span class="n">line</span><span class="o">.</span><span class="n">get_linewidth</span><span class="p">()</span>
        <span class="n">line</span><span class="o">.</span><span class="n">set_linewidth</span><span class="p">(</span><span class="mi">2</span> <span class="o">*</span> <span class="n">lw</span><span class="p">)</span>
        <span class="n">line</span><span class="o">.</span><span class="n">set_data</span><span class="p">(</span><span class="n">x_int</span><span class="p">,</span> <span class="n">y_int</span><span class="p">)</span>

        <span class="c"># don&#39;t add background line for axes</span>
        <span class="k">if</span> <span class="p">(</span><span class="n">line</span> <span class="ow">is</span> <span class="ow">not</span> <span class="n">xaxis</span><span class="p">)</span> <span class="ow">and</span> <span class="p">(</span><span class="n">line</span> <span class="ow">is</span> <span class="ow">not</span> <span class="n">yaxis</span><span class="p">):</span>
            <span class="n">line_bg</span> <span class="o">=</span> <span class="n">pl</span><span class="o">.</span><span class="n">Line2D</span><span class="p">(</span><span class="n">x_int</span><span class="p">,</span> <span class="n">y_int</span><span class="p">,</span> <span class="n">color</span><span class="o">=</span><span class="n">bgcolor</span><span class="p">,</span>
                                <span class="n">linewidth</span><span class="o">=</span><span class="mi">8</span> <span class="o">*</span> <span class="n">lw</span><span class="p">)</span>

            <span class="n">ax</span><span class="o">.</span><span class="n">add_line</span><span class="p">(</span><span class="n">line_bg</span><span class="p">)</span>
        <span class="n">ax</span><span class="o">.</span><span class="n">add_line</span><span class="p">(</span><span class="n">line</span><span class="p">)</span>

    <span class="c"># Draw arrow-heads at the end of axes lines</span>
    <span class="n">arr1</span> <span class="o">=</span> <span class="mf">0.03</span> <span class="o">*</span> <span class="n">np</span><span class="o">.</span><span class="n">array</span><span class="p">([</span><span class="o">-</span><span class="mi">1</span><span class="p">,</span> <span class="mi">0</span><span class="p">,</span> <span class="o">-</span><span class="mi">1</span><span class="p">])</span>
    <span class="n">arr2</span> <span class="o">=</span> <span class="mf">0.02</span> <span class="o">*</span> <span class="n">np</span><span class="o">.</span><span class="n">array</span><span class="p">([</span><span class="o">-</span><span class="mi">1</span><span class="p">,</span> <span class="mi">0</span><span class="p">,</span> <span class="mi">1</span><span class="p">])</span>

    <span class="n">arr1</span><span class="p">[::</span><span class="mi">2</span><span class="p">]</span> <span class="o">+=</span> <span class="n">np</span><span class="o">.</span><span class="n">random</span><span class="o">.</span><span class="n">normal</span><span class="p">(</span><span class="mi">0</span><span class="p">,</span> <span class="mf">0.005</span><span class="p">,</span> <span class="mi">2</span><span class="p">)</span>
    <span class="n">arr2</span><span class="p">[::</span><span class="mi">2</span><span class="p">]</span> <span class="o">+=</span> <span class="n">np</span><span class="o">.</span><span class="n">random</span><span class="o">.</span><span class="n">normal</span><span class="p">(</span><span class="mi">0</span><span class="p">,</span> <span class="mf">0.005</span><span class="p">,</span> <span class="mi">2</span><span class="p">)</span>

    <span class="n">x</span><span class="p">,</span> <span class="n">y</span> <span class="o">=</span> <span class="n">xaxis</span><span class="o">.</span><span class="n">get_data</span><span class="p">()</span>
    <span class="k">if</span> <span class="s">&#39;+&#39;</span> <span class="ow">in</span> <span class="nb">str</span><span class="p">(</span><span class="n">xaxis_arrow</span><span class="p">):</span>
        <span class="n">ax</span><span class="o">.</span><span class="n">plot</span><span class="p">(</span><span class="n">x</span><span class="p">[</span><span class="o">-</span><span class="mi">1</span><span class="p">]</span> <span class="o">+</span> <span class="n">arr1</span> <span class="o">*</span> <span class="n">xspan</span> <span class="o">*</span> <span class="n">aspect</span><span class="p">,</span>
                <span class="n">y</span><span class="p">[</span><span class="o">-</span><span class="mi">1</span><span class="p">]</span> <span class="o">+</span> <span class="n">arr2</span> <span class="o">*</span> <span class="n">yspan</span><span class="p">,</span>
                <span class="n">color</span><span class="o">=</span><span class="s">&#39;k&#39;</span><span class="p">,</span> <span class="n">lw</span><span class="o">=</span><span class="mi">2</span><span class="p">)</span>
    <span class="k">if</span> <span class="s">&#39;-&#39;</span> <span class="ow">in</span> <span class="nb">str</span><span class="p">(</span><span class="n">xaxis_arrow</span><span class="p">):</span>
        <span class="n">ax</span><span class="o">.</span><span class="n">plot</span><span class="p">(</span><span class="n">x</span><span class="p">[</span><span class="mi">0</span><span class="p">]</span> <span class="o">-</span> <span class="n">arr1</span> <span class="o">*</span> <span class="n">xspan</span> <span class="o">*</span> <span class="n">aspect</span><span class="p">,</span>
                <span class="n">y</span><span class="p">[</span><span class="mi">0</span><span class="p">]</span> <span class="o">-</span> <span class="n">arr2</span> <span class="o">*</span> <span class="n">yspan</span><span class="p">,</span>
                <span class="n">color</span><span class="o">=</span><span class="s">&#39;k&#39;</span><span class="p">,</span> <span class="n">lw</span><span class="o">=</span><span class="mi">2</span><span class="p">)</span>

    <span class="n">x</span><span class="p">,</span> <span class="n">y</span> <span class="o">=</span> <span class="n">yaxis</span><span class="o">.</span><span class="n">get_data</span><span class="p">()</span>
    <span class="k">if</span> <span class="s">&#39;+&#39;</span> <span class="ow">in</span> <span class="nb">str</span><span class="p">(</span><span class="n">yaxis_arrow</span><span class="p">):</span>
        <span class="n">ax</span><span class="o">.</span><span class="n">plot</span><span class="p">(</span><span class="n">x</span><span class="p">[</span><span class="o">-</span><span class="mi">1</span><span class="p">]</span> <span class="o">+</span> <span class="n">arr2</span> <span class="o">*</span> <span class="n">xspan</span> <span class="o">*</span> <span class="n">aspect</span><span class="p">,</span>
                <span class="n">y</span><span class="p">[</span><span class="o">-</span><span class="mi">1</span><span class="p">]</span> <span class="o">+</span> <span class="n">arr1</span> <span class="o">*</span> <span class="n">yspan</span><span class="p">,</span>
                <span class="n">color</span><span class="o">=</span><span class="s">&#39;k&#39;</span><span class="p">,</span> <span class="n">lw</span><span class="o">=</span><span class="mi">2</span><span class="p">)</span>
    <span class="k">if</span> <span class="s">&#39;-&#39;</span> <span class="ow">in</span> <span class="nb">str</span><span class="p">(</span><span class="n">yaxis_arrow</span><span class="p">):</span>
        <span class="n">ax</span><span class="o">.</span><span class="n">plot</span><span class="p">(</span><span class="n">x</span><span class="p">[</span><span class="mi">0</span><span class="p">]</span> <span class="o">-</span> <span class="n">arr2</span> <span class="o">*</span> <span class="n">xspan</span> <span class="o">*</span> <span class="n">aspect</span><span class="p">,</span>
                <span class="n">y</span><span class="p">[</span><span class="mi">0</span><span class="p">]</span> <span class="o">-</span> <span class="n">arr1</span> <span class="o">*</span> <span class="n">yspan</span><span class="p">,</span>
                <span class="n">color</span><span class="o">=</span><span class="s">&#39;k&#39;</span><span class="p">,</span> <span class="n">lw</span><span class="o">=</span><span class="mi">2</span><span class="p">)</span>

    <span class="c"># Change all the fonts to humor-sans.</span>
    <span class="n">prop</span> <span class="o">=</span> <span class="n">fm</span><span class="o">.</span><span class="n">FontProperties</span><span class="p">(</span><span class="n">fname</span><span class="o">=</span><span class="s">&#39;Humor-Sans.ttf&#39;</span><span class="p">,</span> <span class="n">size</span><span class="o">=</span><span class="mi">16</span><span class="p">)</span>
    <span class="k">for</span> <span class="n">text</span> <span class="ow">in</span> <span class="n">ax</span><span class="o">.</span><span class="n">texts</span><span class="p">:</span>
        <span class="n">text</span><span class="o">.</span><span class="n">set_fontproperties</span><span class="p">(</span><span class="n">prop</span><span class="p">)</span>
    
    <span class="c"># modify legend</span>
    <span class="n">leg</span> <span class="o">=</span> <span class="n">ax</span><span class="o">.</span><span class="n">get_legend</span><span class="p">()</span>
    <span class="k">if</span> <span class="n">leg</span> <span class="ow">is</span> <span class="ow">not</span> <span class="bp">None</span><span class="p">:</span>
        <span class="n">leg</span><span class="o">.</span><span class="n">set_frame_on</span><span class="p">(</span><span class="bp">False</span><span class="p">)</span>
        
        <span class="k">for</span> <span class="n">child</span> <span class="ow">in</span> <span class="n">leg</span><span class="o">.</span><span class="n">get_children</span><span class="p">():</span>
            <span class="k">if</span> <span class="nb">isinstance</span><span class="p">(</span><span class="n">child</span><span class="p">,</span> <span class="n">pl</span><span class="o">.</span><span class="n">Line2D</span><span class="p">):</span>
                <span class="n">x</span><span class="p">,</span> <span class="n">y</span> <span class="o">=</span> <span class="n">child</span><span class="o">.</span><span class="n">get_data</span><span class="p">()</span>
                <span class="n">child</span><span class="o">.</span><span class="n">set_data</span><span class="p">(</span><span class="n">xkcd_line</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="n">y</span><span class="p">,</span> <span class="n">mag</span><span class="o">=</span><span class="mi">10</span><span class="p">,</span> <span class="n">f1</span><span class="o">=</span><span class="mi">100</span><span class="p">,</span> <span class="n">f2</span><span class="o">=</span><span class="mf">0.001</span><span class="p">))</span>
                <span class="n">child</span><span class="o">.</span><span class="n">set_linewidth</span><span class="p">(</span><span class="mi">2</span> <span class="o">*</span> <span class="n">child</span><span class="o">.</span><span class="n">get_linewidth</span><span class="p">())</span>
            <span class="k">if</span> <span class="nb">isinstance</span><span class="p">(</span><span class="n">child</span><span class="p">,</span> <span class="n">pl</span><span class="o">.</span><span class="n">Text</span><span class="p">):</span>
                <span class="n">child</span><span class="o">.</span><span class="n">set_fontproperties</span><span class="p">(</span><span class="n">prop</span><span class="p">)</span>
    
    <span class="c"># Set the axis limits</span>
    <span class="n">ax</span><span class="o">.</span><span class="n">set_xlim</span><span class="p">(</span><span class="n">xax_lim</span><span class="p">[</span><span class="mi">0</span><span class="p">]</span> <span class="o">-</span> <span class="mf">0.1</span> <span class="o">*</span> <span class="n">xspan</span><span class="p">,</span>
                <span class="n">xax_lim</span><span class="p">[</span><span class="mi">1</span><span class="p">]</span> <span class="o">+</span> <span class="mf">0.1</span> <span class="o">*</span> <span class="n">xspan</span><span class="p">)</span>
    <span class="n">ax</span><span class="o">.</span><span class="n">set_ylim</span><span class="p">(</span><span class="n">yax_lim</span><span class="p">[</span><span class="mi">0</span><span class="p">]</span> <span class="o">-</span> <span class="mf">0.1</span> <span class="o">*</span> <span class="n">yspan</span><span class="p">,</span>
                <span class="n">yax_lim</span><span class="p">[</span><span class="mi">1</span><span class="p">]</span> <span class="o">+</span> <span class="mf">0.1</span> <span class="o">*</span> <span class="n">yspan</span><span class="p">)</span>

    <span class="c"># adjust the axes</span>
    <span class="n">ax</span><span class="o">.</span><span class="n">set_xticks</span><span class="p">([])</span>
    <span class="n">ax</span><span class="o">.</span><span class="n">set_yticks</span><span class="p">([])</span>      

    <span class="k">if</span> <span class="n">expand_axes</span><span class="p">:</span>
        <span class="n">ax</span><span class="o">.</span><span class="n">figure</span><span class="o">.</span><span class="n">set_facecolor</span><span class="p">(</span><span class="n">bgcolor</span><span class="p">)</span>
        <span class="n">ax</span><span class="o">.</span><span class="n">set_axis_off</span><span class="p">()</span>
        <span class="n">ax</span><span class="o">.</span><span class="n">set_position</span><span class="p">([</span><span class="mi">0</span><span class="p">,</span> <span class="mi">0</span><span class="p">,</span> <span class="mi">1</span><span class="p">,</span> <span class="mi">1</span><span class="p">])</span>
    
    <span class="k">return</span> <span class="n">ax</span>
</pre></div>



## Testing it Out

Let's test this out with a simple plot.  We'll plot two curves, add some labels,
and then call ``XKCDify`` on the axis.  I think the results are pretty nice!

<div class="highlight"><pre><span class="o">%</span><span class="k">pylab</span> <span class="n">inline</span>
</pre></div>


    
    Welcome to pylab, a matplotlib-based Python environment [backend: module://IPython.zmq.pylab.backend_inline].
    For more information, type 'help(pylab)'.


<div class="highlight"><pre><span class="n">np</span><span class="o">.</span><span class="n">random</span><span class="o">.</span><span class="n">seed</span><span class="p">(</span><span class="mi">0</span><span class="p">)</span>

<span class="n">ax</span> <span class="o">=</span> <span class="n">pylab</span><span class="o">.</span><span class="n">axes</span><span class="p">()</span>

<span class="n">x</span> <span class="o">=</span> <span class="n">np</span><span class="o">.</span><span class="n">linspace</span><span class="p">(</span><span class="mi">0</span><span class="p">,</span> <span class="mi">10</span><span class="p">,</span> <span class="mi">100</span><span class="p">)</span>
<span class="n">ax</span><span class="o">.</span><span class="n">plot</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="n">np</span><span class="o">.</span><span class="n">sin</span><span class="p">(</span><span class="n">x</span><span class="p">)</span> <span class="o">*</span> <span class="n">np</span><span class="o">.</span><span class="n">exp</span><span class="p">(</span><span class="o">-</span><span class="mf">0.1</span> <span class="o">*</span> <span class="p">(</span><span class="n">x</span> <span class="o">-</span> <span class="mi">5</span><span class="p">)</span> <span class="o">**</span> <span class="mi">2</span><span class="p">),</span> <span class="s">&#39;b&#39;</span><span class="p">,</span> <span class="n">lw</span><span class="o">=</span><span class="mi">1</span><span class="p">,</span> <span class="n">label</span><span class="o">=</span><span class="s">&#39;damped sine&#39;</span><span class="p">)</span>
<span class="n">ax</span><span class="o">.</span><span class="n">plot</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="o">-</span><span class="n">np</span><span class="o">.</span><span class="n">cos</span><span class="p">(</span><span class="n">x</span><span class="p">)</span> <span class="o">*</span> <span class="n">np</span><span class="o">.</span><span class="n">exp</span><span class="p">(</span><span class="o">-</span><span class="mf">0.1</span> <span class="o">*</span> <span class="p">(</span><span class="n">x</span> <span class="o">-</span> <span class="mi">5</span><span class="p">)</span> <span class="o">**</span> <span class="mi">2</span><span class="p">),</span> <span class="s">&#39;r&#39;</span><span class="p">,</span> <span class="n">lw</span><span class="o">=</span><span class="mi">1</span><span class="p">,</span> <span class="n">label</span><span class="o">=</span><span class="s">&#39;damped cosine&#39;</span><span class="p">)</span>

<span class="n">ax</span><span class="o">.</span><span class="n">set_title</span><span class="p">(</span><span class="s">&#39;check it out!&#39;</span><span class="p">)</span>
<span class="n">ax</span><span class="o">.</span><span class="n">set_xlabel</span><span class="p">(</span><span class="s">&#39;x label&#39;</span><span class="p">)</span>
<span class="n">ax</span><span class="o">.</span><span class="n">set_ylabel</span><span class="p">(</span><span class="s">&#39;y label&#39;</span><span class="p">)</span>

<span class="n">ax</span><span class="o">.</span><span class="n">legend</span><span class="p">(</span><span class="n">loc</span><span class="o">=</span><span class="s">&#39;lower right&#39;</span><span class="p">)</span>

<span class="n">ax</span><span class="o">.</span><span class="n">set_xlim</span><span class="p">(</span><span class="mi">0</span><span class="p">,</span> <span class="mi">10</span><span class="p">)</span>
<span class="n">ax</span><span class="o">.</span><span class="n">set_ylim</span><span class="p">(</span><span class="o">-</span><span class="mf">1.0</span><span class="p">,</span> <span class="mf">1.0</span><span class="p">)</span>

<span class="c">#XKCDify the axes -- this operates in-place</span>
<span class="n">XKCDify</span><span class="p">(</span><span class="n">ax</span><span class="p">,</span> <span class="n">xaxis_loc</span><span class="o">=</span><span class="mf">0.0</span><span class="p">,</span> <span class="n">yaxis_loc</span><span class="o">=</span><span class="mf">1.0</span><span class="p">,</span>
        <span class="n">xaxis_arrow</span><span class="o">=</span><span class="s">&#39;+-&#39;</span><span class="p">,</span> <span class="n">yaxis_arrow</span><span class="o">=</span><span class="s">&#39;+-&#39;</span><span class="p">,</span>
        <span class="n">expand_axes</span><span class="o">=</span><span class="bp">True</span><span class="p">)</span>
</pre></div>


<pre>
    <matplotlib.axes.AxesSubplot at 0x2fecbd0>
</pre>


![](tests/ipynbref/XKCD_plots_orig_files/XKCD_plots_orig_fig_00.png)


## Duplicating an XKCD Comic

Now let's see if we can use this to replicated an XKCD comic in matplotlib.
This is a good one:

<div class="highlight"><pre><span class="n">Image</span><span class="p">(</span><span class="s">&#39;http://imgs.xkcd.com/comics/front_door.png&#39;</span><span class="p">)</span>
</pre></div>


<pre>
    <IPython.core.display.Image at 0x2ff4a10>
</pre>


With the new ``XKCDify`` function, this is relatively easy to replicate.  The results
are not exactly identical, but I think it definitely gets the point across!

<div class="highlight"><pre><span class="c"># Some helper functions</span>
<span class="k">def</span> <span class="nf">norm</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="n">x0</span><span class="p">,</span> <span class="n">sigma</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">np</span><span class="o">.</span><span class="n">exp</span><span class="p">(</span><span class="o">-</span><span class="mf">0.5</span> <span class="o">*</span> <span class="p">(</span><span class="n">x</span> <span class="o">-</span> <span class="n">x0</span><span class="p">)</span> <span class="o">**</span> <span class="mi">2</span> <span class="o">/</span> <span class="n">sigma</span> <span class="o">**</span> <span class="mi">2</span><span class="p">)</span>

<span class="k">def</span> <span class="nf">sigmoid</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="n">x0</span><span class="p">,</span> <span class="n">alpha</span><span class="p">):</span>
    <span class="k">return</span> <span class="mf">1.</span> <span class="o">/</span> <span class="p">(</span><span class="mf">1.</span> <span class="o">+</span> <span class="n">np</span><span class="o">.</span><span class="n">exp</span><span class="p">(</span><span class="o">-</span> <span class="p">(</span><span class="n">x</span> <span class="o">-</span> <span class="n">x0</span><span class="p">)</span> <span class="o">/</span> <span class="n">alpha</span><span class="p">))</span>
    
<span class="c"># define the curves</span>
<span class="n">x</span> <span class="o">=</span> <span class="n">np</span><span class="o">.</span><span class="n">linspace</span><span class="p">(</span><span class="mi">0</span><span class="p">,</span> <span class="mi">1</span><span class="p">,</span> <span class="mi">100</span><span class="p">)</span>
<span class="n">y1</span> <span class="o">=</span> <span class="n">np</span><span class="o">.</span><span class="n">sqrt</span><span class="p">(</span><span class="n">norm</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="mf">0.7</span><span class="p">,</span> <span class="mf">0.05</span><span class="p">))</span> <span class="o">+</span> <span class="mf">0.2</span> <span class="o">*</span> <span class="p">(</span><span class="mf">1.5</span> <span class="o">-</span> <span class="n">sigmoid</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="mf">0.8</span><span class="p">,</span> <span class="mf">0.05</span><span class="p">))</span>

<span class="n">y2</span> <span class="o">=</span> <span class="mf">0.2</span> <span class="o">*</span> <span class="n">norm</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="mf">0.5</span><span class="p">,</span> <span class="mf">0.2</span><span class="p">)</span> <span class="o">+</span> <span class="n">np</span><span class="o">.</span><span class="n">sqrt</span><span class="p">(</span><span class="n">norm</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="mf">0.6</span><span class="p">,</span> <span class="mf">0.05</span><span class="p">))</span> <span class="o">+</span> <span class="mf">0.1</span> <span class="o">*</span> <span class="p">(</span><span class="mi">1</span> <span class="o">-</span> <span class="n">sigmoid</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="mf">0.75</span><span class="p">,</span> <span class="mf">0.05</span><span class="p">))</span>

<span class="n">y3</span> <span class="o">=</span> <span class="mf">0.05</span> <span class="o">+</span> <span class="mf">1.4</span> <span class="o">*</span> <span class="n">norm</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="mf">0.85</span><span class="p">,</span> <span class="mf">0.08</span><span class="p">)</span>
<span class="n">y3</span><span class="p">[</span><span class="n">x</span> <span class="o">&gt;</span> <span class="mf">0.85</span><span class="p">]</span> <span class="o">=</span> <span class="mf">0.05</span> <span class="o">+</span> <span class="mf">1.4</span> <span class="o">*</span> <span class="n">norm</span><span class="p">(</span><span class="n">x</span><span class="p">[</span><span class="n">x</span> <span class="o">&gt;</span> <span class="mf">0.85</span><span class="p">],</span> <span class="mf">0.85</span><span class="p">,</span> <span class="mf">0.3</span><span class="p">)</span>

<span class="c"># draw the curves</span>
<span class="n">ax</span> <span class="o">=</span> <span class="n">pl</span><span class="o">.</span><span class="n">axes</span><span class="p">()</span>
<span class="n">ax</span><span class="o">.</span><span class="n">plot</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="n">y1</span><span class="p">,</span> <span class="n">c</span><span class="o">=</span><span class="s">&#39;gray&#39;</span><span class="p">)</span>
<span class="n">ax</span><span class="o">.</span><span class="n">plot</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="n">y2</span><span class="p">,</span> <span class="n">c</span><span class="o">=</span><span class="s">&#39;blue&#39;</span><span class="p">)</span>
<span class="n">ax</span><span class="o">.</span><span class="n">plot</span><span class="p">(</span><span class="n">x</span><span class="p">,</span> <span class="n">y3</span><span class="p">,</span> <span class="n">c</span><span class="o">=</span><span class="s">&#39;red&#39;</span><span class="p">)</span>

<span class="n">ax</span><span class="o">.</span><span class="n">text</span><span class="p">(</span><span class="mf">0.3</span><span class="p">,</span> <span class="o">-</span><span class="mf">0.1</span><span class="p">,</span> <span class="s">&quot;Yard&quot;</span><span class="p">)</span>
<span class="n">ax</span><span class="o">.</span><span class="n">text</span><span class="p">(</span><span class="mf">0.5</span><span class="p">,</span> <span class="o">-</span><span class="mf">0.1</span><span class="p">,</span> <span class="s">&quot;Steps&quot;</span><span class="p">)</span>
<span class="n">ax</span><span class="o">.</span><span class="n">text</span><span class="p">(</span><span class="mf">0.7</span><span class="p">,</span> <span class="o">-</span><span class="mf">0.1</span><span class="p">,</span> <span class="s">&quot;Door&quot;</span><span class="p">)</span>
<span class="n">ax</span><span class="o">.</span><span class="n">text</span><span class="p">(</span><span class="mf">0.9</span><span class="p">,</span> <span class="o">-</span><span class="mf">0.1</span><span class="p">,</span> <span class="s">&quot;Inside&quot;</span><span class="p">)</span>

<span class="n">ax</span><span class="o">.</span><span class="n">text</span><span class="p">(</span><span class="mf">0.05</span><span class="p">,</span> <span class="mf">1.1</span><span class="p">,</span> <span class="s">&quot;fear that</span><span class="se">\n</span><span class="s">there&#39;s</span><span class="se">\n</span><span class="s">something</span><span class="se">\n</span><span class="s">behind me&quot;</span><span class="p">)</span>
<span class="n">ax</span><span class="o">.</span><span class="n">plot</span><span class="p">([</span><span class="mf">0.15</span><span class="p">,</span> <span class="mf">0.2</span><span class="p">],</span> <span class="p">[</span><span class="mf">1.0</span><span class="p">,</span> <span class="mf">0.2</span><span class="p">],</span> <span class="s">&#39;-k&#39;</span><span class="p">,</span> <span class="n">lw</span><span class="o">=</span><span class="mf">0.5</span><span class="p">)</span>

<span class="n">ax</span><span class="o">.</span><span class="n">text</span><span class="p">(</span><span class="mf">0.25</span><span class="p">,</span> <span class="mf">0.8</span><span class="p">,</span> <span class="s">&quot;forward</span><span class="se">\n</span><span class="s">speed&quot;</span><span class="p">)</span>
<span class="n">ax</span><span class="o">.</span><span class="n">plot</span><span class="p">([</span><span class="mf">0.32</span><span class="p">,</span> <span class="mf">0.35</span><span class="p">],</span> <span class="p">[</span><span class="mf">0.75</span><span class="p">,</span> <span class="mf">0.35</span><span class="p">],</span> <span class="s">&#39;-k&#39;</span><span class="p">,</span> <span class="n">lw</span><span class="o">=</span><span class="mf">0.5</span><span class="p">)</span>

<span class="n">ax</span><span class="o">.</span><span class="n">text</span><span class="p">(</span><span class="mf">0.9</span><span class="p">,</span> <span class="mf">0.4</span><span class="p">,</span> <span class="s">&quot;embarrassment&quot;</span><span class="p">)</span>
<span class="n">ax</span><span class="o">.</span><span class="n">plot</span><span class="p">([</span><span class="mf">1.0</span><span class="p">,</span> <span class="mf">0.8</span><span class="p">],</span> <span class="p">[</span><span class="mf">0.55</span><span class="p">,</span> <span class="mf">1.05</span><span class="p">],</span> <span class="s">&#39;-k&#39;</span><span class="p">,</span> <span class="n">lw</span><span class="o">=</span><span class="mf">0.5</span><span class="p">)</span>

<span class="n">ax</span><span class="o">.</span><span class="n">set_title</span><span class="p">(</span><span class="s">&quot;Walking back to my</span><span class="se">\n</span><span class="s">front door at night:&quot;</span><span class="p">)</span>

<span class="n">ax</span><span class="o">.</span><span class="n">set_xlim</span><span class="p">(</span><span class="mi">0</span><span class="p">,</span> <span class="mi">1</span><span class="p">)</span>
<span class="n">ax</span><span class="o">.</span><span class="n">set_ylim</span><span class="p">(</span><span class="mi">0</span><span class="p">,</span> <span class="mf">1.5</span><span class="p">)</span>

<span class="c"># modify all the axes elements in-place</span>
<span class="n">XKCDify</span><span class="p">(</span><span class="n">ax</span><span class="p">,</span> <span class="n">expand_axes</span><span class="o">=</span><span class="bp">True</span><span class="p">)</span>
</pre></div>


<pre>
    <matplotlib.axes.AxesSubplot at 0x2fef210>
</pre>


![](tests/ipynbref/XKCD_plots_orig_files/XKCD_plots_orig_fig_01.png)


Pretty good for a couple hours's work!

I think the possibilities here are pretty limitless: this is going to be a hugely
useful and popular feature in matplotlib, especially when the sketch artist PR is mature
and part of the main package.  I imagine using this style of plot for schematic figures
in presentations where the normal crisp matplotlib lines look a bit too "scientific".
I'm giving a few talks at the end of the month... maybe I'll even use some of
this code there.

This post was written entirely in an IPython Notebook: the notebook file is available for
download [here](http://jakevdp.github.com/downloads/notebooks/XKCD_plots.ipynb).
For more information on blogging with notebooks in octopress, see my
[previous post](http://jakevdp.github.com/blog/2012/10/04/blogging-with-ipython/)
on the subject.
