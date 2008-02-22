<?xml version="1.0" encoding="utf-8"?>
<?xml-stylesheet ekr_test?>
<leo_file>
<leo_header file_format="2" tnodes="0" max_tnode_index="0" clone_windows="0"/>
<globals body_outline_ratio="0.5">
	<global_window_position top="165" left="26" height="621" width="1280"/>
	<global_log_window_position top="0" left="0" height="0" width="0"/>
</globals>
<preferences/>
<find_panel_settings/>
<vnodes>
<v t="vivainio.20080218184525"><vh>@chapters</vh></v>
<v t="vivainio.20080218184540" a="E"><vh>@ipy-startup</vh>
<v t="vivainio.20080218184613.1"><vh>b</vh></v>
<v t="vivainio.20080218200031"><vh>Some classes P</vh>
<v t="vivainio.20080218190816"><vh>File-like access</vh></v>
<v t="vivainio.20080218200106"><vh>csv data</vh></v>
<v t="vivainio.20080219225120"><vh>String list</vh></v>
<v t="vivainio.20080219230342"><vh>slist to leo</vh></v>
</v>
</v>
<v t="vivainio.20080218195413"><vh>Class tests</vh>
<v t="vivainio.20080218200509"><vh>csvr</vh></v>
<v t="vivainio.20080218191007"><vh>tempfile</vh></v>
<v t="vivainio.20080218195413.1"><vh>rfile</vh></v>
<v t="vivainio.20080219225804"><vh>strlist</vh></v>
</v>
<v t="vivainio.20080218201219"><vh>Direct variables</vh>
<v t="vivainio.20080222201226"><vh>NewHeadline</vh></v>
<v t="vivainio.20080218201219.2"><vh>bar</vh></v>
</v>
<v t="vivainio.20080222193236" a="E"><vh>Docs</vh>
<v t="vivainio.20080222193236.1" a="TV"><vh>Quick intro</vh></v>
</v>
<v t="vivainio.20080222202211"><vh>test stuff</vh></v>
<v t="vivainio.20080222202211.1"><vh>spam</vh></v>
<v t="vivainio.20080222202211.2"><vh>NewHeadline</vh></v>
</vnodes>
<tnodes>
<t tx="vivainio.20080218184525">?</t>
<t tx="vivainio.20080218184540">?Direct children of this node will be pushed at ipython bridge startup

This node itself will *not* be pushed</t>
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
<t tx="vivainio.20080218200031">@others</t>
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
<t tx="vivainio.20080219230342">import ipy_leo
@ipy_leo.format_for_leo.when_type(IPython.genutils.SList)
def format_slist(obj):
    return "@cl slist\n" + obj.n
</t>
<t tx="vivainio.20080222193236"></t>
<t tx="vivainio.20080222193236.1">@wrap
@nocolor

Introduction
============

The purpose of ILeo, or leo-ipython bridge, is being a two-way communication
channel between Leo and IPython. The level of integration is much deeper than
conventional integration in IDEs; most notably, you are able to store *data* in
Leo nodes, in addition to mere program code. The possibilities of this are
endless, and this degree of integration has not been seen previously in the python
world.

IPython users are accustomed to using things like %edit to produce non-trivial
functions/classes (i.e. something that they don't want to enter directly on the
interactive prompt, but creating a proper script/module involves too much
overhead). In ILeo, this task consists just going to the Leo window, creating a node
and writing the code there, and pressing alt+I (push-to-ipython).

Obviously, you can save the Leo document as usual - this is a great advantage
of ILeo over using %edit, you can save your experimental scripts all at one
time, without having to organize them into script/module files (before you
really want to, of course!)


Installation
============

You need the latest version of Leo, and the development version of IPython (ILeo
will be incorporated to IPython 0.8.3.

You can get IPython from Launchpad by installing bzr and doing

bzr branch lp:ipython

and running "setup.py install".

You need to enable the 'ipython.py' plugin in Leo: 

- Help -&gt; Open LeoSettings.leo

- Edit @settings--&gt;Plugins--&gt;@enabled-plugins, add/uncomment 'ipython.py'

- Restart Leo. Be sure that you have the console window open (start leo.py from console, or double-click leo.py on windows)

- Press alt+5 OR alt-x start-ipython to launch IPython in the console that
started leo. You can start entering IPython commands normally, and Leo will keep
running in the same time.

Accessing IPython from Leo
==========================

IPython code
------------

Just enter IPython commands on a Leo node and press alt-I to execute
push-to-ipython to execute the script in IPython. 'commands' is interpreted
loosely here - you can enter function and class definitions, in addition to the
things you would usually enter at IPython prompt - calculations, system commands etc.

Everything that would be legal to enter on IPython prompt is legal to execute
from ILeo.

Results will be shows in Leo log window for convenience, in addition to the console.

Suppose that a node had the following contents:
{{{
1+2
print "hello"
3+4

def f(x):
    return x.upper()

f('hello world')
}}}

If you press alt+I on that done, you will see the following in Leo log window (IPython tab):
    
{{{
In: 1+2
&lt;2&gt; 3
In: 3+4
&lt;4&gt; 7
In: f('hello world')
&lt;6&gt; 'HELLO WORLD'
}}}

(numbers like &lt;6&gt; mean IPython output history indices).


Plain Python code
-----------------

If the headline of the node ends with capital P, alt-I will not run the code
through IPython translation mechanism but use the direct python 'exec' statement
(in IPython user namespace) to execute the code. It wont be shown in IPython
history, and sometimes it is safer (and more efficient) to execute things as
plain Python statements. Large class definitions are good candidates for P
nodes.

Accessing Leo nodes from IPython
================================

The real fun starts when you start entering text to leo nodes, and are using
that as data (input/output) for your IPython work.

Accessing Leo nodes happens through the variable 'wb' (short for "WorkBook")
that exist in the IPython user namespace. Nodes that are directly accessible are
the ones that have simple names which could also be Python variable names;
'foo_1' will be accessible directly from IPython, whereas 'my scripts' will not.
If you want to access a node with arbitrary headline, add a child node '@a foo'
(@a stands for 'anchor'). Then, the parent of '@a foo' is accessible through
'wb.foo'.

You can see what nodes are accessible be entering (in IPython) wb.&lt;TAB&gt;. Example:

[C:leo/src]|12&gt; wb.
wb.b           wb.tempfile    wb.rfile       wb.NewHeadline
wb.bar         wb.Docs        wb.strlist     wb.csvr    

Suppose that we had a node with headline 'spam' and body: 

['12',2222+32]

we can access it from IPython (or from scripts entered into other Leo nodes!) by doing:
    
C:leo/src]|19&gt; wb.spam.v
          &lt;19&gt; ['12', 2254]

'v' attribute stands for 'value', which means the node contents will be run
through 'eval' and everything you would be able to enter into IPython prompt
will be converted to objects. This mechanism can be extended far beyond direct
evaluation (see '@cl definitions').

'v' attribute also has a setter, i.e. you can do:

wb.spam.v = "mystring"

Which will result in the node 'spam' having the following text:

'mystring'

What assignment to 'v' does can be configured through generic functions
(simplegeneric module, will be explained later).

Besides v, you can set the body text directly through wb.spam.b =
"some\nstring", headline by wb.spam.h = 'new_headline' (obviously you must
access the node through wb.new_headline from that point onwards), and access the
contents as string list (IPython SList) through 'wb.spam.l'.

If you do 'wb.foo.v = 12' when node named 'foo' does not exist, the node titled
'foo' will be automatically created and assigned body 12.

@cl definitions
===============

If the first line in the body text is of the form '@cl sometext', IPython will
will evaluate 'sometext' and call the result with the rest of the body when you
do 'wb.foo.v'. An example is in place here. Suppose that we have defined a class
(I use the term class in a non-python sense here)

{{{
def rfile(body,n):
    """ @cl rfile 

    produces a StringIO (file like obj) of the rest of the body """

    import StringIO
    return StringIO.StringIO(body)
}}}

Now, let's say you node 'spam' with text

{{{
@cl rfile
hello
world
and whatever
}}}

Now, on IPython, we can do this:

{{{    
[C:leo/src]|22&gt; f = wb.spam.v
[C:leo/src]|23&gt; f
           &lt;23&gt; &lt;StringIO.StringIO instance at 0x04E7E490&gt;
[C:leo/src]|24&gt; f.readline()
           &lt;24&gt; u'hello\n'
[C:leo/src]|25&gt; f.readline()
           &lt;25&gt; u'world\n'
[C:leo/src]|26&gt; f.readline()
           &lt;26&gt; u'and whatever'
[C:leo/src]|27&gt; f.readline()
           &lt;27&gt; u''    
}}} 

You should declare new @cl types to make ILeo as convenient your problem domain as possible. For example, a "@cl etree" could return the elementtree object for xml content, or 

Special node types
==================

@ipy-startup
------------

If this node exist, the *direct children* of this will be pushed to IPython when
ILeo is started (you press alt+5). Use it to push your own @cl definitions etc.
The contents of of the node itself will be ignored.

@ipy-results
------------

When you create a new node (wb.foo.v = 'stuff'), the node foo will be created as
a child of this node. If @ipy-results does not exist, the new node will be created after the currently selected node.

@a nodes
--------

You can attach these as children of existing nodes to provide a way to access
nodes with arbitrary headlines, or to provide aliases to other nodes. If
multiple @a nodes are attached as children of a node, all the names can be used
to access the same object.

Acknowledgements &amp; History
==========================

This idea got started when I (Ville) saw this post by Edward Ream (the author of
Leo) on IPython developer mailing list:
    
    http://lists.ipython.scipy.org/pipermail/ipython-dev/2008-January/003551.html
    
I was using FreeMind as mind mapping software, and so I had an immediate use
case for Leo (which, incidentally, is superior to FreeMind as mind mapper). The
wheels started rolling, I got obsessed with the power of this concept
(everything clicked together), and Edwards excitement paralleled mine.
Everything was mind-bogglingly easy/trivial, something that is typical of all
revolutionary technologies (think Python here).

The discussion that "built" ILeo is here:
    http://sourceforge.net/forum/forum.php?thread_id=1911662&amp;forum_id=10226    

</t>
<t tx="vivainio.20080222201226">1+2
print "hello"
3+4

def f(x):
    return x.upper()

f('hello world')</t>
<t tx="vivainio.20080222202211"></t>
<t tx="vivainio.20080222202211.1">@cl rfile
hello
world
and whatever</t>
<t tx="vivainio.20080222202211.2"></t>
</tnodes>
</leo_file>
