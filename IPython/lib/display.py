"""Various display related classes.

Authors : MinRK, gregcaporaso, dannystaple
"""
import urllib

from os.path import exists, isfile, splitext, abspath, join, isdir
from os import walk


class YouTubeVideo(object):
    """Class for embedding a YouTube Video in an IPython session, based on its video id.

    e.g. to embed the video on this page:

    http://www.youtube.com/watch?v=foo

    you would do:

    vid = YouTubeVideo("foo")
    display(vid)
    
    To start from 30 seconds:
    
    vid = YouTubeVideo("abc", start=30)
    display(vid)
    
    To calculate seconds from time as hours, minutes, seconds use:
    start=int(timedelta(hours=1, minutes=46, seconds=40).total_seconds())

    Other parameters can be provided as documented at 
    https://developers.google.com/youtube/player_parameters#parameter-subheader
    """

    def __init__(self, id, width=400, height=300, **kwargs):
        self.id = id
        self.width = width
        self.height = height
        self.params = kwargs

    def _repr_html_(self):
        """return YouTube embed iframe for this video id"""
        if self.params:
            params = "?" + urllib.urlencode(self.params)
        else:
            params = ""
        return """
            <iframe
                width="%i"
                height="%i"
                src="http://www.youtube.com/embed/%s%s"
                frameborder="0"
                allowfullscreen
            ></iframe>
        """ % (self.width, self.height, self.id, params)

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
             
            notebook_display_formatter : func passed to os.path.walk when
             formatting links for display in the notebook
            
            terminal_display_formatter : func passed to os.path.walk when
             formatting links for display in the terminal
            
        """
        self.included_suffixes = included_suffixes
        # remove trailing slashs for more consistent output formatting
        path = path.rstrip('/')
        FileLink.__init__(self,
                           path,
                           url_prefix,
                           result_html_prefix,
                           result_html_suffix)
        
        self.notebook_display_formatter = \
             notebook_display_formatter or self._get_notebook_display_formatter()
        self.terminal_display_formatter = \
             terminal_display_formatter or self._get_terminal_display_formatter()
    
    def _get_display_formatter(self,
                               dirname_output_format,
                               fname_output_format,
                               fp_format):
        """ generate func to pass to os.path.walk
        
           dirname_output_format: string to use for formatting directory 
            names, dirname will be substituted for a single "%s" which
            must appear in this string
           fname_output_format: string to use for formatting file names,
            if a single "%s" appears in the string, fname will be substituted
            if two "%s" appear in the string, the path to fname will be 
             substituted for the first and fname will be substituted for the
             second
           fp_format: string to use for formatting filepaths, must contain
            exactly two "%s" and the dirname will be subsituted for the first
            and fname will be substituted for the second
        """
        
        included_suffixes = self.included_suffixes

        def f(output_lines, dirname, fnames):
            """ func to be passed to os.path.walk """
            # begin by figuring out which filenames, if any, 
            # are going to be displayed
            display_fnames = []
            for fname in fnames:
                if (isfile(join(dirname,fname)) and
                       (included_suffixes == None or
                        splitext(fname)[1] in included_suffixes)):
                      display_fnames.append(fname)
        
            if len(display_fnames) == 0:
                # if there are no filenames to display, don't print anything
                # (not even the directory name)
                pass
            else:
                # otherwise print the formatted directory name followed by 
                # the formatted filenames
                dirname_output_line = dirname_output_format % dirname
                output_lines.append(dirname_output_line)
                for fname in display_fnames:
                    fp = fp_format % (dirname,fname)
                    try:
                        # output can include both a filepath and a filename...
                        fname_output_line = fname_output_format % (fp, fname)
                    except TypeError:
                        # ... or just a single filepath
                        fname_output_line = fname_output_format % fname
                    output_lines.append(fname_output_line)
            return
        return f

    def _get_notebook_display_formatter(self,
                                        spacer="&nbsp;&nbsp;"):
        """ generate func to pass to os.path.walk for notebook formatting
        """
        dirname_output_format = \
         self.result_html_prefix + "%s/" + self.result_html_suffix
        fname_output_format = \
         self.result_html_prefix + spacer + self.html_link_str + self.result_html_suffix
        fp_format = self.url_prefix + '%s/%s'
        
        return self._get_display_formatter(dirname_output_format,
                                           fname_output_format,
                                           fp_format)

    def _get_terminal_display_formatter(self,
                                        spacer="  "):
        """ generate func to pass to os.path.walk for terminal formatting
        """
        dirname_output_format = "%s/"
        fname_output_format = spacer + "%s"
        fp_format = '%s/%s'
        
        return self._get_display_formatter(dirname_output_format,
                                           fname_output_format,
                                           fp_format)
    
    def _format_path(self):
        result_lines = []
        walked_dir = list(walk(self.path))
        walked_dir.sort()
        for dirname, subdirs, fnames in walked_dir:
            self.notebook_display_formatter(result_lines,dirname, fnames)
        return '\n'.join(result_lines)
    
    def __repr__(self):
        """return newline-separated absolute paths
        """
        result_lines = []
        walked_dir = list(walk(self.path))
        walked_dir.sort()
        for dirname, subdirs, fnames in walked_dir:
            self.terminal_display_formatter(result_lines, dirname, fnames)
        return '\n'.join(result_lines)
