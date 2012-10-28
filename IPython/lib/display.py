"""Various display related classes.

Authors : MinRK, gregcaporaso
"""

from os.path import exists, isfile, splitext, abspath, join, isdir, walk


class YouTubeVideo(object):
    """Class for embedding a YouTube Video in an IPython session, based on its video id.

    e.g. to embed the video on this page:

    http://www.youtube.com/watch?v=foo

    you would do:

    vid = YouTubeVideo("foo")
    display(vid)
    """

    def __init__(self, id, width=400, height=300):
        self.id = id
        self.width = width
        self.height = height

    def _repr_html_(self):
        """return YouTube embed iframe for this video id"""
        return """
            <iframe
                width="%i"
                height="%i"
                src="http://www.youtube.com/embed/%s"
                frameborder="0"
                allowfullscreen
            ></iframe>
        """%(self.width, self.height, self.id)

class FileLink(object):
    """Class for embedding a local file link in an IPython session, based on path

    e.g. to embed a link that was generated in the IPython notebook as my/data.txt

    you would do:

    local_file = FileLink("my/data.txt")
    display(local_file)
    
    or in the HTML notebook, just
    
    FileLink("my/data.txt")
    """
    
    html_link_str = "<a href='%s' target='_blank'>%s</a>"
    
    def __init__(self,
                 path,
                 url_prefix='files/',
                 result_html_prefix='',
                 result_html_suffix='<br>'):
        """
            path : path to the file or directory that should be formatted
            directory_prefix : prefix to be prepended to all files to form a
             working link [default: 'files']
            result_html_prefix : text to append to beginning to link
             [default: none]
            result_html_suffix : text to append at the end of link
             [default: '<br>']
        """
        self.path = path
        self.url_prefix = url_prefix
        self.result_html_prefix = result_html_prefix
        self.result_html_suffix = result_html_suffix
    
    def _format_path(self):
        fp = ''.join([self.url_prefix,self.path])
        return ''.join([self.result_html_prefix,
                        self.html_link_str % (fp, self.path),
                        self.result_html_suffix])
        
    def _repr_html_(self):
        """return html link to file
        """
        if not exists(self.path):
            return ("Path (<tt>%s</tt>) doesn't exist. " 
                    "It may still be in the process of "
                    "being generated, or you may have the "
                    "incorrect path." % self.path)
        
        return self._format_path()
    
    def __repr__(self):
        """return absolute path to file
        """
        return abspath(self.path)
        
# Create an alias for formatting a single directory name as a link.
# Right now this is the same as a formatting for a single file, but 
# we'll encourage users to reference these with a different class in
# case we want to change this in the future.
DirectoryLink = FileLink

class FileLinks(FileLink):
    """Class for embedding local file links in an IPython session, based on path

    e.g. to embed links to files that were generated in the IPython notebook under my/data

    you would do:

    local_files = FileLinks("my/data")
    display(local_files)
    
    or in the HTML notebook, just
    
    FileLinks("my/data")
    
    """
    def __init__(self,
                 path,
                 url_prefix='files/',
                 included_suffixes=None,
                 result_html_prefix='',
                 result_html_suffix='<br>',
                 notebook_display_formatter=None,
                 terminal_display_formatter=None):
        """
            included_suffixes : list of filename suffixes to include when
             formatting output [default: include all files]
             
            See the FileLink (baseclass of LocalDirectory) docstring for 
             information on additional parameters.
        """
        self.included_suffixes = included_suffixes
        
        self.notebook_display_formatter = \
         self._get_notebook_display_formatter(url_prefix,
                                              result_html_prefix,
                                              result_html_suffix,
                                              included_suffixes)
        self.terminal_display_formatter = \
         self._get_terminal_display_formatter(url_prefix,
                                              result_html_prefix,
                                              result_html_suffix,
                                              included_suffixes)
        FileLink.__init__(self,
                           path,
                           url_prefix,
                           result_html_prefix,
                           result_html_suffix)
    
    def _get_notebook_display_formatter(self,
                                        url_prefix,
                                        result_html_prefix,
                                        result_html_suffix,
                                        included_suffixes):
        """ """
        def f(output_lines, dirname, fnames):
            """  """
            # begin by figuring out which filenames, if any, 
            # are going to be displayed
            display_fnames = []
            for fname in fnames:
                if (isfile(join(dirname,fname)) and
                       (included_suffixes == None or
                        splitext(fname)[1] in included_suffixes)):
                      display_fnames.append(fname)
            
            if len(display_fnames) == 0:
                pass
            else:
                output_lines.append(''.join([result_html_prefix,
                                             dirname,
                                             result_html_suffix]))
                for fname in display_fnames:
                    fp = ''.join([self.url_prefix,dirname,'/',fname])
                    output_lines.append(''.join([self.result_html_prefix,
                                                   '&nbsp;&nbsp;',
                                                   self.html_link_str % (fp,fname),
                                                   self.result_html_suffix]))
            return
        return f

    def _get_terminal_display_formatter(self,
                                        url_prefix,
                                        result_html_prefix,
                                        result_html_suffix,
                                        included_suffixes):
        """ """
        def f(output_lines, dirname, fnames):
            """  """
            # begin by figuring out which filenames, if any, 
            # are going to be displayed
            display_fnames = []
            for fname in fnames:
                if (isfile(join(dirname,fname)) and
                       (included_suffixes == None or
                        splitext(fname)[1] in included_suffixes)):
                      display_fnames.append(fname)

            if len(display_fnames) == 0:
                pass
            else:
                output_lines.append(dirname)
                for fname in display_fnames:
                    fp = abspath(join(dirname,fname))
                    output_lines.append('  %s' % fp)
            return
        return f
    
    def _format_path(self):
        result_lines = []
        walk(self.path, self.notebook_display_formatter, result_lines)
        return '\n'.join(result_lines)
    
    def __repr__(self):
        """return newline-separated absolute paths
        """
        result_lines = []
        walk(self.path, self.terminal_display_formatter, result_lines)
        return '\n'.join(result_lines)