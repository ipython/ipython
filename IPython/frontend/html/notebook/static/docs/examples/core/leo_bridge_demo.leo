<?xml version="1.0" encoding="utf-8"?>
<?xml-stylesheet ekr_test?>
<leo_file>
<leo_header file_format="2" tnodes="0" max_tnode_index="0" clone_windows="0"/>
<globals body_outline_ratio="0.307814992026">
	<global_window_position top="257" left="131" height="627" width="1280"/>
	<global_log_window_position top="0" left="0" height="0" width="0"/>
</globals>
<preferences/>
<find_panel_settings/>
<vnodes>
<v t="vivainio.20080222193236" a="E"><vh>Documentation</vh>
<v t="vivainio.20080223121915" tnodeList="vivainio.20080223121915,vivainio.20080222193236.1,vivainio.20080223133858,vivainio.20080223133922,vivainio.20080223133947,vivainio.20080223134018,vivainio.20080223134100,vivainio.20080223134118,vivainio.20080223134433,vivainio.20080223142207,vivainio.20080223134136"><vh>@nosent ILeo_doc.txt</vh>
<v t="vivainio.20080222193236.1"><vh>Documentation</vh>
<v t="vivainio.20080223133858"><vh>Introduction</vh></v>
<v t="vivainio.20080223133922"><vh>Installation</vh></v>
<v t="vivainio.20080223133947"><vh>Accessing IPython from Leo</vh></v>
<v t="vivainio.20080223134018"><vh>Accessing Leo nodes from IPython</vh></v>
<v t="vivainio.20080223134100"><vh>Cl definitions</vh></v>
<v t="vivainio.20080223134118"><vh>Special node types</vh></v>
<v t="vivainio.20080223134433"><vh>Custom push</vh></v>
<v t="vivainio.20080223142207" a="E"><vh>Code snippets</vh></v>
<v t="vivainio.20080223134136"><vh>Acknowledgements and history</vh></v>
</v>
</v>
</v>
<v t="vivainio.20080218184525"><vh>@chapters</vh></v>
<v t="vivainio.20080223133721" a="E"><vh>@settings</vh>
<v t="vivainio.20080316092617"><vh>@@string ipython_argv = ipython -pylab</vh></v>
<v t="vivainio.20080223133721.1"><vh>@enabled-plugins</vh></v>
</v>
<v t="vivainio.20080218184540"><vh>@ipy-startup</vh>
<v t="vivainio.20080218184613.1"><vh>b</vh></v>
<v t="vivainio.20080218200031"><vh>Some classes P</vh>
<v t="vivainio.20080218190816"><vh>File-like access</vh></v>
<v t="vivainio.20080218200106"><vh>csv data</vh></v>
<v t="vivainio.20080219225120"><vh>String list</vh></v>
<v t="vivainio.20080219230342"><vh>slist to leo</vh></v>
</v>
</v>
<v t="vivainio.20080218195413" a="E"><vh>Class tests</vh>
<v t="vivainio.20080218200509"><vh>csvr</vh></v>
<v t="vivainio.20080218191007"><vh>tempfile</vh></v>
<v t="vivainio.20080218195413.1"><vh>rfile</vh></v>
<v t="vivainio.20080219225804"><vh>strlist</vh></v>
</v>
<v t="vivainio.20080222201226" a="V"><vh>IPython script push tests</vh></v>
<v t="vivainio.20080218201219" a="E"><vh>Direct variables</vh>
<v t="vivainio.20080218201219.2"><vh>bar</vh></v>
</v>
<v t="vivainio.20080316144536" a="E"><vh>pylab tests</vh>
<v t="vivainio.20080316145539.2"><vh>Generate testarr</vh></v>
<v t="vivainio.20080316085925"><vh>testarr</vh></v>
<v t="vivainio.20080316085950"><vh>Call plotter on testarr</vh></v>
</v>
<v t="vivainio.20080222202211"><vh>test stuff</vh></v>
<v t="vivainio.20080223142403"><vh>@ipy-results</vh>
<v t="vivainio.20080223142403.1"><vh>foo</vh></v>
</v>
<v t="vivainio.20080222202211.1" a="E"><vh>spam</vh></v>
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
<t tx="vivainio.20080222193236">?</t>
<t tx="vivainio.20080222193236.1">@wrap
@nocolor</t>
<t tx="vivainio.20080222201226"># test ipython script 'cleanup' with complex blocks
1+2
print "hello"
3+4

def f(x):
    return x.upper()


if 0:
    print "foo"
else:
    print "bar"

def g():
    pass

g()

if 1:
    if 1:
        print "hello"

        print "world"

if 1:
    print "hello"

    print "word"
else:
    print "foo"

    print "bar"
    print "baz"

try:
    raise Exception
except:
    print "exc ok"</t>
<t tx="vivainio.20080222202211"></t>
<t tx="vivainio.20080222202211.1" ipython="7d71005506636f6f7264737101284b0c4bde747102732e">@cl rfile
hello
world
and whatever</t>
<t tx="vivainio.20080223121915">@others
</t>
<t tx="vivainio.20080223133721"></t>
<t tx="vivainio.20080223133721.1">ipython.py</t>
<t tx="vivainio.20080223133858">
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
</t>
<t tx="vivainio.20080223133922">
Installation
============

You need at least Leo 4.4.7, and the development version of IPython (ILeo
will be incorporated to IPython 0.8.3).

You can get IPython from Launchpad by installing bzr and doing

bzr branch lp:ipython

and running "setup.py install".

You need to enable the 'ipython.py' plugin in Leo: 

- Help -&gt; Open LeoSettings.leo

- Edit @settings--&gt;Plugins--&gt;@enabled-plugins, add/uncomment 'ipython.py'

- Alternatively, you can add @settings--&gt;@enabled-plugins with body ipython.py to your leo document.

- Restart Leo. Be sure that you have the console window open (start leo.py from console, or double-click leo.py on windows)

- Press alt+5 OR alt-x start-ipython to launch IPython in the console that
started leo. You can start entering IPython commands normally, and Leo will keep
running at the same time.
</t>
<t tx="vivainio.20080223133947">
Accessing IPython from Leo
==========================

IPython code
------------

Just enter IPython commands on a Leo node and press alt-I to execute
push-to-ipython in order to execute the script in IPython. 'commands' is
interpreted loosely here - you can enter function and class definitions, in
addition to the things you would usually enter at IPython prompt - calculations,
system commands etc.

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

If you press alt+I on that node, you will see the following in Leo log window (IPython tab):

{{{
In: 1+2
&lt;2&gt; 3
In: 3+4
&lt;4&gt; 7
In: f('hello world')
&lt;6&gt; 'HELLO WORLD'
}}}

(numbers like &lt;6&gt; mean IPython output history indices; the actual object can be
referenced with _6 as usual in IPython).


Plain Python code
-----------------

If the headline of the node ends with capital P, alt-I will not run the code
through IPython translation mechanism but use the direct python 'exec' statement
(in IPython user namespace) to execute the code. It wont be shown in IPython
history, and sometimes it is safer (and more efficient) to execute things as
plain Python statements. Large class definitions are good candidates for P
nodes.
</t>
<t tx="vivainio.20080223134018">
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
[C:leo/src]|12&gt; wb.tempfile
           &lt;12&gt; &lt;ipy_leo.LeoNode object at 0x044B6D90&gt;

So here, we meet the 'LeoNode' class that is your key to manipulating Leo
content from IPython!

LeoNode
-------

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
('simplegeneric' module, will be explained later).

Besides v, you can set the body text directly through 

wb.spam.b = "some\nstring", 

headline by 

wb.spam.h = 'new_headline' 

(obviously you must access the node through wb.new_headline from that point
onwards), and access the contents as string list (IPython SList) through
'wb.spam.l'.

If you do 'wb.foo.v = 12' when node named 'foo' does not exist, the node titled
'foo' will be automatically created and assigned body 12.

LeoNode also supports go() that focuses the node in the Leo window, and ipush()
that simulates pressing alt+I on the node.

You can access unknownAttributes by .uA property dictionary. Unknown attributes
allow you to store arbitrary (pickleable) python objects in the Leo nodes; the
attributes are stored when you save the .leo document, and recreated when you
open the document again. The attributes are not visible anywhere, but can be
used for domain-specific metatada. Example:

    [C:leo/src]|12&gt; wb.spam.uA['coords'] = (12,222)
    [C:leo/src]|13&gt; wb.spam.uA
               &lt;13&gt; {'coords': (12, 222)}    

Accessing children with iteration and dict notation
---------------------------------------------------

Sometimes, you may want to treat a node as a 'database', where the nodes
children represent elements in the database. You can create a new child node for
node 'spam', with headline 'foo bar' like this:

    wb.spam['foo bar'] = "Hello"

And assign a new value for it by doing 

    wb.spam['foo bar'].v = "Hello again"

Note how you can't use .v when you first create the node - i.e. the node needs
to be initialized by simple assignment, that will be interpreted as assignment
to '.v'. This is a conscious design choice.

If you try to do wb.spam['bar'] = 'Hello', ILeo will assign '@k bar' as the
headline for the child instead, because 'bar' is a legal python name (and as
such would be incorporated in the workbook namespace). This is done to avoid
crowding the workbook namespace with extraneous items. The item will still be
accessible as wb.spam['bar']

LeoNodes are iterable, so to see the headlines of all the children of 'spam' do:

    for n in wb.spam:
        print n.h
</t>
<t tx="vivainio.20080223134100">
@cl definitions
===============

If the first line in the body text is of the form '@cl sometext', IPython will
evaluate 'sometext' and call the result with the rest of the body when you do
'wb.foo.v'. An example is in place here. Suppose that we have defined a class (I
use the term class in a non-python sense here)

{{{
def rfile(body,node):
    """ @cl rfile 

    produces a StringIO (file like obj) of the rest of the body """

    import StringIO
    return StringIO.StringIO(body)
}}}

(note that node is ignored here - but it could be used to access headline,
children etc.),

Now, let's say you have node 'spam' with text

{{{
@cl rfile
hello
world
and whatever
}}}

Now, in IPython, we can do this:

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

You should declare new @cl types to make ILeo as convenient your problem domain
as possible. For example, a "@cl etree" could return the elementtree object for
xml content.
</t>
<t tx="vivainio.20080223134118">
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
</t>
<t tx="vivainio.20080223134136">
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

?</t>
<t tx="vivainio.20080223134433">
Declaring custom push-to-ipython handlers
=========================================

Sometimes, you might want to configure what alt+I on a node does. You can do
that by creating your own push function and expose it using
ipy_leo.expose_ileo_push(f, priority). The function should check whether the
node should by handled by the function and raise IPython.ipapi.TryNext if it
will not do the handling, giving the next function in the chain a chance to see
whether it should handle the push.

This example would print an uppercase version of node body if the node headline ends
with U (yes, this is completely useless!):

{{{
def push_upcase(node):
    if not node.h.endswith('U'):
        raise TryNext
    print node.b.upper()

ipy_leo.expose_ileo_push(push_upcase, 12)
}}}

(the priority should be between 0-100 - typically, you don't need to care about
it and can usually omit the argument altogether)
</t>
<t tx="vivainio.20080223142207">
Example code snippets
=====================

Get list of all headlines of all the nodes in leo:

    [node.h for node in wb]

Create node with headline 'baz', empty body:
    wb.baz

Create 10 child nodes for baz, where i is headline and 'Hello ' + i is body:       

    for i in range(10):
        wb.baz[i] = 'Hello %d' % i


</t>
<t tx="vivainio.20080223142403"></t>
<t tx="vivainio.20080223142403.1">12</t>
<t tx="vivainio.20080316085925">array([[ 0,  1,  2],
       [ 3,  4,  5],
       [ 6,  7,  8],
       [ 9, 10, 11]])</t>
<t tx="vivainio.20080316085950"># press alt+i here to plot testarr

plot(wb.testarr.v)</t>
<t tx="vivainio.20080316092617"></t>
<t tx="vivainio.20080316144536">Quickstart:
    easy_install numpy    
    easy_install matplotlib

Make sure you have '@string ipython-argv = ipython -pylab' in @settings. We currently recommend using TkAgg as the backend (it's also the default)</t>
<t tx="vivainio.20080316145539.2">#press alt+i here to generate an array for plotter

wb.testarr.v = arange(12).reshape(4,3)</t>
</tnodes>
</leo_file>
