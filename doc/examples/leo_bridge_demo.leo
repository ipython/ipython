<?xml version="1.0" encoding="utf-8"?>
<?xml-stylesheet ekr_test?>
<leo_file>
<leo_header file_format="2" tnodes="0" max_tnode_index="0" clone_windows="0"/>
<globals body_outline_ratio="0.5">
	<global_window_position top="250" left="207" height="621" width="1280"/>
	<global_log_window_position top="0" left="0" height="0" width="0"/>
</globals>
<preferences/>
<find_panel_settings/>
<vnodes>
<v t="vivainio.20080218184525"><vh>@chapters</vh></v>
<v t="vivainio.20080218184540" a="E"><vh>@ipy-startup</vh>
<v t="vivainio.20080218184613.1"><vh>b</vh></v>
<v t="vivainio.20080218200031" a="E"><vh>Some classes P</vh>
<v t="vivainio.20080218190816"><vh>File-like access</vh></v>
<v t="vivainio.20080218200106"><vh>csv data</vh></v>
<v t="vivainio.20080219225120"><vh>String list</vh></v>
<v t="vivainio.20080219230342" a="TV"><vh>slist to leo</vh></v>
</v>
</v>
<v t="vivainio.20080218195413"><vh>Class tests</vh>
<v t="vivainio.20080218200509"><vh>csvr</vh></v>
<v t="vivainio.20080218191007"><vh>tempfile</vh></v>
<v t="vivainio.20080218195413.1"><vh>rfile</vh></v>
<v t="vivainio.20080219225804"><vh>strlist</vh></v>
</v>
<v t="vivainio.20080218201219" a="E"><vh>Direct variables</vh>
<v t="vivainio.20080218201219.2" a="E"><vh>bar</vh></v>
</v>
</vnodes>
<tnodes>
<t tx="vivainio.20080218184525">?</t>
<t tx="vivainio.20080218184540"># this stuff will be pushed at ipython bridge startup

@others</t>
<t tx="vivainio.20080218184613.1">print "world"</t>
<t tx="vivainio.20080218190816">def rfile(body,n):
    """ @cl rfile 

    produces a StringIO (file like obj of the rest of the body) """

    import StringIO
    return StringIO.StringIO(body)

def tmpfile(body,n):
    """ @cl tmpfile

    Produces a temporary file, with node body as contents

    """
    import tempfile
    h, fname = tempfile.mkstemp()
    f = open(fname,'w')
    f.write(body)
    f.close()
    return fname
</t>
<t tx="vivainio.20080218191007">@cl tmpfile

Hello</t>
<t tx="vivainio.20080218195413">?</t>
<t tx="vivainio.20080218195413.1">@cl rfile
These
lines
should 
be
readable </t>
<t tx="vivainio.20080218200031"></t>
<t tx="vivainio.20080218200106">def csvdata(body,n):
    import csv
    d = csv.Sniffer().sniff(body)
    reader = csv.reader(body.splitlines(), dialect = d)
    return reader</t>
<t tx="vivainio.20080218200509">@cl csvdata

a,b,b
1,2,2</t>
<t tx="vivainio.20080218201219"></t>
<t tx="vivainio.20080218201219.2">@cl
"hello world"</t>
<t tx="vivainio.20080219225120">import IPython.genutils
def slist(body,n):
    return IPython.genutils.SList(body.splitlines())
</t>
<t tx="vivainio.20080219225804">@cl slist
hello
world
on
many
lines
</t>
<t tx="vivainio.20080219230342">@ipy_leo.format_for_leo.when_type(IPython.genutils.SList)
def format_slist(obj):
    return "@cl slist\n" + obj.n
</t>
</tnodes>
</leo_file>
