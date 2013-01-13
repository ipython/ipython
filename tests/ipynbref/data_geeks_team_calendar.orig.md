<div class="highlight"><pre><span class="c">#! /usr/bin/env python</span>
<span class="sd">&#39;&#39;&#39;</span>
<span class="sd">github_team_calendar.py</span>
<span class="sd">Python program to scrape friends github to build team calendar for github</span>
<span class="sd">&#39;&#39;&#39;</span>


<span class="kn">import</span> <span class="nn">json</span>
<span class="kn">import</span> <span class="nn">requests</span>
<span class="kn">import</span> <span class="nn">pandas</span> <span class="kn">as</span> <span class="nn">pd</span>


<span class="k">def</span> <span class="nf">line_draw_target</span><span class="p">(</span><span class="n">target</span><span class="p">):</span>                                                    
    <span class="n">github_url</span> <span class="o">=</span> <span class="s">&#39;https://github.com/users/</span><span class="si">%s</span><span class="s">/contributions_calendar_data&#39;</span>       
    <span class="n">r</span> <span class="o">=</span> <span class="n">requests</span><span class="o">.</span><span class="n">get</span><span class="p">(</span><span class="n">github_url</span> <span class="o">%</span> <span class="n">target</span><span class="p">)</span>                                                                                                                                                                                                                                                                                   
    <span class="n">data</span> <span class="o">=</span> <span class="n">json</span><span class="o">.</span><span class="n">loads</span><span class="p">(</span><span class="n">r</span><span class="o">.</span><span class="n">text</span><span class="p">)</span>                                                    
    <span class="n">dates</span><span class="p">,</span> <span class="n">contributions</span> <span class="o">=</span> <span class="nb">zip</span><span class="p">(</span><span class="o">*</span><span class="n">data</span><span class="p">)</span>                                            
    <span class="n">ts</span> <span class="o">=</span> <span class="n">pd</span><span class="o">.</span><span class="n">Series</span><span class="p">(</span><span class="n">contributions</span><span class="p">,</span> <span class="n">index</span><span class="o">=</span><span class="n">dates</span><span class="p">)</span>
    <span class="n">plt</span><span class="o">.</span><span class="n">plot</span><span class="p">(</span><span class="n">ts</span><span class="p">)</span>
</pre></div>



<div class="highlight"><pre><span class="n">target</span> <span class="o">=</span> <span class="s">&quot;mikedewar&quot;</span>
<span class="n">line_draw_target</span><span class="p">(</span><span class="n">target</span><span class="p">)</span>
        
</pre></div>



![](tests/ipynbref/data_geeks_team_calendar_orig_files/data_geeks_team_calendar_orig_fig_00.png)


<div class="highlight"><pre><span class="n">target</span> <span class="o">=</span> <span class="s">&quot;drewconway&quot;</span>
<span class="n">line_draw_target</span><span class="p">(</span><span class="n">target</span><span class="p">)</span>
</pre></div>



![](tests/ipynbref/data_geeks_team_calendar_orig_files/data_geeks_team_calendar_orig_fig_01.png)


<div class="highlight"><pre><span class="n">target</span> <span class="o">=</span> <span class="s">&quot;hmason&quot;</span>
<span class="n">line_draw_target</span><span class="p">(</span><span class="n">target</span><span class="p">)</span>
</pre></div>



![](tests/ipynbref/data_geeks_team_calendar_orig_files/data_geeks_team_calendar_orig_fig_02.png)


<div class="highlight"><pre><span class="n">target</span> <span class="o">=</span> <span class="s">&quot;mbostock&quot;</span>
<span class="n">line_draw_target</span><span class="p">(</span><span class="n">target</span><span class="p">)</span>
</pre></div>



![](tests/ipynbref/data_geeks_team_calendar_orig_files/data_geeks_team_calendar_orig_fig_03.png)


<div class="highlight"><pre><span class="n">target</span> <span class="o">=</span> <span class="s">&quot;amueller&quot;</span>
<span class="n">line_draw_target</span><span class="p">(</span><span class="n">target</span><span class="p">)</span>
</pre></div>



![](tests/ipynbref/data_geeks_team_calendar_orig_files/data_geeks_team_calendar_orig_fig_04.png)


